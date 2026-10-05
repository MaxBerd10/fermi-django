"""Regression coverage for the admin-panel audit: server-side search on every list,
draft/scheduled news, an editable publication date, unique slugs, 400s instead of 500s,
and the inbound-submission review workflow."""
import base64
from datetime import datetime, timedelta, timezone as dt_timezone

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.content.models import Page
from apps.departments.models import StaffMember
from apps.faculties.models import Faculty
from apps.forms.models import ContactSubmission, ContestSubmission
from apps.media_lib.models import Document
from apps.news.models import NewsCategory, NewsPost

User = get_user_model()
ADMIN = "/api/v1/admin"


def timezone_utc(hours: int):
    return dt_timezone(timedelta(hours=hours))


@pytest.fixture
def admin_client(db):
    user = User.objects.create_user(username="auditor", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


@pytest.fixture
def category(db):
    return NewsCategory.objects.create(slug="tadbirlar", name_uz="Tadbirlar", name_ru="Мероприятия", name_en="Events")


def _post(admin_client, category, **extra):
    body = {"title_uz": "Sinov yangilik", "content_uz": "<p>Matn</p>", "category_id": category.id}
    body.update(extra)
    return admin_client.post(f"{ADMIN}/news", body, format="json")


# --- search -----------------------------------------------------------------------------------

def test_news_search_filters_by_title_and_returns_nothing_for_a_miss(admin_client, category):
    _post(admin_client, category, title_uz="Eko klub aksiyasi")
    _post(admin_client, category, title_uz="Boshqa mavzu")

    hit = admin_client.get(f"{ADMIN}/news", {"search": "eko klub"})
    miss = admin_client.get(f"{ADMIN}/news", {"search": "zzz-yoq"})

    assert [r["title_uz"] for r in hit.data["results"]] == ["Eko klub aksiyasi"]
    assert miss.data["count"] == 0


@pytest.mark.parametrize("resource", ["pages", "faculty", "departments", "leaders", "gallery-images", "networks", "contacts"])
def test_every_admin_list_honours_the_search_param(admin_client, resource):
    # an empty-match search must not 500 and must not return more than the unfiltered list
    all_rows = admin_client.get(f"{ADMIN}/{resource}")
    searched = admin_client.get(f"{ADMIN}/{resource}", {"search": "zzz-no-such-text"})
    assert searched.status_code == 200
    assert searched.data["count"] == 0 <= all_rows.data["count"]


# --- draft / scheduled / dated news -----------------------------------------------------------

def test_a_draft_is_hidden_from_the_public_site_but_not_from_the_admin(admin_client, category):
    res = _post(admin_client, category, title_uz="Qoralama", status=0)
    slug, post_id = res.data["slug"], res.data["id"]

    assert admin_client.get(f"{ADMIN}/news/{post_id}").data["status"] == 0
    public = APIClient()
    assert public.get(f"/api/v1/news/{slug}/").status_code == 404
    assert slug not in [r["slug"] for r in public.get("/api/v1/news/").data["results"]]

    admin_client.put(f"{ADMIN}/news/{post_id}", {**res.data, "status": 1}, format="json")
    assert public.get(f"/api/v1/news/{slug}/").status_code == 200


def test_a_future_dated_post_is_not_public_until_its_date(admin_client, category):
    future = (timezone.now() + timedelta(days=3)).isoformat()
    res = _post(admin_client, category, title_uz="Rejalashtirilgan", date=future)
    assert APIClient().get(f"/api/v1/news/{res.data['slug']}/").status_code == 404


def test_the_publication_date_can_be_back_dated_from_the_form(admin_client, category):
    res = _post(admin_client, category, title_uz="Kecha", date="2026-09-24T12:00:00+05:00")
    assert res.status_code == 201
    expected = datetime(2026, 9, 24, 12, 0, tzinfo=timezone_utc(5))
    assert datetime.fromisoformat(admin_client.get(f"{ADMIN}/news/{res.data['id']}").data["date"]) == expected
    assert datetime.fromisoformat(APIClient().get(f"/api/v1/news/{res.data['slug']}/").data["published_at"]) == expected


def test_a_bad_date_is_a_400_not_a_crash(admin_client, category):
    res = _post(admin_client, category, date="kecha")
    assert res.status_code == 400 and "date" in res.data


def test_two_posts_with_the_same_title_get_distinct_slugs(admin_client, category):
    first = _post(admin_client, category, title_uz="Bir xil sarlavha")
    second = _post(admin_client, category, title_uz="Bir xil sarlavha")
    assert second.status_code == 201
    assert first.data["slug"] != second.data["slug"]


def test_a_title_that_slugifies_to_nothing_still_saves(admin_client, category):
    assert _post(admin_client, category, title_uz="Привет мир").status_code == 201


def test_an_unknown_category_is_a_400(admin_client):
    res = admin_client.post(f"{ADMIN}/news", {"title_uz": "X", "content_uz": "<p>x</p>", "category_id": 9999}, format="json")
    assert res.status_code == 400 and "category_id" in res.data


def test_admin_news_list_reports_real_view_counts(admin_client, category):
    res = _post(admin_client, category)
    NewsPost.objects.filter(pk=res.data["id"]).update(view_count=7)
    row = admin_client.get(f"{ADMIN}/news").data["results"][0]
    assert row["seen"] == 7


# --- leaders: validation is a 400, never a 500 --------------------------------------------------

@pytest.mark.parametrize("category_id", ["", None, "abc", 999999])
def test_creating_a_leader_with_a_missing_or_bad_category_is_a_400(admin_client, category_id):
    body = {"name_uz": "Aliyev Vali", "position_uz": "Mudir", "phone": "1", "email": "a@b.uz", "reception_days_uz": "Du"}
    if category_id is not None:
        body["category_id"] = category_id
    res = admin_client.post(f"{ADMIN}/leaders", body, format="json")
    assert res.status_code == 400, res.content


def test_a_leader_with_a_real_category_saves(admin_client, db):
    res = admin_client.post(
        f"{ADMIN}/leaders",
        {"name_uz": "Aliyev Vali", "position_uz": "Rektor", "category_id": 1, "phone": "1", "email": "a@b.uz", "reception_days_uz": "Du"},
        format="json",
    )
    assert res.status_code == 201 and StaffMember.objects.count() == 1


# --- inbound submissions: review workflow -------------------------------------------------------

def test_opening_a_submission_marks_it_read_and_the_form_can_mark_it_new_again(admin_client, db):
    sub = ContactSubmission.objects.create(name="Ali", subject="S", phone="1", email="a@b.uz", message="Salom")
    assert admin_client.get(f"{ADMIN}/contacts").data["results"][0]["status"] == 1

    opened = admin_client.get(f"{ADMIN}/contacts/{sub.id}")
    assert opened.data["status"] == 0 and opened.data["created_at"]

    admin_client.put(f"{ADMIN}/contacts/{sub.id}", {**opened.data, "status": 1}, format="json")
    sub.refresh_from_db()
    assert sub.is_read is False


def test_a_contest_submission_exposes_its_file_name_and_link(admin_client, db):
    doc = Document(title="cv.pdf")
    doc.file.save("cv.pdf", ContentFile(b"%PDF-1.4 x"), save=True)
    sub = ContestSubmission.objects.create(full_name="Ali", phone="1", email="a@b.uz", file=doc)

    row = admin_client.get(f"{ADMIN}/contest-submissions/{sub.id}").data
    assert row["file_name"] == "cv.pdf" and row["file"].endswith("cv.pdf")


# --- public contest form -------------------------------------------------------------------------

def _apply(client, **extra):
    data = {"fullName": "Ali Valiyev", "phone": "+998901112233", "email": "a@b.uz", "message": "Salom"}
    data.update(extra)
    return client.post("/api/v1/forms/contest", data, format="multipart")


def test_a_rejected_attachment_creates_no_submission(db):
    res = _apply(APIClient(), file=SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream"))
    assert res.status_code == 400
    assert ContestSubmission.objects.count() == 0


def test_an_accepted_attachment_lives_at_an_unguessable_url(db):
    res = _apply(APIClient(), file=SimpleUploadedFile("cv.pdf", b"%PDF-1.4 x", content_type="application/pdf"))
    assert res.status_code == 200
    name = ContestSubmission.objects.get().file.file.name
    assert name.endswith("/cv.pdf")
    random_dir = name.rsplit("/", 2)[-2]
    assert len(random_dir) == 32 and int(random_dir, 16) >= 0


# --- the global exception handler ----------------------------------------------------------------

def test_django_model_validation_errors_become_a_400(admin_client, db):
    # StaffMember.clean() raises django's ValidationError (not DRF's) for "no department/faculty/role".
    Faculty.objects.all().delete()
    res = admin_client.post(
        f"{ADMIN}/leaders",
        {"name_uz": "X", "position_uz": "Y", "category_id": 1001, "phone": "1", "email": "a@b.uz", "reception_days_uz": "Du"},
        format="json",
    )
    assert res.status_code == 400


# --- handover audit (2026-10-05): what a non-technical editor runs into ----------------------------

@pytest.mark.parametrize("resource, payload, field", [
    ("gallery-images", {"title_uz": "Rasm"}, "img"),
    ("schedules", {"title_uz": "Jadval", "course_id": None}, "course_id"),
    ("result-files", {"title_uz": "Natija", "category_id": None}, "category_id"),
])
def test_forgetting_the_file_is_a_readable_400_not_a_500(admin_client, db, resource, payload, field):
    res = admin_client.post(f"/api/v1/admin/{resource}", payload, format="json")
    assert res.status_code == 400
    assert field in res.json()


def test_validation_messages_reach_the_editor_in_uzbek(admin_client, db):
    res = admin_client.post("/api/v1/admin/networks", {"title": "x", "icon": "ri-x", "url": "not a url"}, format="json")
    assert res.status_code == 400
    assert res.json()["url"] == ["To'g'ri havola kiriting (https:// bilan boshlansin)."]


def test_deleting_something_still_in_use_explains_itself(admin_client, db):
    from apps.media_lib.models import Image, Video
    image = Image(alt_text="p")
    image.file.save("p.png", ContentFile(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")), save=True)
    Video.objects.create(file="v.mp4", poster=image)
    from django.db.models import ProtectedError
    with pytest.raises(ProtectedError):
        image.delete()
    from config.exception_handler import PROTECTED_MESSAGE, exception_handler
    response = exception_handler(ProtectedError("x", set()), {})
    assert response.status_code == 400 and response.data["detail"] == PROTECTED_MESSAGE


def test_a_web_address_typed_in_the_text_survives_a_save(admin_client, category):
    """Blocks store plain text, so the editor's link marks are not kept -- but a URL written out in the text is, and the
    public site turns it into a clickable link (frontend/src/blocks/LinkifiedText.tsx)."""
    html = "<p>Batafsil: https://fjsti.uz/aloqa yoki info@fjsti.uz</p>"
    res = admin_client.post("/api/v1/admin/news", {"title_uz": "LINK", "content_uz": html, "category_id": category.id}, format="json")
    assert res.status_code == 201, res.content
    back = admin_client.get(f"/api/v1/admin/news/{res.data['id']}").json()["content_uz"]
    assert "https://fjsti.uz/aloqa" in back and "info@fjsti.uz" in back
