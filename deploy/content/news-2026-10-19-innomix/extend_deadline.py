# The InnoMix contest was extended to the end of November: applications are now accepted until 30 November and the contest
# days will be announced later by the organisers. This rewrites the two lines of the live post that carried the old dates
# ("⏳ Loyihalar 31-oktabrgacha qabul qilinadi." and "📅 Tanlov 9–13-noyabr kunlari ...") in uz, ru and en, and nothing else:
# the poster, the list of directions, the prize line and the application form line stay as they are. (apply.py is the
# record of the first publish and is left untouched.)
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/news-2026-10-19-innomix/extend_deadline.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/news-2026-10-19-innomix/extend_deadline.py
#
# dry (default) only shows. It stops, changing nothing, if either old line is not there exactly as published (already
# extended, or edited by hand in the admin panel), so a second run is harmless.
import os

from django.db import transaction

from apps.content.models import ContentBlock
from apps.news.models import NewsPost

MODE = os.environ.get("MODE", "dry")
SLUG = "innomix-fjsti-innovatsion-loyihalar-tanlovi-2026"

# (old text per language, new text per language)
EDITS = [
    (
        {
            "uz": "⏳ Loyihalar 31-oktabrgacha qabul qilinadi.",
            "ru": "⏳ Проекты принимаются до 31 октября.",
            "en": "⏳ Projects are accepted until 31 October.",
        },
        {
            "uz": "⏳ Muddat uzaytirildi! Loyihalar 30-noyabrgacha qabul qilinadi.",
            "ru": "⏳ Срок продлён! Проекты принимаются до 30 ноября.",
            "en": "⏳ Deadline extended! Projects are accepted until 30 November.",
        },
    ),
    (
        {
            "uz": "📅 Tanlov 9–13-noyabr kunlari boʻlib oʻtadi.",
            "ru": "📅 Конкурс пройдёт 9–13 ноября.",
            "en": "📅 The contest takes place on 9–13 November.",
        },
        {
            "uz": "📅 Tanlov kunlari keyinroq eʼlon qilinadi.",
            "ru": "📅 Даты проведения конкурса будут объявлены дополнительно.",
            "en": "📅 The contest dates will be announced later.",
        },
    ),
]

print("MODE:", MODE)
post = NewsPost.objects.filter(slug=SLUG).first()
if post is None:
    raise SystemExit("STOP: the post '%s' was not found. Nothing was modified." % SLUG)
blocks = [b for b in ContentBlock.objects.filter(page=post.page).order_by("order") if b.block_type == "paragraph"]

plan = []
for old, new in EDITS:
    hit = [b for b in blocks if all((b.data.get(lang) or {}).get("text") == old[lang] for lang in ("uz", "ru", "en"))]
    if len(hit) != 1:
        raise SystemExit("STOP: the line '%s' is not there exactly once in all three languages (found %d). Nothing was modified." % (old["uz"], len(hit)))
    plan.append((hit[0], new))

for block, new in plan:
    for lang in ("uz", "ru", "en"):
        print("%s: %s  ->  %s" % (lang, block.data[lang]["text"], new[lang]))
if MODE != "apply":
    print("DRY RUN: nothing was changed. Run again with MODE=apply to write the new lines.")
else:
    with transaction.atomic():
        for block, new in plan:
            for lang in ("uz", "ru", "en"):
                block.data[lang]["text"] = new[lang]
            block.save(update_fields=["data"])
        post.save()  # touches the post so the site's caches see the change
    print("DONE: the post now says applications are accepted until 30 November.")
    print("(the site shows it within about a minute)")
