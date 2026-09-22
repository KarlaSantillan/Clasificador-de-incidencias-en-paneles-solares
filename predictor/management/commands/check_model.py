import numpy as np
from django.core.management.base import BaseCommand, CommandError

from predictor.services.model_service import (
    EXPECTED_OUTPUT_COUNT,
    ModelIntegrationError,
    get_model_service,
)


class Command(BaseCommand):
    help = 'Comprueba la carga y la salida técnica del modelo Keras configurado.'

    def handle(self, *args, **options):
        service = get_model_service()

        if not service.model_path.is_file():
            raise CommandError(f'No existe el modelo: {service.model_path}')
        self.stdout.write(f'Modelo encontrado: {service.model_path}')

        if not service.class_names_path.is_file():
            raise CommandError(
                f'No existe class_names.json: {service.class_names_path}'
            )
        self.stdout.write(f'Clases encontradas: {service.class_names_path}')

        try:
            self.stdout.write('Cargando el modelo con compile=False...')
            self.stdout.write(f'Forma de entrada: {service.input_shape}')
            self.stdout.write(f'Forma de salida: {service.output_shape}')

            synthetic_batch = np.full(
                (1, 224, 224, 3), 127.5, dtype=np.float32
            )
            probabilities = service.predict_batch(synthetic_batch)
        except ModelIntegrationError as exc:
            raise CommandError(str(exc)) from exc

        if probabilities.shape != (EXPECTED_OUTPUT_COUNT,):
            raise CommandError(
                f'Se esperaban exactamente 6 probabilidades y se obtuvo '
                f'{probabilities.shape}.'
            )
        if not np.all(np.isfinite(probabilities)):
            raise CommandError('La predicción contiene valores no finitos.')

        probability_sum = float(np.sum(probabilities))
        if not np.isclose(probability_sum, 1.0, rtol=1e-5, atol=1e-5):
            raise CommandError(
                f'Las probabilidades suman {probability_sum:.8f}, no aproximadamente 1.'
            )

        self.stdout.write('Predicción sintética (no representa una clasificación real):')
        for class_name, probability in zip(service.class_names, probabilities):
            self.stdout.write(f'  {class_name}: {float(probability):.8f}')
        self.stdout.write(f'Suma de probabilidades: {probability_sum:.8f}')
        self.stdout.write(
            self.style.SUCCESS('Integración del modelo verificada correctamente.')
        )
