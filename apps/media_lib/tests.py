"""
Proves the dimension-guessing bug from the old site can't happen here: width/height
are read from the actual decoded image by Pillow, never trusted from user input.
"""

import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

from apps.media_lib.models import Document, Image, Video


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


@pytest.mark.django_db
def test_video_requires_a_poster_image():
    # A poster is a required FK, not an optional field — this is what makes the
    # old site's "black until you press play" bug structurally impossible here
    # instead of papered over with a preload+seek workaround.
    poster = Image.objects.create(file=make_uploaded_png(320, 180), alt_text="poster")
    video_file = SimpleUploadedFile("clip.mp4", b"not-real-video-bytes", content_type="video/mp4")

    video = Video.objects.create(file=video_file, poster=poster)

    assert video.poster_id == poster.id


@pytest.mark.django_db
def test_document_file_size_is_computed_from_the_actual_upload():
    upload = SimpleUploadedFile("order-42.pdf", b"%PDF-1.4 fake pdf bytes", content_type="application/pdf")

    document = Document.objects.create(file=upload, title="Buyruq 42")
    document.refresh_from_db()

    assert document.file_size == len(b"%PDF-1.4 fake pdf bytes")
    assert document.filename == "order-42.pdf"


@pytest.mark.django_db
def test_document_rejects_non_pdf_files():
    # Only PDF is accepted for now — the old site's one real document type —
    # rather than opening this up to arbitrary uploaded file types.
    upload = SimpleUploadedFile("not-a-pdf.exe", b"MZ fake binary", content_type="application/octet-stream")

    document = Document(file=upload, title="Suspicious file")
    with pytest.raises(ValidationError):
        document.full_clean()
