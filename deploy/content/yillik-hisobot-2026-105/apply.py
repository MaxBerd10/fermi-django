# NEWS POST yashil-universitet-yashil-makon (found by the post's slug): the first picture of the article was a different picture per language: the Uzbek text showed the poster "2025 YIL: Atrof-muhitni asrash va
# yashil iqtisodiyot yili" (Uzbek words and QR codes on it), the Russian and the English text a photo of the institute building in its park. A reader of one language saw another
# picture than a reader of another, and the poster's Uzbek words meant nothing to the Russian and English readers. As the user decided ("bitta rasm qolsin"), ALL THREE languages show the
# photo (the language-neutral one); the poster stays in the picture library (nothing is deleted). RUN AFTER scripts 39-104.
#
# SAFE BY DESIGN: dry (default) writes nothing; the picture is changed only if block 1 of the page still is the image block of the plan (the three files by name), otherwise the apply is
# cancelled; apply is one transaction with a backup (a second apply is refused); undo puts the old block back, only where the block still is what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-105/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-105/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-105/apply.py
import copy

from django.utils import timezone

from apps.content.migration_tools import run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image

NAME = "yillik-hisobot-2026-105"
SLUG = "yashil-universitet-yashil-makon"
POSTER_TAIL = "Yashil_makon_HeKcf7k.jpg"   # what the Uzbek text showed
PHOTO_TAIL = "17_4H5Llkj.jpg"             # what the Russian and the English text showed: now all three


def tail(image_id):
    image = Image.objects.filter(pk=image_id).first()
    return image.file.name.rsplit("/", 1)[-1] if image else None


def build(apply):
    # the article's text is the Page of the news post (its own slug is "news-<number>"); the post's slug is the address of the article
    block = ContentBlock.objects.filter(page__news_post__slug=SLUG, order=1).first()
    problem = None
    if block is None or block.block_type != "image":
        problem = "block 1 is not a picture"
    elif [tail(block.data[lang].get("image_id")) for lang in ("uz", "ru", "en")] != [POSTER_TAIL, PHOTO_TAIL, PHOTO_TAIL]:
        problem = "block 1 does not show the pictures of the plan any more (edited since)"
    if problem:
        print("SKIPPED %s #1: %s" % (SLUG, problem))
        print("\n0 change(s), 1 skipped.")
        if apply:
            raise SystemExit("STOP: the picture is not what the plan was made from, nothing was written.")
        return {}
    print("%s #1: the Uzbek text shows %s instead of %s (ru and en already show it)" % (SLUG, PHOTO_TAIL, POSTER_TAIL))
    print("\n1 change(s), 0 skipped.")
    if not apply:
        return {}
    old = copy.deepcopy(block.data)
    block.data["uz"]["image_id"] = block.data["ru"]["image_id"]
    block.full_clean()
    block.save(update_fields=["data"])
    Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
    return {"pk": block.pk, "old": old, "new_fp": sha(block.data)}


def undo(rows):
    block = ContentBlock.objects.filter(pk=rows["pk"]).first()
    if block is None or sha(block.data) != rows["new_fp"]:
        print("left block %s: it was edited or removed since" % rows["pk"])
        return
    block.data = rows["old"]
    block.save(update_fields=["data"])
    print("restored the old picture of the Uzbek text.")


run_modes(NAME, build, undo)
