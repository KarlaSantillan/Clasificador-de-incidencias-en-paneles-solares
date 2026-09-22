import warnings
from io import BytesIO
from pathlib import Path

from django import forms
from PIL import Image, UnidentifiedImageError


MAX_UPLOAD_SIZE = 10 * 1024 * 1024
MAX_IMAGE_WIDTH = 10_000
MAX_IMAGE_HEIGHT = 10_000
MAX_IMAGE_PIXELS = 40_000_000

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}
FORMAT_EXTENSIONS = {
    'JPEG': {'.jpg', '.jpeg'},
    'PNG': {'.png'},
    'WEBP': {'.webp'},
}


class LimitedImageField(forms.ImageField):
    """Rechaza tamaño y vacío antes de pedir a Pillow que decodifique el archivo."""

    def to_python(self, data):
        if data is not None:
            size = getattr(data, 'size', None)
            if size == 0:
                raise forms.ValidationError('El archivo está vacío.')
            if size is not None and size > MAX_UPLOAD_SIZE:
                raise forms.ValidationError(
                    'La imagen supera el tamaño máximo permitido de 10 MB.'
                )
        return super().to_python(data)


class ImageUploadForm(forms.Form):
    image = LimitedImageField(
        label='Imagen del panel solar',
        required=True,
        error_messages={
            'required': 'Selecciona una imagen para analizar.',
            'invalid_image': (
                'El archivo no es una imagen válida o está dañado. '
                'Utiliza JPG, JPEG, PNG o WEBP.'
            ),
            'empty': 'El archivo está vacío.',
        },
        widget=forms.ClearableFileInput(
            attrs={
                'accept': '.jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp',
                'class': 'file-input-native',
            }
        ),
    )

    def clean_image(self):
        uploaded = self.cleaned_data['image']

        if not uploaded.size:
            raise forms.ValidationError('El archivo está vacío.')
        if uploaded.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError(
                'La imagen supera el tamaño máximo permitido de 10 MB.'
            )

        extension = Path(uploaded.name or '').suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                'Formato no permitido. Utiliza archivos JPG, JPEG, PNG o WEBP.'
            )

        try:
            uploaded.seek(0)
            content = uploaded.read()
            uploaded.seek(0)
            if not content:
                raise forms.ValidationError('El archivo está vacío.')

            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(BytesIO(content)) as image:
                    detected_format = (image.format or '').upper()
                    image.verify()

                with Image.open(BytesIO(content)) as image:
                    width, height = image.size
                    image.load()
        except forms.ValidationError:
            raise
        except (
            UnidentifiedImageError,
            OSError,
            SyntaxError,
            ValueError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as exc:
            raise forms.ValidationError(
                'El archivo no es una imagen válida o está dañado.'
            ) from exc

        if detected_format not in ALLOWED_FORMATS:
            raise forms.ValidationError(
                'El contenido de la imagen no corresponde a JPG, JPEG, PNG o WEBP.'
            )
        if extension not in FORMAT_EXTENSIONS[detected_format]:
            raise forms.ValidationError(
                'La extensión del archivo no coincide con el formato real de la imagen.'
            )
        if width < 1 or height < 1:
            raise forms.ValidationError('La imagen no tiene dimensiones válidas.')
        if (
            width > MAX_IMAGE_WIDTH
            or height > MAX_IMAGE_HEIGHT
            or width * height > MAX_IMAGE_PIXELS
        ):
            raise forms.ValidationError(
                'Las dimensiones de la imagen son demasiado grandes. '
                'Utiliza una imagen de hasta 10 000 píxeles por lado y 40 megapíxeles.'
            )

        uploaded.seek(0)
        return uploaded
