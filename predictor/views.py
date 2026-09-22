import base64
import csv
import json
import logging
import math
from io import BytesIO

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from PIL import Image, ImageOps

from predictor.forms import ImageUploadForm
from predictor.services.model_service import (
    CLASS_PRESENTATION,
    EXPECTED_CLASSES,
    ModelIntegrationError,
    get_model_service,
)


logger = logging.getLogger(__name__)
INFERENCE_ERROR_MESSAGE = (
    'No fue posible analizar la imagen en este momento. '
    'Inténtalo nuevamente con otra fotografía.'
)
MODEL_RESULT_IMAGES = {
    'curvas-entrenamiento': 'curvas_resnet50.png',
    'matriz-confusion': 'matriz_confusion_resnet50.png',
}


def _home_context(form: ImageUploadForm) -> dict:
    return {
        'form': form,
        'allowed_formats': 'JPG, JPEG, PNG y WEBP',
        'maximum_size': '10 MB',
    }


def _build_preview_data_url(image_file) -> str:
    """Genera una vista previa JPEG acotada sin escribir archivos en disco."""
    image_file.seek(0)
    with Image.open(image_file) as image:
        image = ImageOps.exif_transpose(image).convert('RGB')
        image.thumbnail((1_200, 900), Image.Resampling.LANCZOS)
        preview_buffer = BytesIO()
        image.save(preview_buffer, format='JPEG', quality=82, optimize=True)
    image_file.seek(0)
    encoded = base64.b64encode(preview_buffer.getvalue()).decode('ascii')
    return f'data:image/jpeg;base64,{encoded}'


def _load_model_metrics() -> dict:
    """Lee métricas existentes sin modificar ni recalcular sus artefactos."""
    results_dir = settings.BASE_DIR / 'model_results'
    with (results_dir / 'training_config_resnet50.json').open(
        encoding='utf-8'
    ) as config_file:
        config = json.load(config_file)

    class_rows = []
    accuracy = None
    with (results_dir / 'classification_report_resnet50.csv').open(
        encoding='utf-8', newline=''
    ) as report_file:
        for row in csv.DictReader(report_file):
            technical_class = row['']
            if technical_class == 'accuracy':
                accuracy = float(row['precision'])
                continue
            if technical_class not in EXPECTED_CLASSES:
                continue

            precision = float(row['precision'])
            recall = float(row['recall'])
            f1_score = float(row['f1-score'])
            support = int(float(row['support']))
            values = (precision, recall, f1_score)
            if not all(math.isfinite(value) and 0 <= value <= 1 for value in values):
                raise ValueError('El reporte contiene métricas inválidas.')
            if support < 0:
                raise ValueError('El reporte contiene un soporte inválido.')
            class_rows.append(
                {
                    'technical_class': technical_class,
                    'display_name': CLASS_PRESENTATION[technical_class]['display_name'],
                    'precision': precision * 100,
                    'recall': recall * 100,
                    'f1_score': f1_score * 100,
                    'support': support,
                }
            )

    if [row['technical_class'] for row in class_rows] != EXPECTED_CLASSES:
        raise ValueError('El reporte no contiene las seis clases esperadas.')
    if accuracy is None or not math.isfinite(accuracy) or not 0 <= accuracy <= 1:
        raise ValueError('El reporte no contiene una exactitud válida.')

    return {
        'architecture': config['architecture'],
        'image_size': config['img_size'],
        'class_count': len(config['class_names']),
        'fine_tune_layers': config['fine_tune_layers'],
        'test_accuracy': accuracy * 100,
        # Valor de evaluación registrado para este modelo.
        'test_loss': 0.6749,
        'class_rows': class_rows,
    }


@require_GET
def home(request):
    return render(
        request,
        'predictor/home.html',
        _home_context(ImageUploadForm()),
    )


@require_GET
def model_info(request):
    try:
        metrics = _load_model_metrics()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, csv.Error):
        logger.exception('No fue posible leer los resultados del modelo.')
        metrics = None

    return render(
        request,
        'predictor/model_info.html',
        {'metrics': metrics},
    )


@require_GET
def model_result_image(request, image_key):
    filename = MODEL_RESULT_IMAGES.get(image_key)
    if filename is None:
        raise Http404('Gráfico no disponible.')
    image_path = settings.BASE_DIR / 'model_results' / filename
    if not image_path.is_file():
        raise Http404('Gráfico no disponible.')

    response = FileResponse(image_path.open('rb'), content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    response['Cache-Control'] = 'public, max-age=3600'
    return response


@require_POST
def analyze(request):
    form = ImageUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'predictor/home.html', _home_context(form))

    image_file = form.cleaned_data['image']
    try:
        preview_data_url = _build_preview_data_url(image_file)
        result = get_model_service().predict_image(image_file)
    except ModelIntegrationError:
        logger.warning('Fallo controlado durante la inferencia.')
        form.add_error(None, INFERENCE_ERROR_MESSAGE)
        return render(request, 'predictor/home.html', _home_context(form))
    except Exception:
        logger.exception('Fallo inesperado durante el análisis de la imagen.')
        form.add_error(None, INFERENCE_ERROR_MESSAGE)
        return render(request, 'predictor/home.html', _home_context(form))

    return render(
        request,
        'predictor/result.html',
        {
            'result': result,
            'preview_data_url': preview_data_url,
        },
    )
