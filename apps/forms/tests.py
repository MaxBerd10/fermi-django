"""Coverage for the three public form endpoints (previously entirely
missing -- see each model's own docstring): every visitor submission that
reaches this API has to actually land in the database, since none of it can
be recovered from the old site if lost (see DEPLOYMENT.md's backup note).
"""
from django.core.files.uploadedfile import SimpleUploadedFile

import pytest
from rest_framework.test import APIClient

from apps.content.models import Page
from apps.faculties.models import Faculty
from apps.forms.models import AcceptanceSubmission, ContactSubmission, VirtualSubmission


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def faculty(db):
    page = Page.objects.create(slug="test-faculty-page")
    return Faculty.objects.create(slug="test-faculty", name_uz="X", name_ru="X", name_en="X", page=page)


# --- /forms/contact ----------------------------------------------------

def test_contact_submission_is_saved_and_returns_no_content(client, db):
    res = client.post(
        "/api/v1/forms/contact",
        {"name": "Aliyev Vali", "email": "vali@example.com", "phone": "+998900000000",
         "subject": "Savol bor", "message": "Assalomu alaykum, savolim bor edi."},
        format="json",
    )
    assert res.status_code == 204
    submission = ContactSubmission.objects.get()
    assert submission.name == "Aliyev Vali"
    assert submission.is_read is False


def test_contact_submission_requires_message(client, db):
    res = client.post(
        "/api/v1/forms/contact",
        {"name": "Aliyev Vali", "email": "vali@example.com", "phone": "+998900000000", "subject": "Savol"},
        format="json",
    )
    assert res.status_code == 400
    assert not ContactSubmission.objects.exists()


# --- /forms/qabul --------------------------------------------------------

def test_qabul_submission_maps_camelcase_fields_and_returns_id(client, db):
    res = client.post(
        "/api/v1/forms/qabul",
        {
            "categoryId": 3, "fish": "Karimova Nilufar", "subject": "Bakalavriat",
            "phone": "+998911234567", "email": "nilufar@example.com",
            "regionId": 1, "districtId": 2, "quarterId": 4,
        },
        format="json",
    )
    assert res.status_code == 200
    assert res.data["submitted"] is True
    submission = AcceptanceSubmission.objects.get(id=res.data["id"])
    assert submission.category_id == 3
    assert submission.quarter_id == 4


def test_qabul_submission_allows_optional_ids_to_be_omitted(client, db):
    res = client.post(
        "/api/v1/forms/qabul",
        {"fish": "Karimova Nilufar", "phone": "+998911234567", "email": "nilufar@example.com"},
        format="json",
    )
    assert res.status_code == 200
    submission = AcceptanceSubmission.objects.get(id=res.data["id"])
    assert submission.category_id is None


# --- /forms/virtual-reception --------------------------------------------

def test_virtual_reception_submission_without_file(client, db):
    res = client.post(
        "/api/v1/forms/virtual-reception",
        {
            "fish": "Tursunov Aziz", "provinceId": 1, "districtId": 2,
            "address": "Farg'ona sh.", "phone": "+998933334455", "email": "aziz@example.com",
            "gender": "male", "text": "Savolim bor.",
        },
    )
    assert res.status_code == 200
    submission = VirtualSubmission.objects.get(id=res.data["id"])
    assert submission.faculty_id is None
    assert submission.file is None


def test_virtual_reception_submission_with_file_attaches_a_document(client, db):
    upload = SimpleUploadedFile("murojaat.pdf", b"%PDF-1.4 fake pdf bytes", content_type="application/pdf")
    res = client.post(
        "/api/v1/forms/virtual-reception",
        {
            "fish": "Tursunov Aziz", "phone": "+998933334455", "email": "aziz@example.com",
            "text": "Ilova biriktirilgan.", "file": upload,
        },
        format="multipart",
    )
    assert res.status_code == 200
    submission = VirtualSubmission.objects.get(id=res.data["id"])
    assert submission.file is not None
    assert submission.file.filename == "murojaat.pdf"


def test_virtual_reception_does_not_reject_a_non_pdf_xlsx_upload(client, db):
    # Documented current behavior, not a desired one: the manually-attached
    # Document here skips media_lib.Document's own
    # FileExtensionValidator(["pdf", "xlsx"]) because the view never calls
    # full_clean() on it (see VirtualReceptionFormView.post's own comment).
    upload = SimpleUploadedFile("rasm.jpg", b"\xff\xd8\xff\xe0fakejpeg", content_type="image/jpeg")
    res = client.post(
        "/api/v1/forms/virtual-reception",
        {"fish": "Ochilova Malika", "phone": "+998900000001", "email": "m@example.com", "text": "Rasm.", "file": upload},
        format="multipart",
    )
    assert res.status_code == 200
    submission = VirtualSubmission.objects.get(id=res.data["id"])
    assert submission.file.filename == "rasm.jpg"


def test_virtual_reception_links_a_real_faculty(client, faculty):
    # Unlike category_id/region_id/district_id elsewhere in apps.forms
    # (plain, unenforced id labels), VirtualSubmission.faculty is a real
    # ForeignKey -- facultyId must reference a Faculty that actually exists.
    res = client.post(
        "/api/v1/forms/virtual-reception",
        {"fish": "Yusupov Bekzod", "phone": "+998900000002", "email": "b@example.com", "text": "Savol.", "facultyId": faculty.id},
    )
    assert res.status_code == 200
    submission = VirtualSubmission.objects.get(id=res.data["id"])
    assert submission.faculty_id == faculty.id


def test_virtual_reception_rejects_a_nonexistent_faculty_id(client, db):
    # facultyId is a PrimaryKeyRelatedField (not a plain IntegerField, unlike
    # category/region/district ids elsewhere in apps.forms) precisely so a
    # bad id fails validation here with a clean 400, instead of reaching
    # save() and raising an unhandled IntegrityError against the real
    # ForeignKey (which would surface as an unhandled 500 in production).
    res = client.post(
        "/api/v1/forms/virtual-reception",
        {"fish": "Yusupov Bekzod", "phone": "+998900000002", "email": "b@example.com", "text": "Savol.", "facultyId": 999999},
    )
    assert res.status_code == 400
    assert not VirtualSubmission.objects.exists()


# --- Rate limiting: shared "public_form" throttle scope ---------------------

def test_public_form_throttle_is_shared_across_all_three_endpoints(client, db):
    # DEFAULT_THROTTLE_RATES["public_form"] = "10/min", and all three views
    # share that one scope -- so 10 total requests across contact/qabul are
    # allowed before the 11th (to either endpoint) is throttled.
    for i in range(5):
        res = client.post(
            "/api/v1/forms/contact",
            {"name": f"Flood {i}", "email": f"f{i}@example.com", "phone": "+998900000000",
             "subject": "Spam", "message": "Spam"},
            format="json",
        )
        assert res.status_code == 204

    for i in range(5):
        res = client.post(
            "/api/v1/forms/qabul",
            {"fish": f"Flood {i}", "phone": "+998900000000", "email": f"g{i}@example.com"},
            format="json",
        )
        assert res.status_code == 200

    res = client.post(
        "/api/v1/forms/contact",
        {"name": "Overflow", "email": "over@example.com", "phone": "+998900000000",
         "subject": "Spam", "message": "Spam"},
        format="json",
    )
    assert res.status_code == 429
