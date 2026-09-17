"""Coverage for the admin_api views that operate on apps.forms,
apps.site_settings, and apps.admission_results models (this app has no
models of its own -- see admission_results_views.py, forms_views.py,
settings_views.py). Focuses on the behavior that's easy to silently break:
the shared IsAdminStaff permission boundary, the uz->ru/en fallback pattern
(and where it's deliberately absent), and the handful of API/model field-name
mismatches (quater_id, titlte) the frontend depends on.
"""
import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.admission_results.models import ResultCategory, ResultFile, ResultsPage
from apps.content.models import Page
from apps.faculties.models import Faculty
from apps.forms.models import AcceptanceSubmission, ContactSubmission, VirtualSubmission
from apps.media_lib.models import Document, Image
from apps.site_settings.models import SiteCounter, SiteLogo, SiteSetting, SocialNetwork, UsefulSite

User = get_user_model()

# The classic minimal 1x1 transparent PNG -- Image's post_init signal reads
# real width/height via Pillow (see ImageField(width_field=...)), so a bare
# path string only works if a real, valid image already sits there.
_PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _write_media_file(path: str, content: bytes = b"%PDF-1.4 fake pdf bytes") -> str:
    """Puts real bytes at `path` under the test's (isolated, tmp_path)
    MEDIA_ROOT, matching what a prior real upload (MediaUploadView) would
    have left behind -- resolve_or_create_image/document only work against
    a path that already exists in storage, same as production."""
    return default_storage.save(path, ContentFile(content))


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def faculty(db):
    page = Page.objects.create(slug="test-faculty-page")
    return Faculty.objects.create(slug="test-faculty", name_uz="X", name_ru="X", name_en="X", page=page)


def _bearer_client(user):
    client = APIClient()
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(username="admin", password="x", is_staff=True)


@pytest.fixture
def admin_client(staff_user):
    return _bearer_client(staff_user)


@pytest.fixture
def plain_user(db):
    return User.objects.create_user(username="visitor", password="x", is_staff=False)


@pytest.fixture
def plain_client(plain_user):
    return _bearer_client(plain_user)


# --- Shared permission boundary -------------------------------------------
# Every admin_api resource sets permission_classes = [IsAuthenticated,
# IsAdminStaff] identically (see common.py::IsAdminStaff) -- checked here
# against two representative endpoints (a plain list and a singleton)
# rather than duplicated 11 times over.

@pytest.mark.parametrize("url", ["/api/v1/admin/result-categories/", "/api/v1/admin/setting/"])
def test_admin_endpoint_rejects_anonymous(client, url, db):
    res = client.get(url)
    assert res.status_code == 401


@pytest.mark.parametrize("url", ["/api/v1/admin/result-categories/", "/api/v1/admin/setting/"])
def test_admin_endpoint_rejects_non_staff(plain_client, url, db):
    res = plain_client.get(url)
    assert res.status_code == 403


@pytest.mark.parametrize("url", ["/api/v1/admin/result-categories/", "/api/v1/admin/setting/"])
def test_admin_endpoint_allows_staff(admin_client, url, db):
    res = admin_client.get(url)
    assert res.status_code == 200


# --- admin/result-categories, admin/result-files ---------------------------

def test_result_category_create_falls_back_uz_to_blank_ru_en(admin_client, db):
    res = admin_client.post("/api/v1/admin/result-categories/", {"title_uz": "Davolash ishi"}, format="json")
    assert res.status_code == 201
    assert res.data["title_uz"] == "Davolash ishi"
    assert res.data["title_ru"] == "Davolash ishi"
    assert res.data["title_en"] == "Davolash ishi"


def test_result_category_create_keeps_explicit_ru_en(admin_client, db):
    res = admin_client.post(
        "/api/v1/admin/result-categories/",
        {"title_uz": "Davolash ishi", "title_ru": "Лечебное дело", "title_en": "General Medicine"},
        format="json",
    )
    assert res.status_code == 201
    assert res.data["title_ru"] == "Лечебное дело"
    assert res.data["title_en"] == "General Medicine"


def test_result_category_update_reapplies_fallback_when_ru_en_cleared(admin_client, db):
    category = ResultCategory.objects.create(title_uz="Farmatsiya", title_ru="Фармация", title_en="Pharmacy")
    res = admin_client.patch(f"/api/v1/admin/result-categories/{category.id}/", {"title_uz": "Farmatsiya 2"}, format="json")
    assert res.status_code == 200
    assert res.data["title_ru"] == "Farmatsiya 2"
    assert res.data["title_en"] == "Farmatsiya 2"


def test_result_category_delete_cascades_to_its_files(admin_client, db):
    category = ResultCategory.objects.create(title_uz="Pediatriya", title_ru="Педиатрия", title_en="Pediatrics")
    upload = SimpleUploadedFile("natija.pdf", b"%PDF-1.4 fake pdf bytes", content_type="application/pdf")
    document = Document.objects.create(file=upload, title="Natija")
    file_ = ResultFile.objects.create(
        category=category, document=document, title_uz="1-guruh", title_ru="1-я группа", title_en="Group 1",
    )
    res = admin_client.delete(f"/api/v1/admin/result-categories/{category.id}/")
    assert res.status_code == 204
    assert not ResultFile.objects.filter(id=file_.id).exists()


def test_result_file_create_resolves_document_from_bare_path_and_falls_back_titles(admin_client, db):
    category = ResultCategory.objects.create(title_uz="Stomatologiya", title_ru="Стоматология", title_en="Dentistry")
    path = _write_media_file("uploads/documents/2024/06/n1.pdf")
    res = admin_client.post(
        "/api/v1/admin/result-files/",
        {"title_uz": "Natija 1", "category_id": category.id, "file": path},
        format="json",
    )
    assert res.status_code == 201
    assert res.data["title_ru"] == "Natija 1"
    assert res.data["title_en"] == "Natija 1"
    assert res.data["file"].endswith(f"/{path}")
    assert Document.objects.filter(file=path).exists()


def test_result_file_create_reuses_existing_document_for_same_path(admin_client, db):
    category = ResultCategory.objects.create(title_uz="Farmatsiya", title_ru="Фармация", title_en="Pharmacy")
    path = _write_media_file("uploads/documents/2024/06/shared.pdf")
    existing = Document.objects.create(file=path, title="Shared")
    admin_client.post(
        "/api/v1/admin/result-files/",
        {"title_uz": "A", "category_id": category.id, "file": path},
        format="json",
    )
    assert Document.objects.filter(file=path).count() == 1
    assert ResultFile.objects.get(title_uz="A").document_id == existing.id


def test_result_file_update_without_category_id_keeps_existing_category(admin_client, db):
    category = ResultCategory.objects.create(title_uz="Cat A", title_ru="A", title_en="A")
    upload = SimpleUploadedFile("keep.pdf", b"%PDF-1.4 fake pdf bytes", content_type="application/pdf")
    document = Document.objects.create(file=upload, title="Keep")
    file_ = ResultFile.objects.create(category=category, document=document, title_uz="X", title_ru="X", title_en="X")
    res = admin_client.patch(f"/api/v1/admin/result-files/{file_.id}/", {"title_uz": "Y"}, format="json")
    assert res.status_code == 200
    file_.refresh_from_db()
    assert file_.category_id == category.id


# --- admin/results-page (singleton) -----------------------------------------

def test_results_page_get_auto_creates_singleton_row(admin_client, db):
    assert not ResultsPage.objects.exists()
    res = admin_client.get("/api/v1/admin/results-page/")
    assert res.status_code == 200
    assert res.data["results"][0]["id"] == 1


def test_results_page_update_falls_back_blank_ru_en_to_uz(admin_client, db):
    ResultsPage.get_solo()
    res = admin_client.patch(
        "/api/v1/admin/results-page/1/",
        {"heading_uz": "Natijalar", "intro_uz": "Kirish matni", "announcement_uz": "E'lon matni"},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["heading_ru"] == "Natijalar"
    assert res.data["heading_en"] == "Natijalar"
    assert res.data["intro_ru"] == "Kirish matni"
    assert res.data["announcement_en"] == "E'lon matni"


def test_results_page_update_keeps_explicit_ru_en(admin_client, db):
    ResultsPage.get_solo()
    res = admin_client.patch(
        "/api/v1/admin/results-page/1/",
        {"heading_uz": "Natijalar", "heading_ru": "Результаты", "heading_en": "Results"},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["heading_ru"] == "Результаты"
    assert res.data["heading_en"] == "Results"


# --- admin/contacts (perform_update side effect) ----------------------------

def test_contact_list_reports_unread_status(admin_client, db):
    ContactSubmission.objects.create(name="Ali", subject="Savol", phone="+998900000000", email="a@example.com", message="Salom")
    res = admin_client.get("/api/v1/admin/contacts/")
    assert res.status_code == 200
    assert res.data["results"][0]["status"] == 1  # unread


def test_contact_update_marks_it_read_as_a_side_effect(admin_client, db):
    submission = ContactSubmission.objects.create(
        name="Ali", subject="Savol", phone="+998900000000", email="a@example.com", message="Salom",
    )
    assert submission.is_read is False
    res = admin_client.patch(f"/api/v1/admin/contacts/{submission.id}/", {"subject": "Savol (ko'rildi)"}, format="json")
    assert res.status_code == 200
    submission.refresh_from_db()
    assert submission.is_read is True
    assert res.data["status"] == 0  # read


# --- admin/acceptances (quater_id -> quarter_id typo mapping) ---------------

def test_acceptance_create_maps_quater_id_to_quarter_id_field(admin_client, db):
    res = admin_client.post(
        "/api/v1/admin/acceptances/",
        {"fish": "Aliyev Vali", "phone": "+998900000000", "email": "v@example.com", "quater_id": 7},
        format="json",
    )
    assert res.status_code == 201
    assert res.data["quater_id"] == 7
    assert AcceptanceSubmission.objects.get(id=res.data["id"]).quarter_id == 7


# --- admin/virtual-submissions (plain faculty_id, read-only file) ----------

def test_virtual_submission_create_accepts_faculty_id(admin_client, faculty):
    res = admin_client.post(
        "/api/v1/admin/virtual-submissions/",
        {"fish": "Aliyeva Nilufar", "phone": "+998900000000", "email": "n@example.com", "text": "Savol", "faculty_id": faculty.id},
        format="json",
    )
    assert res.status_code == 201
    assert res.data["faculty_id"] == faculty.id
    assert res.data["file"] is None


def test_virtual_submission_file_field_is_read_only(admin_client, db):
    upload = SimpleUploadedFile("v.pdf", b"%PDF-1.4 fake pdf bytes", content_type="application/pdf")
    document = Document.objects.create(file=upload, title="V")
    submission = VirtualSubmission.objects.create(
        fish="Karimov Sardor", phone="+998900000000", email="s@example.com", text="Savol", file=document,
    )
    res = admin_client.get(f"/api/v1/admin/virtual-submissions/{submission.id}/")
    assert res.data["file"].endswith(document.file.name)
    # Attempting to change it via the admin API is silently ignored -- "file"
    # has no write path in this serializer at all (see AdminVirtualSubmissionSerializer).
    other_path = _write_media_file("uploads/documents/2024/06/other.pdf")
    admin_client.patch(f"/api/v1/admin/virtual-submissions/{submission.id}/", {"file": other_path}, format="json")
    submission.refresh_from_db()
    assert submission.file_id == document.id


# --- admin/setting: NO uz->ru/en fallback (contrast with the above) --------

def test_setting_update_does_not_fall_back_blank_address_ru_en(admin_client, db):
    SiteSetting.get_solo()
    res = admin_client.patch(
        "/api/v1/admin/setting/1/",
        {"phone": "+998732430000", "email": "info@fjsti.uz", "address_uz": "Farg'ona sh."},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["address_uz"] == "Farg'ona sh."
    assert res.data["address_ru"] == ""
    assert res.data["address_en"] == ""


# --- admin/logo: also no fallback, per-field passthrough -------------------

def test_logo_update_sets_fields_independently_without_fallback(admin_client, db):
    SiteLogo.get_solo()
    res = admin_client.patch("/api/v1/admin/logo/1/", {"title_uz": "FJSTI"}, format="json")
    assert res.status_code == 200
    assert res.data["title_uz"] == "FJSTI"
    assert res.data["title_ru"] == ""
    assert res.data["title_en"] == ""


def test_logo_update_resolves_image_from_bare_path(admin_client, db):
    SiteLogo.get_solo()
    path = _write_media_file("uploads/2024/06/logo.png", content=_PNG_1PX)
    res = admin_client.patch("/api/v1/admin/logo/1/", {"img": path}, format="json")
    assert res.status_code == 200
    assert res.data["img"].endswith(f"/{path}")
    assert Image.objects.filter(file=path).exists()


# --- admin/counter: plain passthrough ---------------------------------------

def test_counter_update_persists_numeric_fields(admin_client, db):
    SiteCounter.get_solo()
    res = admin_client.patch(
        "/api/v1/admin/counter/1/",
        {"professor_teachers": 120, "students": 3500, "graduaters": 900, "book_fund": 45000},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["students"] == 3500


# --- admin/networks: "titlte" typo field mapping ----------------------------

def test_network_create_maps_titlte_to_title_field(admin_client, db):
    res = admin_client.post(
        "/api/v1/admin/networks/",
        {"titlte": "Telegram", "icon": "ri-telegram-line", "url": "https://t.me/fjsti"},
        format="json",
    )
    assert res.status_code == 201
    assert res.data["titlte"] == "Telegram"
    assert SocialNetwork.objects.get(id=res.data["id"]).title == "Telegram"


# --- admin/useful-sites: uz->ru/en fallback, like result-categories --------

def test_useful_site_create_falls_back_uz_to_blank_ru_en(admin_client, db):
    res = admin_client.post(
        "/api/v1/admin/useful-sites/", {"title_uz": "Vazirlik", "url": "https://gov.uz"}, format="json",
    )
    assert res.status_code == 201
    assert res.data["title_ru"] == "Vazirlik"
    assert res.data["title_en"] == "Vazirlik"
    assert UsefulSite.objects.get(id=res.data["id"]).url == "https://gov.uz"
