import json
import threading
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO

import numpy as np
import tensorflow as tf
from django.conf import settings
from PIL import Image, ImageOps


EXPECTED_CLASSES = [
    'Bird-drop',
    'Clean',
    'Dusty',
    'Electrical-damage',
    'Physical-Damage',
    'Snow-Covered',
]
EXPECTED_INPUT_SHAPE = (None, 224, 224, 3)
EXPECTED_OUTPUT_COUNT = len(EXPECTED_CLASSES)

CLASS_PRESENTATION = {
    'Bird-drop': {
        'display_name': 'Excremento de aves',
        'description': (
            'Se observan patrones similares a residuos o excrementos de aves '
            'sobre la superficie.'
        ),
        'recommendation': (
            'Revisar y limpiar cuidadosamente la superficie siguiendo las '
            'indicaciones de mantenimiento del fabricante.'
        ),
    },
    'Clean': {
        'display_name': 'Panel limpio',
        'description': (
            'La superficie presenta características visuales similares a un '
            'panel limpio.'
        ),
        'recommendation': (
            'Mantener las inspecciones y limpiezas preventivas programadas.'
        ),
    },
    'Dusty': {
        'display_name': 'Panel cubierto de polvo',
        'description': (
            'Se observan características compatibles con acumulación de polvo.'
        ),
        'recommendation': (
            'Realizar una inspección y limpieza adecuada para evitar pérdida '
            'de eficiencia.'
        ),
    },
    'Electrical-damage': {
        'display_name': 'Daño eléctrico visible',
        'description': (
            'La imagen presenta patrones visuales relacionados con posibles '
            'daños eléctricos visibles.'
        ),
        'recommendation': (
            'Evitar manipular el panel sin protección y solicitar una inspección '
            'de personal técnico capacitado.'
        ),
    },
    'Physical-Damage': {
        'display_name': 'Daño físico',
        'description': (
            'Se identifican características visuales compatibles con daño físico '
            'en el panel.'
        ),
        'recommendation': (
            'Suspender cualquier manipulación riesgosa y solicitar una revisión '
            'técnica del estado del panel.'
        ),
    },
    'Snow-Covered': {
        'display_name': 'Panel cubierto de nieve',
        'description': (
            'La superficie presenta patrones visuales similares a una cobertura '
            'de nieve.'
        ),
        'recommendation': (
            'Verificar las condiciones del entorno y aplicar procedimientos '
            'seguros de retiro establecidos para la instalación.'
        ),
    },
}

ACADEMIC_NOTICE = (
    'Este resultado es generado por un modelo académico de clasificación de '
    'imágenes y no sustituye una inspección técnica profesional.'
)
LOW_CONFIDENCE_MESSAGE = (
    'El modelo encontró similitudes con esta categoría, pero el resultado '
    'presenta baja confianza. Se recomienda utilizar otra fotografía con mejor '
    'iluminación, enfoque y visibilidad del panel.'
)

RESULT_TONES = {
    'Bird-drop': 'amber',
    'Clean': 'green',
    'Dusty': 'amber',
    'Electrical-damage': 'orange',
    'Physical-Damage': 'red',
    'Snow-Covered': 'blue-gray',
}


class ModelIntegrationError(RuntimeError):
    """Indica un fallo controlado al validar o ejecutar el modelo."""


class ModelService:
    """Carga y ejecuta ResNet50 sin duplicar su preprocesamiento interno."""

    model_relative_path = Path('ml_models') / 'best_resnet50_paneles_6clases.keras'
    classes_relative_path = Path('ml_models') / 'class_names.json'

    def __init__(self) -> None:
        self._model = None
        self._class_names = None
        self._load_lock = threading.Lock()

    @property
    def model_path(self) -> Path:
        return Path(settings.BASE_DIR) / self.model_relative_path

    @property
    def class_names_path(self) -> Path:
        return Path(settings.BASE_DIR) / self.classes_relative_path

    @property
    def model(self):
        self._ensure_loaded()
        return self._model

    @property
    def class_names(self) -> list[str]:
        self._ensure_loaded()
        return list(self._class_names)

    @property
    def input_shape(self) -> tuple:
        return tuple(self.model.input_shape)

    @property
    def output_shape(self) -> tuple:
        return tuple(self.model.output_shape)

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return

        with self._load_lock:
            if self._model is not None:
                return
            class_names = self._load_class_names()
            model = self._load_model()
            self._validate_model_shapes(model)
            self._class_names = class_names
            self._model = model

    def _load_class_names(self) -> list[str]:
        path = self.class_names_path
        if not path.is_file():
            raise ModelIntegrationError(
                f'No se encontró el archivo de clases requerido: {path}'
            )

        try:
            with path.open(encoding='utf-8') as class_file:
                class_names = json.load(class_file)
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelIntegrationError(
                f'No se pudo leer un JSON válido de clases en {path}: {exc}'
            ) from exc

        if class_names != EXPECTED_CLASSES:
            raise ModelIntegrationError(
                'Las clases no coinciden exactamente con el orden esperado. '
                f'Esperado: {EXPECTED_CLASSES}. Encontrado: {class_names!r}.'
            )
        return class_names

    def _load_model(self):
        path = self.model_path
        if not path.is_file():
            raise ModelIntegrationError(f'No se encontró el modelo requerido: {path}')

        try:
            return tf.keras.models.load_model(path, compile=False)
        except Exception as exc:
            raise ModelIntegrationError(
                f'No se pudo cargar el modelo Keras desde {path}: {exc}'
            ) from exc

    @staticmethod
    def _validate_model_shapes(model) -> None:
        if isinstance(model.input_shape, list):
            raise ModelIntegrationError('El modelo debe tener una sola entrada.')
        input_shape = tuple(model.input_shape)
        if input_shape != EXPECTED_INPUT_SHAPE:
            raise ModelIntegrationError(
                f'Forma de entrada inválida: {input_shape}. '
                f'Se esperaba {EXPECTED_INPUT_SHAPE}.'
            )

        if isinstance(model.output_shape, list):
            raise ModelIntegrationError('El modelo debe tener una sola salida.')
        output_shape = tuple(model.output_shape)
        if len(output_shape) != 2 or output_shape[-1] != EXPECTED_OUTPUT_COUNT:
            raise ModelIntegrationError(
                f'Forma de salida inválida: {output_shape}. '
                f'La salida debe contener {EXPECTED_OUTPUT_COUNT} probabilidades.'
            )

    @staticmethod
    def prepare_image(image_source: str | Path | BinaryIO) -> np.ndarray:
        """Devuelve RGB float32 224x224 en rango 0-255.

        No normaliza, no cambia a BGR y no usa preprocess_input porque esas
        operaciones ya forman parte del modelo guardado.
        """
        try:
            if hasattr(image_source, 'seek'):
                image_source.seek(0)
            with Image.open(image_source) as image:
                image = ImageOps.exif_transpose(image).convert('RGB')
                image_array = np.asarray(image, dtype=np.float32)
        except (OSError, SyntaxError, ValueError) as exc:
            raise ModelIntegrationError('No se pudo preparar la imagen.') from exc
        finally:
            if hasattr(image_source, 'seek'):
                image_source.seek(0)

        try:
            resized = tf.image.resize(image_array, (224, 224)).numpy()
            batch = np.expand_dims(
                resized.astype(np.float32, copy=False), axis=0
            )
        except Exception as exc:
            raise ModelIntegrationError('No se pudo redimensionar la imagen.') from exc

        if batch.shape != (1, 224, 224, 3):
            raise ModelIntegrationError(
                f'La imagen preparada tiene forma {batch.shape}; '
                'se esperaba (1, 224, 224, 3).'
            )
        if not np.all(np.isfinite(batch)) or np.min(batch) < 0 or np.max(batch) > 255:
            raise ModelIntegrationError(
                'La imagen preparada contiene valores de píxeles inválidos.'
            )
        return batch

    @staticmethod
    def _validate_probabilities(probabilities: np.ndarray) -> np.ndarray:
        probabilities = np.asarray(probabilities)
        if probabilities.shape != (EXPECTED_OUTPUT_COUNT,):
            raise ModelIntegrationError(
                f'Se esperaban exactamente 6 probabilidades y se obtuvo '
                f'{probabilities.shape}.'
            )
        if not np.all(np.isfinite(probabilities)):
            raise ModelIntegrationError('La predicción contiene valores no finitos.')
        if np.any(probabilities < 0):
            raise ModelIntegrationError('La predicción contiene probabilidades negativas.')

        probability_sum = float(np.sum(probabilities))
        if not np.isclose(probability_sum, 1.0, rtol=1e-5, atol=1e-5):
            raise ModelIntegrationError(
                f'Las probabilidades suman {probability_sum:.8f}, no aproximadamente 1.'
            )
        return probabilities

    def predict_batch(self, batch: np.ndarray) -> np.ndarray:
        batch = np.asarray(batch, dtype=np.float32)
        if batch.shape != (1, 224, 224, 3):
            raise ModelIntegrationError(
                f'Lote inválido: {batch.shape}. Se esperaba (1, 224, 224, 3).'
            )
        if not np.all(np.isfinite(batch)):
            raise ModelIntegrationError('La entrada contiene valores no finitos.')
        if np.min(batch) < 0 or np.max(batch) > 255:
            raise ModelIntegrationError('Los píxeles deben estar en el rango 0-255.')

        try:
            predictions = np.asarray(self.model.predict(batch, verbose=0))
        except ModelIntegrationError:
            raise
        except Exception as exc:
            raise ModelIntegrationError('No se pudo ejecutar la predicción.') from exc

        if predictions.shape != (1, EXPECTED_OUTPUT_COUNT):
            raise ModelIntegrationError(
                f'La predicción produjo {predictions.shape}; se esperaba (1, 6).'
            )
        return self._validate_probabilities(predictions[0])

    @classmethod
    def build_prediction_result(cls, probabilities: np.ndarray) -> dict:
        """Construye el resultado sin redondear valores antes de los cálculos."""
        probabilities = cls._validate_probabilities(probabilities)
        top_index = int(np.argmax(probabilities))
        technical_class = EXPECTED_CLASSES[top_index]
        confidence = float(probabilities[top_index])

        # Regla visual de presentación; no es una calibración científica.
        if confidence >= 0.75:
            confidence_level = 'Confianza alta'
            confidence_key = 'high'
        elif confidence >= 0.60:
            confidence_level = 'Confianza moderada'
            confidence_key = 'moderate'
        else:
            confidence_level = 'Confianza baja'
            confidence_key = 'low'

        ordered_probabilities = []
        for index in np.argsort(probabilities)[::-1]:
            class_name = EXPECTED_CLASSES[int(index)]
            probability = float(probabilities[int(index)])
            percentage = probability * 100.0
            ordered_probabilities.append(
                {
                    'technical_class': class_name,
                    'display_name': CLASS_PRESENTATION[class_name]['display_name'],
                    'probability': probability,
                    'percentage': percentage,
                    # Valor limitado para atributos de presentación en HTML.
                    'bar_percentage': min(max(percentage, 0.0), 100.0),
                    'is_winner': class_name == technical_class,
                }
            )

        presentation = CLASS_PRESENTATION[technical_class]
        return {
            'technical_class': technical_class,
            'display_name': presentation['display_name'],
            'confidence': confidence,
            'confidence_percentage': confidence * 100.0,
            'confidence_level': confidence_level,
            'confidence_key': confidence_key,
            'result_tone': RESULT_TONES[technical_class],
            'is_low_confidence': confidence < 0.60,
            'description': presentation['description'],
            'recommendation': presentation['recommendation'],
            'probabilities': ordered_probabilities,
            'academic_notice': ACADEMIC_NOTICE,
            'low_confidence_message': LOW_CONFIDENCE_MESSAGE,
        }

    def predict_image(self, image_source: str | Path | BinaryIO) -> dict:
        batch = self.prepare_image(image_source)
        probabilities = self.predict_batch(batch)
        return self.build_prediction_result(probabilities)


@lru_cache(maxsize=1)
def get_model_service() -> ModelService:
    """Devuelve la única instancia del servicio usada por el proceso Django."""
    return ModelService()
