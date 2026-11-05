# One-off fix for the live "Ekofaol yoshlar" post: the first publish (apply.py at 748fd87) carried a second paragraph that
# was not in the author's text ("Tadbir davomida ishtirokchilar institut hududidagi daraxtlar tanasini oqladi ..." and its
# ru/en translations). This deletes exactly that paragraph block (it holds all three languages) and nothing else: the
# first paragraph, the cover and the gallery stay. apply.py itself no longer creates the extra paragraph.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-ekofaol-yoshlar/trim_extra_paragraph.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-ekofaol-yoshlar/trim_extra_paragraph.py
#
# dry (default) only shows; if the post no longer has that second paragraph (already trimmed, or edited by hand in the
# admin panel) it stops and changes nothing.
import os

from django.db import transaction

from apps.content.models import ContentBlock
from apps.news.models import NewsPost

MODE = os.environ.get("MODE", "dry")
SLUG = "ekofaol-yoshlar-loyihasi-ekologik-tadbirlar-yashil-universitet"
EXTRA_STARTS = "Tadbir davomida ishtirokchilar institut hududidagi daraxtlar"

print("MODE:", MODE)
post = NewsPost.objects.filter(slug=SLUG).first()
if post is None:
    raise SystemExit("STOP: the post '%s' was not found. Nothing was modified." % SLUG)
blocks = list(ContentBlock.objects.filter(page=post.page).order_by("order"))
print("blocks:", [(b.order, b.block_type) for b in blocks])
extra = [b for b in blocks if b.block_type == "paragraph" and (b.data.get("uz") or {}).get("text", "").startswith(EXTRA_STARTS)]
if len(extra) != 1:
    raise SystemExit("STOP: the extra paragraph is not there exactly once (found %d). Nothing was modified." % len(extra))
block = extra[0]
for lang in ("uz", "ru", "en"):
    print("%s: %s" % (lang, (block.data.get(lang) or {}).get("text", "")[:100]))
if MODE != "apply":
    print("DRY RUN: nothing was changed. Run again with MODE=apply to delete this paragraph.")
else:
    with transaction.atomic():
        block.delete()
        post.save()  # touches the post so the site's caches see the change
    print("DONE. Left:", [(b.order, b.block_type) for b in ContentBlock.objects.filter(page=post.page).order_by("order")])
    print("(the site shows it within about a minute)")
