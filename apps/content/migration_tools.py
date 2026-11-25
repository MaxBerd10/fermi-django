"""The toolkit under every content script (deploy/content/*/apply.py).

A script describes WHAT to change (`build`) and how to put it back (`undo`); this module gives it the safe skeleton the earlier scripts each
copied: dry run by default, one transaction, a backup file, a second apply refused, an undo that retires the backup, a fingerprint check that
skips a block someone edited in the admin since the plan was made, and pictures created from local files (owned by www-data when run as root).

    MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-NN/apply.py
    MODE=apply ...
    MODE=undo  ...
"""
import hashlib
import json
import os
import shutil
from datetime import datetime

from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.utils import timezone

from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document, Image

DEFAULT_BACKUP_DIR = "/var/backups/fermi-django"


def sha(payload) -> str:
    """Fingerprint of one language's payload of a block."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def fingerprint_ok(block: ContentBlock, expected: dict[str, str]) -> bool:
    """True while every language's payload is exactly what the plan was made from (nobody edited the block in the admin since)."""
    return all(sha(block.data.get(lang)) == fingerprint for lang, fingerprint in expected.items())


def _give_to_www_data(path: str) -> None:
    """Only when run as root: the file and every folder created under MEDIA_ROOT go to www-data (the site runs as www-data)."""
    if os.geteuid() != 0:
        return
    root = str(settings.MEDIA_ROOT)
    shutil.chown(path, "www-data", "www-data")
    folder = os.path.dirname(path)
    while folder.startswith(root) and len(folder) > len(root):
        try:
            if os.stat(folder).st_uid == 0:
                shutil.chown(folder, "www-data", "www-data")
        except OSError:
            pass
        folder = os.path.dirname(folder)


def make_image(path: str, alt_text: str = "") -> Image:
    """An Image row (real width and height computed by the model) from a local file."""
    image = Image(alt_text=alt_text)
    with open(path, "rb") as handle:
        image.file.save(os.path.basename(path), File(handle), save=True)
    _give_to_www_data(image.file.path)
    return image


def reuse_or_make_image(path: str, alt_text: str = "") -> Image:
    """make_image(), unless the library already holds this very file (same name stem, same size): then that row (a picture used on two pages is one row)."""
    stem, extension = os.path.splitext(os.path.basename(path))
    size = os.path.getsize(path)
    for image in Image.objects.filter(file__contains=stem, file__endswith=extension):
        try:
            if image.file.size == size:
                return image
        except (OSError, ValueError):
            continue
    return make_image(path, alt_text)


def image_from_media(media_path: str, alt_text: str = "") -> Image:
    """The Image row of a file that already lies in the media folder (`media_path` relative to MEDIA_ROOT, e.g. "migrated/img/x.jpg"):
    the existing row of that file, or a new row pointing at the file (it is not copied). Raises FileNotFoundError if the file is not there."""
    existing = Image.objects.filter(file=media_path).first()
    if existing:
        return existing
    if not os.path.isfile(os.path.join(str(settings.MEDIA_ROOT), media_path)):
        raise FileNotFoundError(f"{media_path} is not in {settings.MEDIA_ROOT}")
    image = Image(file=media_path, alt_text=alt_text)
    image.save()
    return image


def replace_blocks(page: Page, order: int, count: int, new_blocks: list[dict]) -> list[int]:
    """Replaces the `count` consecutive blocks starting at `order` ({"block_type", "data"} for each new one; count 0 only inserts, an empty
    list only deletes); later blocks move to make or close the room. Returns the new primary keys. Every new block is validated
    (ContentBlock.clean) before it is saved, so a malformed block cannot be written."""
    with transaction.atomic():
        page.blocks.filter(order__gte=order, order__lt=order + count).delete()
        shift = len(new_blocks) - count
        later = list(page.blocks.filter(order__gte=order + count).order_by("-order" if shift > 0 else "order"))
        for block in later:
            block.order += shift
            block.save(update_fields=["order"])
        pks = []
        for offset, spec in enumerate(new_blocks):
            block = ContentBlock(page=page, order=order + offset, block_type=spec["block_type"], data=spec["data"])
            block.full_clean()
            block.save()
            pks.append(block.pk)
        Page.objects.filter(pk=page.pk).update(updated_at=timezone.now())
    return pks


def replace_block(page: Page, order: int, new_blocks: list[dict]) -> list[int]:
    """The one block at `order` is replaced by `new_blocks`."""
    return replace_blocks(page, order, 1, new_blocks)


def make_document(path: str, title: str = "") -> Document:
    """A Document row (a downloadable file) from a local file."""
    document = Document(title=title)
    with open(path, "rb") as handle:
        document.file.save(os.path.basename(path), File(handle), save=True)
    _give_to_www_data(document.file.path)
    return document


class Backup:
    """The JSON file an apply leaves behind (what it created and the old payloads); a second apply is refused while it exists."""

    def __init__(self, name: str):
        self.dir = os.environ.get("BACKUP_DIR", DEFAULT_BACKUP_DIR)
        self.path = os.path.join(self.dir, f"{name}.json")

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def save(self, **rows) -> None:
        os.makedirs(self.dir, exist_ok=True)
        with open(self.path, "w", encoding="utf8") as handle:
            json.dump({"created_at": datetime.now().isoformat(), **rows}, handle, ensure_ascii=False)

    def load(self) -> dict:
        with open(self.path, encoding="utf8") as handle:
            return json.load(handle)

    def retire(self) -> None:
        os.rename(self.path, self.path + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))


def run_modes(name: str, build, undo) -> None:
    """The dry / apply / undo skeleton. `build(apply: bool) -> dict` prints what it would do (and does nothing) when apply is False,
    and when True does the writes and returns the rows the backup keeps; `undo(rows)` puts back what `build` made."""
    mode = os.environ.get("MODE", "dry")
    print("MODE:", mode)
    backup = Backup(name)
    if mode == "undo":
        if not backup.exists():
            raise SystemExit(f"STOP: no backup file ({backup.path}): nothing to undo.")
        with transaction.atomic():
            undo(backup.load())
        backup.retire()
        print("UNDONE (the backup was kept under a new name)")
        return
    if mode not in ("dry", "apply"):
        raise SystemExit("STOP: MODE must be dry, apply or undo.")
    if mode == "apply" and backup.exists():
        raise SystemExit(f"STOP: {backup.path} already exists, so this was applied before. Run MODE=undo first to redo it.")
    if mode == "dry":
        build(False)
        print("DRY RUN: nothing was changed. Run again with MODE=apply.")
        return
    with transaction.atomic():
        rows = build(True)
        backup.save(**rows)
    print("DONE. To put everything back: MODE=undo with the same command.")
