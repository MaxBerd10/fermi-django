"""Moves what visitors attached to the reception / contest forms before the private area existed
(media/uploads/documents/<year>/<month>/...) into the private area, so /media/ stops serving them.

    manage.py move_visitor_uploads            # dry run: lists what would move
    manage.py move_visitor_uploads --apply    # backs the old paths up (JSON), then moves
    manage.py move_visitor_uploads --restore  # puts the latest backup's files back where they were

Only documents that nothing but a visitor submission points at are touched; a document that is also used by the
site itself (a schedule, admission results, ...) is reported and left alone. Run it as www-data or as root: as
root it hands the new folders back to www-data, the user the site runs as.
"""
import glob
import json
import os
import shutil
import uuid
from datetime import datetime

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from apps.forms.models import ContestSubmission, VirtualSubmission
from apps.media_lib.models import Document
from apps.media_lib.private import PRIVATE_PREFIX, is_private_path

SUBMISSION_MODELS = (VirtualSubmission, ContestSubmission)
BACKUP_GLOB = "visitor-uploads-*.json"


def _other_references(document):
    """Models other than the visitor submissions that point at this document."""
    found = []
    # include_hidden: the site's own links to a document (schedules, admission results) are declared with
    # related_name="+", which the plain `related_objects` listing leaves out.
    for rel in Document._meta.get_fields(include_hidden=True):
        if not (rel.auto_created and not rel.concrete and (rel.one_to_many or rel.one_to_one)):
            continue
        if rel.related_model in SUBMISSION_MODELS:
            continue
        if rel.related_model._default_manager.filter(**{rel.field.name: document}).exists():
            found.append(rel.related_model.__name__)
    return found


def _hand_to_www_data(paths):
    if os.geteuid() != 0:
        return
    import grp
    import pwd

    uid, gid = pwd.getpwnam("www-data").pw_uid, grp.getgrnam("www-data").gr_gid
    for path in paths:
        os.chown(path, uid, gid)


class Command(BaseCommand):
    help = "Move old visitor attachments into the private (not publicly served) area."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="really move the files")
        parser.add_argument("--restore", action="store_true", help="undo the latest --apply")
        parser.add_argument("--backup-dir", default="/var/backups/fermi-django")

    def handle(self, *args, **options):
        if options["restore"]:
            return self._restore(options["backup_dir"])

        ids = set()
        for model in SUBMISSION_MODELS:
            ids |= set(model.objects.exclude(file=None).values_list("file_id", flat=True))
        plan, skipped = [], []
        for document in Document.objects.filter(pk__in=ids).order_by("pk"):
            name = document.file.name
            if is_private_path(name):
                continue
            shared = _other_references(document)
            if shared:
                skipped.append((document.pk, name, "also used by " + ", ".join(shared)))
            elif not default_storage.exists(name):
                skipped.append((document.pk, name, "file is missing on disk"))
            else:
                plan.append((document, name, f"{PRIVATE_PREFIX}{uuid.uuid4().hex}/{os.path.basename(name)}"))

        self.stdout.write(f"visitor documents already private: {len(ids) - len(plan) - len(skipped)}")
        self.stdout.write(f"to move: {len(plan)}")
        for document, old, new in plan:
            self.stdout.write(f"  #{document.pk}  {old}  ->  {new}")
        for pk, name, why in skipped:
            self.stdout.write(self.style.WARNING(f"  SKIPPED #{pk} {name}: {why}"))
        if not options["apply"]:
            self.stdout.write("DRY RUN: nothing was moved. Run again with --apply to move.")
            return
        if not plan:
            self.stdout.write("Nothing to move.")
            return

        os.makedirs(options["backup_dir"], exist_ok=True)
        backup = os.path.join(options["backup_dir"], f"visitor-uploads-{datetime.now():%Y%m%d-%H%M%S}.json")
        with open(backup, "w") as fh:
            json.dump([{"id": d.pk, "old": old, "new": new} for d, old, new in plan], fh, ensure_ascii=True)
        for document, old, new in plan:
            self._move(document, old, new)
        self.stdout.write(self.style.SUCCESS(f"MOVED {len(plan)} file(s). Backup: {backup}"))

    def _move(self, document, old, new):
        source, target = default_storage.path(old), default_storage.path(new)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.move(source, target)
        _hand_to_www_data([os.path.dirname(target), target])
        document.file.name = new
        document.save(update_fields=["file"])

    def _restore(self, backup_dir):
        files = sorted(glob.glob(os.path.join(backup_dir, BACKUP_GLOB)))
        if not files:
            raise CommandError("no backup file in " + backup_dir)
        entries = json.load(open(files[-1]))
        for entry in entries:
            document = Document.objects.filter(pk=entry["id"]).first()
            if document is None or document.file.name != entry["new"]:
                self.stdout.write(self.style.WARNING(f"  skipped #{entry['id']} (changed since)"))
                continue
            source, target = default_storage.path(entry["new"]), default_storage.path(entry["old"])
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.move(source, target)
            _hand_to_www_data([target])
            document.file.name = entry["old"]
            document.save(update_fields=["file"])
        self.stdout.write(self.style.SUCCESS(f"RESTORED from {files[-1]}"))
