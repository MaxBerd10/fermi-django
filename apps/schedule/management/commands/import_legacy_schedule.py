"""
Imports the class-schedule spreadsheets (Course + ScheduleFile) from the old
site into Django.

Unlike every other legacy_import command, this one has no JSON API to fetch
from -- the old site's /schedule page (frontend/src/pages/schedule/page.tsx
in fjstiWeb-main) renders this exact course/specialty/file list as static
JSX, not from a backend call (confirmed: loading that page live makes zero
XHR/fetch requests). So the list below was scraped once from the live
rendered page and is hardcoded here, same as fjstiWeb-main itself hardcoded
it -- there is nothing else to poll.

Idempotent: re-running clears and rebuilds every Course/ScheduleFile row,
same as the other legacy importers.

Usage:
    python manage.py import_legacy_schedule --dry-run
    python manage.py import_legacy_schedule
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.legacy_import.media import DocumentDownloader
from apps.schedule.models import Course, ScheduleFile

_BASE = "https://api.fermi.uz"

# (uz, ru, en) titles for each specialty label as it appears on the old
# site's schedule page -- the same ~8 specialty names repeat across courses.
_SPECIALTY_TITLES: dict[str, tuple[str, str, str]] = {
    "Oliy hamshiralik ishi": ("Oliy hamshiralik ishi", "Высшее сестринское дело", "Higher Nursing"),
    "Biotibbiyot muahandisligi": ("Biotibbiyot muahandisligi", "Биомедицинская инженерия", "Biomedical Engineering"),
    "Tibbiy biologik ish": ("Tibbiy biologik ish", "Медико-биологическое дело", "Medical Biological Work"),
    "Tibbiy profilaktika ishi": ("Tibbiy profilaktika ishi", "Медицинская профилактика", "Medical Prevention Work"),
    "Davolash ishi": ("Davolash ishi", "Лечебное дело", "General Medicine"),
    "Farmatsiya": ("Farmatsiya", "Фармация", "Pharmacy"),
    "Pediatriya": ("Pediatriya", "Педиатрия", "Pediatrics"),
    "Stomatologiya": ("Stomatologiya", "Стоматология", "Dentistry"),
}

# course order -> [(specialty key, file URL), ...], in the old site's own
# on-page order.
_COURSES: list[tuple[int, tuple[str, str, str], list[tuple[str, str]]]] = [
    (1, ("1-kurs", "1-курс", "Year 1"), [
        ("Oliy hamshiralik ishi", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/OHI-1%20kurs.xlsx"),
        ("Biotibbiyot muahandisligi", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/BTM-1%20kurs.xlsx"),
        ("Tibbiy biologik ish", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/TBI-1%20kurs.xlsx"),
        ("Tibbiy profilaktika ishi", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/TPI-1kurs.xlsx"),
        ("Davolash ishi", f"{_BASE}/uploads/img/fakultet/Davolash%20ishi/Dars%20jadvali/Davolash%20ishi%201%20kurs%201-semestr%202-smena.xlsx"),
        ("Farmatsiya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Farmatsiya%201-%20kurs%201-%20semestr%2004.09.2024.xlsx"),
        ("Pediatriya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Pediatriya%201%20kurs%201%20semestr%2004.09.2024.xlsx"),
        ("Stomatologiya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Stomatologiya%20%20%201-%20kurs%201-semestr%2004.09.2024.xlsx"),
    ]),
    (2, ("2-kurs", "2-курс", "Year 2"), [
        ("Biotibbiyot muahandisligi", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/BTM-2kurs.xlsx"),
        ("Oliy hamshiralik ishi", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/OHI%202%20kurs%20ma%E2%80%98ruza.xlsx"),
        ("Tibbiy biologik ish", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/TBI%202%20kurs.xlsx"),
        ("Tibbiy profilaktika ishi", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/TPI-2kurs.xlsx"),
        ("Davolash ishi", f"{_BASE}/uploads/img/fakultet/Davolash%20ishi/Dars%20jadvali/Davolash%20ishi%202%20kurs%203-semestr%202-smena.xlsx"),
        ("Farmatsiya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Farmatsiya%202%20kurs%203-%20semestr%2004.09.2024.xlsx"),
        ("Pediatriya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Pediatriya%202%20kurs%203-%20semestr%20%2004.09.2024.xlsx"),
        ("Stomatologiya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Stomatologiya%20%20%202%20kurs%203-%20semestr%2004.09.2024.xlsx"),
    ]),
    (3, ("3-kurs", "3-курс", "Year 3"), [
        ("Oliy hamshiralik ishi", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/%D0%9EHI%203%20kurs%20ma%E2%80%98ruza.xlsx"),
        ("Tibbiy profilaktika ishi", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/TPI-3kurs.xlsx"),
        ("Davolash ishi", f"{_BASE}/uploads/img/fakultet/Davolash%20ishi/Dars%20jadvali/Davolash%20ishi%203%20kurs%205%20semestr.xlsx"),
        ("Farmatsiya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Farmatsiya%203%20kurs%205-%20semestr%2004.09.2024.xlsx"),
        ("Pediatriya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Pediatriya%203%20kurs%205-%20semestr%20%2004.09.2024.xlsx"),
        ("Stomatologiya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Stomatologiya%20%20%203%20kurs%205%20semestr%2004.09.2024.xlsx"),
    ]),
    (4, ("4-kurs", "4-курс", "Year 4"), [
        ("Tibbiy profilaktika ishi", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/TPI-4kurs%20ma%E2%80%98ruza.xlsx"),
        ("Davolash ishi", f"{_BASE}/uploads/img/fakultet/Davolash%20ishi/Dars%20jadvali/Davolash%20ishi%204%20kurs%207%20semestr%202-smena.xlsx"),
        ("Farmatsiya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Farmatsiya%204%20kurs%207-%20semestr%2004.09.2024.xlsx"),
        ("Pediatriya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Pediatriya%204%20kurs%207-%20semestr%2004.09.2024.xlsx"),
        ("Stomatologiya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Stomatologiya%20%204%20kurs%207%20semestr%2004.09.2024.xlsx"),
    ]),
    (5, ("5-kurs", "5-курс", "Year 5"), [
        ("Tibbiy profilaktika ishi", f"{_BASE}/uploads/img/fakultet/tibbbiy/DARS%20JADVALI/TPI-5kurs%20ma%E2%80%98ruza.xlsx"),
        ("Davolash ishi", f"{_BASE}/uploads/img/fakultet/Davolash%20ishi/Dars%20jadvali/Davolash%20ishi%205%20kurs%209%20semestr%201-smena.xlsx"),
        ("Farmatsiya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Farmatsiya%205%20kurs%209%20semestr%2004.09.2024.xlsx"),
        ("Stomatologiya", f"{_BASE}/uploads/img/fakultet/Pediatriya%20fakulteti/Dars%20jadvali/Stomatologiya%205-kurs%209-semestr%2004.09.2024.xlsx"),
    ]),
    (6, ("6-kurs", "6-курс", "Year 6"), [
        ("Davolash ishi", f"{_BASE}/uploads/img/fakultet/Davolash%20ishi/Dars%20jadvali/Davolash%20ishi%206%20kurs%2011%20semestr%201%20smena.xlsx"),
    ]),
]


class Command(BaseCommand):
    help = "Import the old site's class-schedule spreadsheets into Course/ScheduleFile."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch and report only -- writes nothing."
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        total_files = sum(len(files) for _, _, files in _COURSES)
        self.stdout.write(f"{len(_COURSES)} course(s), {total_files} schedule file(s) to process.\n")

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Would import {len(_COURSES)} course(s), {total_files} file(s)."))
            return

        documents = DocumentDownloader(
            allowed_extensions=("xlsx",),
            on_error=lambda src, exc: self.stderr.write(self.style.WARNING(f"    could not load {src[:100]}: {exc}")),
        )

        imported_files = 0
        with transaction.atomic():
            ScheduleFile.objects.all().delete()
            Course.objects.all().delete()

            for order, (title_uz, title_ru, title_en), files in _COURSES:
                course = Course.objects.create(
                    title_uz=title_uz, title_ru=title_ru, title_en=title_en, order=order
                )
                for file_order, (specialty, url) in enumerate(files, start=1):
                    document = documents.get_or_download(url)
                    if document is None:
                        continue
                    spec_uz, spec_ru, spec_en = _SPECIALTY_TITLES[specialty]
                    ScheduleFile.objects.create(
                        course=course,
                        document=document,
                        title_uz=spec_uz,
                        title_ru=spec_ru,
                        title_en=spec_en,
                        order=file_order,
                    )
                    imported_files += 1

        self.stdout.write(self.style.SUCCESS(f"\nImported {len(_COURSES)} course(s), {imported_files} schedule file(s)."))
