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


def test_a_storage_failure_rolls_the_submission_back_and_says_so(db, monkeypatch):
    """The 2026-10-04 incident: the disk refused the attachment, the request died with a 500, and 48 half-saved
    applications (name and phone, no document) were left behind."""
    from rest_framework.test import APIClient

    from apps.content.models import Page
    from apps.forms.models import ContestSubmission
    from apps.news.models import NewsPost
    from django.utils import timezone

    contest = NewsPost.objects.create(
        slug="c", title_uz="C", title_ru="C", title_en="C", excerpt_uz="x", excerpt_ru="x", excerpt_en="x",
        page=Page.objects.create(slug="c"), published_at=timezone.now(),
    )

    def refuse(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr("django.db.models.fields.files.FieldFile.save", refuse)
    payload = {
        "contestId": contest.id, "fullName": "Test Person", "phone": "+998901234567", "email": "a@b.uz",
        "file": SimpleUploadedFile("hujjat.pdf", b"%PDF-1.4 x", content_type="application/pdf"),
    }
    res = APIClient().post("/api/v1/forms/contest", payload, format="multipart")

    assert res.status_code == 503
    assert "qayta" in res.json()["detail"]
    assert ContestSubmission.objects.count() == 0
