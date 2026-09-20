from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from apps.forms.views import MAX_VISITOR_UPLOAD_BYTES, validate_visitor_upload


def test_visitor_upload_accepts_a_pdf():
    validate_visitor_upload(SimpleUploadedFile("murojaat.pdf", b"%PDF-1.4"))


def test_visitor_upload_rejects_browser_executable_files():
    upload = SimpleUploadedFile("xss.html", b"<script>alert(1)</script>")

    try:
        validate_visitor_upload(upload)
    except ValidationError as exc:
        assert "file" in exc.detail
    else:
        raise AssertionError("An HTML upload must be rejected")


def test_visitor_upload_rejects_files_over_ten_megabytes():
    upload = SimpleUploadedFile("katta.pdf", b"0" * (MAX_VISITOR_UPLOAD_BYTES + 1))

    try:
        validate_visitor_upload(upload)
    except ValidationError as exc:
        assert "file" in exc.detail
    else:
        raise AssertionError("An over-limit upload must be rejected")
