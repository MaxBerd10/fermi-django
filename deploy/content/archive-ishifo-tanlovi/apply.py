# Closes the "Startap loyihalar - 2026 / iShifo" contest (its deadline has passed): the post moves from the "Tanlovlar"
# category to a "Tanlovlar arxivi" category. That removes it from the home page's "Ochiq tanlovlar" shelf and from the
# "Tanlovlar" list, replaces the application form on its page with an "applications are closed" note, and makes the
# server refuse any new application for it. A "Tanlovlar arxivi" entry is added under the "Tanlovlar" menu item so
# the archive can be found. Nothing is deleted; the applications already received stay in the admin inbox.
#
# Next time a contest ends, no script is needed: in the admin panel open the news post and change its category to
# "Tanlovlar arxivi".
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/archive-ishifo-tanlovi/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/archive-ishifo-tanlovi/apply.py
#   SLUG=innomix-fjsti-innovatsion-loyihalar-tanlovi-2026 MODE=apply .venv/bin/python manage.py shell < deploy/content/archive-ishifo-tanlovi/apply.py   (any other contest)
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/archive-ishifo-tanlovi/apply.py   (reopens the contest)
import os

from django.db import transaction

from apps.menu.models import MenuItem
from apps.news.models import NewsCategory, NewsPost

MODE = os.environ.get("MODE", "dry")
# default: the iShifo contest; another contest: SLUG=<its-slug> MODE=apply ...
POST_SLUG = os.environ.get("SLUG", "ishifo-startap-loyihalar-2026-tanlovi")
OPEN_SLUG, ARCHIVE_SLUG = "tanlovlar", "tanlovlar-arxivi"
ARCHIVE_NAMES = {"uz": "Tanlovlar arxivi", "ru": "Архив конкурсов", "en": "Contests archive"}
OPEN_MENU_URL = "/news/0/tanlovlar"
ARCHIVE_MENU_URL = "/news/0/tanlovlar-arxivi"

print("MODE:", MODE)
post = NewsPost.objects.filter(slug=POST_SLUG).first()
if post is None:
    raise SystemExit("STOP: the post '%s' was not found. Nothing was modified." % POST_SLUG)
print("post:", post.pk, post.title_uz[:70], "| category now:", post.category.slug if post.category else None)
parent = MenuItem.objects.filter(url=OPEN_MENU_URL, parent__isnull=True).first()
print("menu parent 'Tanlovlar':", parent.pk if parent else "NOT FOUND (the archive menu entry will be skipped)")

if MODE == "dry":
    print("DRY RUN: nothing was changed. Run again with MODE=apply to archive it.")
elif MODE == "apply":
    with transaction.atomic():
        archive, created = NewsCategory.objects.get_or_create(
            slug=ARCHIVE_SLUG, defaults={"name_uz": ARCHIVE_NAMES["uz"], "name_ru": ARCHIVE_NAMES["ru"], "name_en": ARCHIVE_NAMES["en"]}
        )
        post.category = archive
        post.save(update_fields=["category"])
        if parent is not None and not MenuItem.objects.filter(url=ARCHIVE_MENU_URL).exists():
            MenuItem.objects.create(
                parent=parent, label_uz=ARCHIVE_NAMES["uz"], label_ru=ARCHIVE_NAMES["ru"], label_en=ARCHIVE_NAMES["en"],
                url=ARCHIVE_MENU_URL, order=1,
            )
    print("DONE. Archived; category '%s' %s." % (ARCHIVE_SLUG, "created" if created else "already existed"))
    print("(the site shows the change within about a minute)")
elif MODE == "undo":
    opened = NewsCategory.objects.filter(slug=OPEN_SLUG).first()
    if opened is None:
        raise SystemExit("STOP: category '%s' not found." % OPEN_SLUG)
    post.category = opened
    post.save(update_fields=["category"])
    print("DONE. The contest is open again (the archive category and its menu entry were left in place).")
else:
    raise SystemExit("Unknown MODE: %s" % MODE)
