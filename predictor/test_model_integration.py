import os
from unittest import skipUnless

import numpy as np
from django.test import SimpleTestCase

from predictor.services.model_service import get_model_service


@skipUnless(
    os.getenv('RUN_MODEL_INTEGRATION_TESTS') == '1',
    'Activa RUN_MODEL_INTEGRATION_TESTS=1 para cargar el modelo real.',
)
class RealModelIntegrationTests(SimpleTestCase):
    def test_real_model_returns_six_valid_probabilities(self):
        batch = np.full((1, 224, 224, 3), 127.5, dtype=np.float32)

        probabilities = get_model_service().predict_batch(batch)

        self.assertEqual(probabilities.shape, (6,))
        self.assertTrue(np.all(np.isfinite(probabilities)))
        self.assertTrue(np.all(probabilities >= 0))
        self.assertTrue(np.isclose(np.sum(probabilities), 1.0, atol=1e-5))
