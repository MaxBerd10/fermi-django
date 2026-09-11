"""
Imports faculties from the old site's live public API into
Faculty/Page/ContentBlock/StaffMember (as faculty leaders).

A faculty's page content is structurally identical to a department's
(free-form HTML body -- see html_extract.py), but its "leaders" (dean,
vice-deans) come back from the API as already-structured JSON with a
stable numeric id per person, so they're aligned across languages by that
id instead of the department staff's photo-filename heuristic.

Usage mirrors import_legacy_departments -- see that command for the
--dry-run / idempotent-re-run rationale.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.legacy_import.fetch import fetch_faculty, fetch_faculty_slugs
from apps.content.legacy_import.html_extract import extract
from apps.content.legacy_import.html_to_text import html_to_plain_text
from apps.content.legacy_import.media import ImageDownloader
from apps.content.legacy_import.merge import LANGS, OTHER_LANGS, merge_languages
from apps.content.models import ContentBlock, Page
from apps.departments.models import StaffMember
from apps.faculties.models import Faculty


class Command(BaseCommand):
    help = "Import faculties from the old site's live API into Faculty/Page/ContentBlock/StaffMember(leaders)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch, extract, and report only -- writes nothing."
        )
        parser.add_argument("--slug", help="Import only this one faculty slug (for testing).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        only_slug = options.get("slug")
        self._images = ImageDownloader(
            on_error=lambda src, exc: self.stderr.write(self.style.WARNING(f"    could not load image {src[:80]}: {exc}"))
        )

        slugs = [only_slug] if only_slug else fetch_faculty_slugs()
        self.stdout.write(f"{len(slugs)} faculty(ies) to process.\n")

        done = 0
        for slug in slugs:
            fac = fetch_faculty(slug)
            results = {lang: extract(fac.content[lang]) for lang in LANGS}
            merged = merge_languages(results)
            leaders = self._align_leaders(fac.leaders_by_lang)

            self.stdout.write(
                f"[{fac.id}] {slug}: {len(merged.blocks)} blocks "
                f"({merged.fallback_block_count} needing translation review), "
                f"{len(leaders)} leaders"
            )

            if dry_run:
                done += 1
                continue

            with transaction.atomic():
                self._import_one(fac, merged, leaders)
            done += 1

        verb = "Would import" if dry_run else "Imported"
        self.stdout.write(self.style.SUCCESS(f"\n{verb} {done} faculty(ies)."))

    # -- leaders -----------------------------------------------------------

    @staticmethod
    def _align_leaders(leaders_by_lang: dict[str, list[dict]]) -> list[dict[str, dict]]:
        """uz is the spine (always present); each other language's leader
        with the same id fills in, or uz's own data stands in if a
        language is missing that leader entirely."""
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
        # "activity" (a list of duties) and "biography" (personal bio) are
        # separate HTML fields on the old site; StaffMember has one bio
        # field, so they're joined rather than adding a schema field for
        # what's a fairly minor secondary piece of content.
        parts = [html_to_plain_text(leader.get("activity")), html_to_plain_text(leader.get("biography"))]
        return "\n\n".join(p for p in parts if p)

    # -- import --------------------------------------------------------

    def _import_one(self, fac, merged, leaders: list[dict[str, dict]]) -> None:
        existing = Faculty.objects.filter(slug=fac.slug).first()
        if existing:
            page_id = existing.page_id
            existing.delete()
            Page.objects.filter(pk=page_id).delete()

        logo = self._images.get_or_download(fac.logo_url)
        # Page.slug is a separate, purely-internal join key -- never used
        # for URLs (Faculty.slug is) -- see import_legacy_departments.py
        # for why it's namespaced by content type + id rather than reusing
        # the public slug.
        page = Page.objects.create(slug=f"faculty-{fac.id}")
        faculty = Faculty.objects.create(
            slug=fac.slug,
            name_uz=fac.title["uz"],
            name_ru=fac.title["ru"] or fac.title["uz"],
            name_en=fac.title["en"] or fac.title["uz"],
            logo=logo,
            page=page,
        )

        order = 1
        for block in merged.blocks:
            data = {}
            skip_block = False
            for lang in LANGS:
                payload = dict(block.payload_by_lang[lang])
                if block.block_type == "image":
                    img = self._images.get_or_download(payload.pop("image_src", None))
                    if img is None:
                        skip_block = True
                        break
                    payload["image_id"] = img.id
                    payload.setdefault("alt", "")
                data[lang] = payload
            if skip_block:
                continue
            content_block = ContentBlock(page=page, order=order, block_type=block.block_type, data=data)
            content_block.full_clean()
            content_block.save()
            order += 1

        for index, row in enumerate(leaders):
            uz = row["uz"]
            photo = self._images.get_or_download(uz.get("photo"))
            StaffMember.objects.create(
                faculty=faculty,
                full_name=(uz.get("name") or "").strip(),
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
                # The old data has no explicit "is this the dean" flag; the
                # dean is consistently listed first, ahead of the vice-deans
                # -- confirmed across the faculties inspected before writing
                # this command.
                is_head=index == 0,
                order=index,
            )
