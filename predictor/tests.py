from io import BytesIO
from unittest import skipUnless
from unittest.mock import Mock, patch

import numpy as np
from django.contrib.staticfiles import finders
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.test import SimpleTestCase
from django.urls import reverse
from PIL import Image, features

from predictor.forms import MAX_UPLOAD_SIZE, ImageUploadForm
from predictor.services.model_service import (
    EXPECTED_CLASSES,
    ModelIntegrationError,
    ModelService,
)


def make_image_bytes(
    image_format='PNG', mode='RGB', size=(32, 24), color=None
):
    if color is None:
        color = {'RGB': (80, 140, 200), 'RGBA': (80, 140, 200, 180), 'L': 120}[mode]
    buffer = BytesIO()
    Image.new(mode, size, color=color).save(buffer, format=image_format)
    return buffer.getvalue()


def make_upload(name='panel.png', image_format='PNG', mode='RGB', size=(32, 24)):
    content_types = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}
    return SimpleUploadedFile(
        name,
        make_image_bytes(image_format=image_format, mode=mode, size=size),
        content_type=content_types[image_format],
    )


def make_result(probabilities=None):
    if probabilities is None:
        probabilities = np.array([0.80, 0.04, 0.04, 0.04, 0.04, 0.04])
    return ModelService.build_prediction_result(probabilities)


class ImageUploadFormTests(SimpleTestCase):
    def test_file_is_required(self):
        form = ImageUploadForm(data={}, files={})

        self.assertFalse(form.is_valid())
        self.assertIn('Selecciona una imagen', form.errors['image'][0])

    def test_valid_jpg(self):
        form = ImageUploadForm(
            files={'image': make_upload('panel.jpg', 'JPEG')}
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_png(self):
        form = ImageUploadForm(files={'image': make_upload()})

        self.assertTrue(form.is_valid(), form.errors)

    @skipUnless(features.check('webp'), 'Pillow no tiene soporte WEBP')
    def test_valid_webp(self):
        form = ImageUploadForm(
            files={'image': make_upload('panel.webp', 'WEBP')}
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_file(self):
        upload = SimpleUploadedFile('panel.jpg', b'', content_type='image/jpeg')
        form = ImageUploadForm(files={'image': upload})

        self.assertFalse(form.is_valid())
        self.assertIn('vacío', form.errors['image'][0])

    def test_text_file_with_jpg_extension(self):
        upload = SimpleUploadedFile(
            'panel.jpg', b'este archivo no es una imagen', content_type='image/jpeg'
        )
        form = ImageUploadForm(files={'image': upload})

        self.assertFalse(form.is_valid())
        self.assertIn('no es una imagen válida', form.errors['image'][0])

    def test_damaged_jpg_is_rejected(self):
        valid_jpg = make_image_bytes(image_format='JPEG')
        damaged = SimpleUploadedFile(
            'panel.jpg',
            valid_jpg[: len(valid_jpg) // 2],
            content_type='image/jpeg',
        )
        form = ImageUploadForm(files={'image': damaged})

        self.assertFalse(form.is_valid())
        self.assertIn('no es una imagen válida', form.errors['image'][0])

    def test_file_larger_than_ten_mb(self):
        content = make_image_bytes(image_format='JPEG')
        upload = InMemoryUploadedFile(
            BytesIO(content),
            field_name='image',
            name='panel.jpg',
            content_type='image/jpeg',
            size=MAX_UPLOAD_SIZE + 1,
            charset=None,
        )
        form = ImageUploadForm(files={'image': upload})

        self.assertFalse(form.is_valid())
        self.assertIn('10 MB', form.errors['image'][0])

    def test_grayscale_image(self):
        form = ImageUploadForm(
            files={'image': make_upload('panel.png', 'PNG', mode='L')}
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_rgba_image(self):
        form = ImageUploadForm(
            files={'image': make_upload('panel.png', 'PNG', mode='RGBA')}
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_excessive_dimensions(self):
        form = ImageUploadForm(
            files={'image': make_upload(size=(10_001, 1))}
        )

        self.assertFalse(form.is_valid())
        self.assertIn('dimensiones', form.errors['image'][0])


class ImagePreparationTests(SimpleTestCase):
    def test_prepare_image_keeps_float32_values_in_zero_to_255_range(self):
        image_file = BytesIO(
            make_image_bytes(image_format='PNG', color=(255, 128, 0))
        )

        batch = ModelService.prepare_image(image_file)

        self.assertEqual(batch.shape, (1, 224, 224, 3))
        self.assertEqual(batch.dtype, np.float32)
        np.testing.assert_allclose(batch[0, 0, 0], [255.0, 128.0, 0.0])

    def test_prepare_grayscale_converts_to_rgb(self):
        batch = ModelService.prepare_image(
            BytesIO(make_image_bytes(mode='L', color=90))
        )

        np.testing.assert_allclose(batch[0, 0, 0], [90.0, 90.0, 90.0])


class PredictionResultTests(SimpleTestCase):
    def test_indices_map_to_exact_classes(self):
        for expected_index, expected_class in enumerate(EXPECTED_CLASSES):
            probabilities = np.full(6, 0.05)
            probabilities[expected_index] = 0.75

            result = ModelService.build_prediction_result(probabilities)

            self.assertEqual(result['technical_class'], expected_class)

    def test_probabilities_are_sorted_descending(self):
        probabilities = np.array([0.05, 0.10, 0.30, 0.15, 0.35, 0.05])

        result = ModelService.build_prediction_result(probabilities)
        ordered = [item['probability'] for item in result['probabilities']]

        self.assertEqual(ordered, sorted(ordered, reverse=True))
        self.assertEqual(len(ordered), 6)

    def test_high_confidence(self):
        result = make_result(np.array([0.75, 0.05, 0.05, 0.05, 0.05, 0.05]))

        self.assertEqual(result['confidence_level'], 'Confianza alta')

    def test_moderate_confidence(self):
        result = make_result(np.array([0.60, 0.08, 0.08, 0.08, 0.08, 0.08]))

        self.assertEqual(result['confidence_level'], 'Confianza moderada')

    def test_low_confidence(self):
        result = make_result(np.array([0.59, 0.082, 0.082, 0.082, 0.082, 0.082]))

        self.assertEqual(result['confidence_level'], 'Confianza baja')
        self.assertTrue(result['is_low_confidence'])

    def test_negative_probability_is_rejected(self):
        with self.assertRaises(ModelIntegrationError):
            ModelService.build_prediction_result(
                np.array([-0.10, 0.30, 0.20, 0.20, 0.20, 0.20])
            )

    def test_non_finite_probability_is_rejected(self):
        with self.assertRaises(ModelIntegrationError):
            ModelService.build_prediction_result(
                np.array([np.nan, 0.20, 0.20, 0.20, 0.20, 0.20])
            )

    def test_probability_sum_is_validated(self):
        with self.assertRaises(ModelIntegrationError):
            ModelService.build_prediction_result(np.full(6, 0.10))

    def test_bar_percentages_are_limited_and_winner_is_unique(self):
        result = make_result()

        self.assertTrue(
            all(0 <= item['bar_percentage'] <= 100 for item in result['probabilities'])
        )
        self.assertEqual(
            sum(item['is_winner'] for item in result['probabilities']),
            1,
        )


class PredictionViewsTests(SimpleTestCase):
    def test_home_get_responds(self):
        response = self.client.get(reverse('predictor:home'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictor/home.html')
        self.assertContains(response, 'Analiza la condición visible')
        self.assertContains(response, '<title>Inspector solar | Analizar panel</title>')
        self.assertContains(response, 'predictor/icons/solar-mark.svg')
        self.assertContains(response, 'predictor/icons/favicon-32x32.png')
        self.assertContains(response, 'predictor/icons/apple-touch-icon.png')

    def test_home_contains_navigation_and_upload_controls(self):
        response = self.client.get(reverse('predictor:home'))

        self.assertContains(response, reverse('predictor:model_info'))
        self.assertContains(response, 'id="drop-zone"')
        self.assertContains(response, 'id="remove-file"')
        self.assertContains(response, 'id="submit-button"')
        self.assertContains(response, 'class="file-input-native"')
        self.assertNotContains(response, 'Ningún archivo seleccionado')

    def test_model_page_uses_real_report_metrics(self):
        response = self.client.get(reverse('predictor:model_info'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictor/model_info.html')
        self.assertContains(response, 'PV Panel Defect Dataset')
        self.assertContains(response, '77,54%')
        self.assertContains(response, 'Excremento de aves')
        self.assertContains(response, 'Electrical-damage')
        self.assertContains(response, reverse('predictor:home'))
        self.assertContains(response, '<title>Modelo ResNet50 | Inspector solar</title>')

    def test_only_allowed_model_result_images_are_served(self):
        response = self.client.get(
            reverse(
                'predictor:model_result_image',
                args=['curvas-entrenamiento'],
            )
        )
        missing = self.client.get(
            reverse('predictor:model_result_image', args=['archivo-no-permitido'])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(missing.status_code, 404)

    def test_valid_post_renders_result(self):
        service = Mock()
        service.predict_image.return_value = make_result()

        with patch('predictor.views.get_model_service', return_value=service):
            response = self.client.post(
                reverse('predictor:analyze'),
                {'image': make_upload()},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictor/result.html')
        self.assertContains(response, 'Excremento de aves')
        self.assertContains(response, '80,00%')
        self.assertContains(response, 'data:image/jpeg;base64,')
        self.assertContains(response, 'class="probability-row is-winner"', count=1)
        self.assertContains(response, 'Alcance del resultado')
        self.assertContains(response, 'data-probability=', count=6)
        self.assertContains(
            response,
            '<title>Excremento de aves | Inspector solar</title>',
        )
        service.predict_image.assert_called_once()

    def test_low_confidence_result_displays_warning(self):
        service = Mock()
        service.predict_image.return_value = make_result(
            np.array([0.59, 0.082, 0.082, 0.082, 0.082, 0.082])
        )

        with patch('predictor.views.get_model_service', return_value=service):
            response = self.client.post(
                reverse('predictor:analyze'),
                {'image': make_upload()},
            )

        self.assertContains(response, 'low-confidence-note')
        self.assertContains(response, 'presenta baja confianza')

    def test_post_without_file_returns_form_error(self):
        response = self.client.post(reverse('predictor:analyze'), {})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictor/home.html')
        self.assertContains(response, 'Selecciona una imagen')

    def test_invalid_post_returns_form_error(self):
        invalid = SimpleUploadedFile(
            'panel.jpg', b'contenido falso', content_type='image/jpeg'
        )

        response = self.client.post(
            reverse('predictor:analyze'), {'image': invalid}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictor/home.html')
        self.assertContains(response, 'no es una imagen válida')

    def test_controlled_model_exception_is_friendly(self):
        service = Mock()
        service.predict_image.side_effect = ModelIntegrationError(
            'detalle interno que no debe mostrarse'
        )

        with patch('predictor.views.get_model_service', return_value=service):
            response = self.client.post(
                reverse('predictor:analyze'),
                {'image': make_upload()},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictor/home.html')
        self.assertContains(response, 'No fue posible analizar la imagen')
        self.assertNotContains(response, 'detalle interno')


class StaticAssetsTests(SimpleTestCase):
    def test_main_visual_assets_exist(self):
        assets = [
            'predictor/css/styles.css',
            'predictor/js/upload.js',
            'predictor/icons/solar-mark.svg',
            'predictor/icons/favicon-32x32.png',
            'predictor/icons/apple-touch-icon.png',
        ]

        for asset in assets:
            with self.subTest(asset=asset):
                self.assertIsNotNone(finders.find(asset))
