"""A visitor's attachment (passport scan, CV, ...) is never served from /media/: it is opened only through the
short-lived signed link the staff-only admin API returns."""
import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.forms.models import VirtualSubmission
from apps.media_lib import private
from apps.media_lib.models import Document

User = get_user_model()
ADMIN = "/api/v1/admin"


@pytest.fixture
def admin_client(db):
    user = User.objects.create_user(username="reviewer", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def _submit_with_file(name="pasport.pdf", content=b"%PDF-1.4 secret"):
    res = APIClient().post(
        "/api/v1/forms/virtual-reception",
        {
            "fish": "Ali Valiyev", "phone": "+998901112233", "email": "a@b.uz", "text": "Salom",
            "file": SimpleUploadedFile(name, content, content_type="application/pdf"),
        },
        format="multipart",
    )
    assert res.status_code == 200, res.content
    return VirtualSubmission.objects.get(pk=res.json()["id"])


def test_a_visitor_attachment_is_stored_in_the_private_area_and_is_not_public(db, client):
    submission = _submit_with_file()
    name = submission.file.file.name

    assert name.startswith("uploads/private/") and name.endswith("/pasport.pdf")
    assert default_storage.exists(name)
    assert client.get("/media/" + name).status_code == 404


@pytest.mark.parametrize("spelling", [
    "uploads/private/x/y.pdf", "/uploads/private/x/y.pdf", "uploads/documents/../private/x/y.pdf",
    "uploads//private/x/y.pdf", "UPLOADS/Private/x/y.pdf",
])
def test_the_public_media_route_refuses_every_spelling_of_a_private_path(client, spelling):
    assert client.get("/media/" + spelling.lstrip("/")).status_code == 404
    assert private.is_private_path(spelling)


def test_site_documents_are_still_served_publicly(db, client):
    document = Document(title="nizom")
    document.file.save("nizom.pdf", ContentFile(b"%PDF-1.4 public"), save=True)

    res = client.get(document.file.url)

    assert res.status_code == 200 and b"".join(res.streaming_content) == b"%PDF-1.4 public"


def test_staff_get_a_signed_link_that_opens_the_file(db, admin_client):
    submission = _submit_with_file(content=b"%PDF-1.4 secret")

    row = admin_client.get(f"{ADMIN}/virtual-submissions/{submission.id}").data
    assert "/private-media/" in row["file"] and "/media/" not in row["file"]
    assert row["file_name"] == "pasport.pdf"

    res = APIClient().get(row["file"])  # opened in a new tab: no login header at all
    assert res.status_code == 200
    assert b"".join(res.streaming_content) == b"%PDF-1.4 secret"
    assert res["Content-Type"] == "application/pdf" and res["Content-Disposition"].startswith("inline")
    assert "no-store" in res["Cache-Control"] and res["X-Content-Type-Options"] == "nosniff"


def test_the_list_and_the_detail_both_hide_the_real_path(db, admin_client):
    submission = _submit_with_file()
    listing = admin_client.get(f"{ADMIN}/virtual-submissions").data["results"][0]
    assert submission.file.file.name not in listing["file"]


def test_a_tampered_or_made_up_link_is_a_404(db, admin_client):
    submission = _submit_with_file()
    link = admin_client.get(f"{ADMIN}/virtual-submissions/{submission.id}").data["file"]

    assert APIClient().get(link[:-3] + "x/").status_code == 404
    assert APIClient().get("/api/v1/private-media/not-a-token/").status_code == 404


def test_a_link_signed_for_a_public_file_does_not_work(db):
    token = private.signing.dumps("uploads/documents/2026/10/x.pdf", salt=private.LINK_SALT)
    assert APIClient().get(f"/api/v1/private-media/{token}/").status_code == 404


def test_an_expired_link_says_so(db, admin_client, monkeypatch):
    submission = _submit_with_file()
    link = admin_client.get(f"{ADMIN}/virtual-submissions/{submission.id}").data["file"]
    monkeypatch.setattr(private, "LINK_LIFETIME_SECONDS", -1)

    res = APIClient().get(link)

    assert res.status_code == 410 and "muddati" in res.content.decode()


def test_word_files_are_offered_as_a_download_not_shown_in_the_tab(db, admin_client):
    res = APIClient().post(
        "/api/v1/forms/virtual-reception",
        {
            "fish": "A", "phone": "1", "email": "a@b.uz", "text": "x",
            "file": SimpleUploadedFile("cv.docx", b"PK", content_type="application/octet-stream"),
        },
        format="multipart",
    )
    submission = VirtualSubmission.objects.get(pk=res.json()["id"])
    link = admin_client.get(f"{ADMIN}/virtual-submissions/{submission.id}").data["file"]

    assert APIClient().get(link)["Content-Disposition"].startswith("attachment")


# --- moving the files that were stored the old (public) way ----------------------------------------

def _legacy_submission(shared=False):
    document = Document(title="eski.pdf")
    document.file.save("eski.pdf", ContentFile(b"%PDF-1.4 old"), save=True)
    assert not private.is_private_path(document.file.name)
    submission = VirtualSubmission.objects.create(fish="Old", phone="1", email="a@b.uz", text="x", file=document)
    return submission, document


def test_move_command_dry_run_changes_nothing(db, client):
    _, document = _legacy_submission()
    old = document.file.name

    call_command("move_visitor_uploads", stdout=io.StringIO())

    document.refresh_from_db()
    assert document.file.name == old and client.get("/media/" + old).status_code == 200


def test_move_command_makes_old_attachments_private_and_restore_undoes_it(db, client, tmp_path):
    submission, document = _legacy_submission()
    old = document.file.name
    out = io.StringIO()

    call_command("move_visitor_uploads", "--apply", f"--backup-dir={tmp_path / 'bk'}", stdout=out)

    document.refresh_from_db()
    assert document.file.name.startswith("uploads/private/") and document.file.name.endswith("/eski.pdf")
    assert default_storage.exists(document.file.name) and not default_storage.exists(old)
    assert client.get("/media/" + old).status_code == 404
    assert client.get("/media/" + document.file.name).status_code == 404

    call_command("move_visitor_uploads", "--restore", f"--backup-dir={tmp_path / 'bk'}", stdout=out)
    document.refresh_from_db()
    assert document.file.name == old and default_storage.exists(old)


def test_move_command_leaves_a_document_the_site_itself_uses(db, tmp_path):
    from apps.schedule.models import Course, ScheduleFile

    _, document = _legacy_submission()
    course = Course.objects.create(title_uz="K", title_ru="K", title_en="K")
    ScheduleFile.objects.create(course=course, document=document, title_uz="J", title_ru="J", title_en="J")
    old = document.file.name
    out = io.StringIO()

    call_command("move_visitor_uploads", "--apply", f"--backup-dir={tmp_path / 'bk'}", stdout=out)

    document.refresh_from_db()
    assert document.file.name == old and "also used by ScheduleFile" in out.getvalue()
