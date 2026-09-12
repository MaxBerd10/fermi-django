"""
Imports institute-wide leadership (rector, prorektorlar) from the old site's
live public API into StaffMember (institute_role="rektor"/"prorektor") —
these people belong to no single kafedra or faculty, unlike every other
StaffMember row, so they carry institute_role instead of department/faculty.

Same leader shape and per-id language alignment as faculty leaders — see
import_legacy_faculties.py's _align_leaders/_leader_bio for the identical
pattern this mirrors.

Usage:
    python manage.py import_legacy_institute_leaders --dry-run
    python manage.py import_legacy_institute_leaders
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.legacy_import.fetch import fetch_institute_leaders
from apps.content.legacy_import.html_to_text import html_to_plain_text
from apps.content.legacy_import.media import ImageDownloader
from apps.content.legacy_import.merge import OTHER_LANGS
from apps.departments.models import StaffMember

# The old site lists a placeholder row for a currently-unfilled prorector
# seat ("VAKANT"/"Вакансия"/"Vacancy") — not a real person, so it's never
# imported (skipping it here means the frontend's own name-based filter
# never has to see it in any language).
_VACANT_NAMES = {"vakant", "вакансия", "vacancy"}

_CATEGORY_TO_ROLE = {
    "rektor": StaffMember.INSTITUTE_ROLE_RECTOR,
    "prorektorlar": StaffMember.INSTITUTE_ROLE_VICE_RECTOR,
}


class Command(BaseCommand):
    help = "Import institute-wide leaders (rector, prorektorlar) from the old site's live API into StaffMember."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch and report only -- writes nothing."
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        images = ImageDownloader(
            on_error=lambda src, exc: self.stderr.write(self.style.WARNING(f"    could not load image {src[:80]}: {exc}"))
        )

        total = 0
        for category_slug, institute_role in _CATEGORY_TO_ROLE.items():
            category = fetch_institute_leaders(category_slug)
            rows = self._align_leaders(category.leaders_by_lang)
            rows = [row for row in rows if (row["uz"].get("name") or "").strip().lower() not in _VACANT_NAMES]

            self.stdout.write(f"{category_slug}: {len(rows)} real leader(s)")
            if dry_run:
                for row in rows:
                    self.stdout.write(f"  - {row['uz'].get('name')} | {row['uz'].get('position')}")
                total += len(rows)
                continue

            with transaction.atomic():
                StaffMember.objects.filter(institute_role=institute_role).delete()
                for index, row in enumerate(rows):
                    uz = row["uz"]
                    photo = images.get_or_download(uz.get("photo"))
                    StaffMember.objects.create(
                        institute_role=institute_role,
                        full_name_uz=(row["uz"].get("name") or "").strip(),
                        full_name_ru=(row["ru"].get("name") or "").strip(),
                        full_name_en=(row["en"].get("name") or "").strip(),
                        title_uz=(row["uz"].get("position") or "").strip(),
                        title_ru=(row["ru"].get("position") or "").strip(),
                        title_en=(row["en"].get("position") or "").strip(),
                        bio_uz=self._leader_bio(row["uz"]),
                        bio_ru=self._leader_bio(row["ru"]),
                        bio_en=self._leader_bio(row["en"]),
                        phone=uz.get("phone") or "",
                        email=uz.get("email") or "",
                        reception_days_uz=(row["uz"].get("receptionDays") or "").strip(),
                        reception_days_ru=(row["ru"].get("receptionDays") or "").strip(),
                        reception_days_en=(row["en"].get("receptionDays") or "").strip(),
                        photo=photo,
                        is_head=index == 0,
                        order=index,
                    )
            total += len(rows)

        verb = "Would import" if dry_run else "Imported"
        self.stdout.write(self.style.SUCCESS(f"\n{verb} {total} institute leader(s)."))

    # -- leaders (identical pattern to import_legacy_faculties.py) ---------

    @staticmethod
    def _align_leaders(leaders_by_lang: dict[str, list[dict]]) -> list[dict[str, dict]]:
        uz_leaders = leaders_by_lang.get("uz", [])
        by_id = {lang: {leader["id"]: leader for leader in leaders_by_lang.get(lang, [])} for lang in OTHER_LANGS}

        rows = []
        for leader in uz_leaders:
            row = {"uz": leader}
            for lang in OTHER_LANGS:
                row[lang] = by_id[lang].get(leader["id"], leader)
            rows.append(row)
        return rows

    @staticmethod
    def _leader_bio(leader: dict) -> str:
        parts = [html_to_plain_text(leader.get("activity")), html_to_plain_text(leader.get("biography"))]
        return "\n\n".join(p for p in parts if p)
