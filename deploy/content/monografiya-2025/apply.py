# Adds/renames the 2025 monograph (cover + PDF) on /blog/2042/monografiya
# (Faoliyat > Doktorantura > Monografiya). Files in this folder go to media/monografiya/.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/monografiya-2025/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/monografiya-2025/apply.py
#   MODE=restore ... (puts the page text back from the backup; the copied files stay, they are harmless)
import datetime
import glob
import json
import os
import shutil

from django.conf import settings
from django.db import transaction

from apps.content.models import ContentBlock, Page

MODE = os.environ.get("MODE", "dry")
SLUG = "monografiya"
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "monografiya-2025")
PDF = "monografiya-2025-rasulov-mt.pdf"
COVER = "monografiya-2025-muqova.jpg"
OLD_PDF = "monografiya-2025-rasulova-kadirova.pdf"
FILES = [COVER, PDF]
DEST_DIR = os.path.join(settings.MEDIA_ROOT, "monografiya")
BASE_URL = os.environ.get("SITE_URL", "https://fermi.uz").rstrip("/") + "/media/monografiya/"
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
TITLE = "Tibbiyot oliy ta’lim muassasalarida fundamental fanlarni integral tizimida o‘qitishning asosiy motivlari"
AUTHORS = "M.T. Rasulov, 2025"
OLD_AUTHORS = "M.T. Rasulova, M.R. Kadirova, 2025"
SNIPPET = (
    '<div style="max-width:320px;margin:0 auto 24px">'
    '<img src="%s%s" alt="Monografiya muqovasi: %s" width="1075" height="1520" decoding="async" />'
    "</div>\r\n"
    '<p><a href="%s%s">%s (%s)</a></p>\r\n\r\n<hr />\r\n'
) % (BASE_URL, COVER, TITLE, BASE_URL, PDF, TITLE, AUTHORS)


def block_of_page():
    page = Page.objects.filter(slug=SLUG).first()
    if page is None:
        raise SystemExit("STOP: page '%s' not found. Nothing was modified." % SLUG)
    blocks = list(page.blocks.filter(block_type="raw_html").order_by("order"))
    if not blocks:
        raise SystemExit("STOP: the page has no text block. Nothing was modified.")
    return blocks[0]


def rewrite_html(html):
    out = html.replace(OLD_PDF + "?v=20261012", PDF).replace(OLD_PDF, PDF)
    out = out.replace(OLD_AUTHORS, AUTHORS)
    return out


def copy_files():
    os.makedirs(DEST_DIR, exist_ok=True)
    for name in FILES:
        src = os.path.join(SRC_DIR, name)
        if not os.path.isfile(src):
            raise SystemExit("STOP: %s is missing (git pull first?). Nothing was modified." % src)
        shutil.copyfile(src, os.path.join(DEST_DIR, name))
    stale = os.path.join(DEST_DIR, OLD_PDF)
    if os.path.isfile(stale):
        os.remove(stale)
    if os.geteuid() == 0:
        import grp
        import pwd
        uid, gid = pwd.getpwnam("www-data").pw_uid, grp.getgrnam("www-data").gr_gid
        for path in [DEST_DIR] + [os.path.join(DEST_DIR, n) for n in FILES]:
            os.chown(path, uid, gid)


print("MODE:", MODE)
block = block_of_page()
langs = [l for l in ("uz", "ru", "en") if isinstance(block.data.get(l), dict) and block.data[l].get("html")]
print("page block id:", block.id, "| languages:", langs)

if MODE == "restore":
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "page-monografiya-*.json")))
    if not files:
        raise SystemExit("STOP: no backup file in " + BACKUP_DIR)
    old = json.load(open(files[-1]))
    ContentBlock.objects.filter(pk=old["id"]).update(data=old["data"])
    print("RESTORED from", files[-1])
else:
    needs_snippet = [l for l in langs if PDF not in block.data[l]["html"] and OLD_PDF not in block.data[l]["html"]]
    needs_rename = [l for l in langs if OLD_PDF in block.data[l]["html"] or OLD_AUTHORS in block.data[l]["html"]]
    print("will add the monograph to:", needs_snippet or "(already linked)")
    print("will rename rasulova-kadirova -> rasulov-mt in:", needs_rename or "(already named)")
    print("files to copy to", DEST_DIR, ":", FILES)
    if MODE == "apply":
        copy_files()
        print("COPIED files to", DEST_DIR)
        if needs_snippet or needs_rename:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            path = os.path.join(BACKUP_DIR, "page-monografiya-%s.json" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
            with open(path, "w") as fh:
                json.dump({"id": block.id, "data": block.data}, fh, ensure_ascii=True)
            data = json.loads(json.dumps(block.data))
            for l in langs:
                data[l]["html"] = rewrite_html(data[l]["html"])
            for l in needs_snippet:
                data[l]["html"] = SNIPPET + data[l]["html"]
            with transaction.atomic():
                block.data = data
                block.clean()
                block.save(update_fields=["data"])
            print("BACKUP:", path)
        print("DONE. The page shows it within about a minute (API cache): %s/blog/2042/monografiya" % "https://fermi.uz")
    else:
        print("DRY RUN: nothing was changed. Run again with MODE=apply to copy the files and update the page.")
