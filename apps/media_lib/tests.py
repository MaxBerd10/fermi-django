"""
Proves the dimension-guessing bug from the old site can't happen here: width/height
are read from the actual decoded image by Pillow, never trusted from user input.
"""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

from apps.media_lib.models import Image


def make_uploaded_png(width: int, height: int, name: str = "test.png") -> SimpleUploadedFile:
    buf = io.BytesIO()
    PILImage.new("RGB", (width, height), color="red").save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")


@pytest.mark.django_db
def test_real_dimensions_are_computed_from_the_actual_image_not_trusted_input():
    upload = make_uploaded_png(width=1600, height=900)
    image = Image.objects.create(file=upload, alt_text="test")
    image.refresh_from_db()

    assert image.width == 1600
    assert image.height == 900
