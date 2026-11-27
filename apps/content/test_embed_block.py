"""An `embed` block is a video the page shows from YouTube. It used to be an <iframe> inside a legacy `raw_html` block; as a typed block the
page keeps only the video's id (and a title), so there is no markup to sanitize and no address to get wrong."""
import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.content.models import ContentBlock, Page

LANGS = ("uz", "ru", "en")


def block(**payload):
    return {lang: dict(payload) for lang in LANGS}


def test_a_youtube_video_is_a_valid_block(db):
    page = Page.objects.create(slug="video-sahifa")
    embed = ContentBlock(page=page, order=1, block_type="embed", data=block(provider="youtube", video_id="Mg6MBqg4f5o", title="Konferensiya"))

    embed.full_clean()


@pytest.mark.parametrize("video_id", ["", "short", "has spaces!!", "x" * 12, "https://youtu.be/Mg6MBqg4f5o", None])
def test_a_video_id_that_is_not_eleven_plain_characters_is_refused(db, video_id):
    page = Page.objects.create(slug="video-sahifa")
    embed = ContentBlock(page=page, order=1, block_type="embed", data=block(provider="youtube", video_id=video_id))

    with pytest.raises(ValidationError):
        embed.full_clean()


def test_only_known_providers_are_allowed(db):
    page = Page.objects.create(slug="video-sahifa")
    embed = ContentBlock(page=page, order=1, block_type="embed", data=block(provider="evil", video_id="Mg6MBqg4f5o"))

    with pytest.raises(ValidationError):
        embed.full_clean()


def test_a_title_is_plain_text(db):
    page = Page.objects.create(slug="video-sahifa")
    embed = ContentBlock(page=page, order=1, block_type="embed", data=block(provider="youtube", video_id="Mg6MBqg4f5o", title="<b>x</b>"))

    with pytest.raises(ValidationError):
        embed.full_clean()


def test_the_public_api_serves_the_block(db):
    page = Page.objects.create(slug="video-sahifa")
    ContentBlock.objects.create(page=page, order=1, block_type="embed", data=block(provider="youtube", video_id="Mg6MBqg4f5o", title="Konferensiya"))

    body = APIClient().get("/api/v1/pages/video-sahifa/").json()

    assert body["blocks"][0]["block_type"] == "embed"
    assert body["blocks"][0]["data"]["uz"]["video_id"] == "Mg6MBqg4f5o"
