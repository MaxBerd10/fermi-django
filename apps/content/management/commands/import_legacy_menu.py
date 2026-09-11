"""
Imports the site navigation tree from the old site's live public API into
MenuItem.

The old menu mixes destinations the new site doesn't serve yet (standalone
CMS pages -- 70% of the tree by item count, a separate "leadership
directory" feature, raw Yii2 controller routes) with ones it does
(departments, faculties, the homepage). Every item's label and tree
position (parent/order) is migrated regardless, since the navigation's
structure and wording carry real information on their own -- only `url` is
left as a non-clickable "#" for a destination this site can't yet serve,
rather than either dropping the item or pointing it at a broken link.

Not idempotent per-item like the other importers (a nav tree has no
natural per-node identity worth preserving across runs) -- it just
replaces the whole tree each time, which is what you want while more
content types gain real destinations here over time.

Usage:
    python manage.py import_legacy_menu --dry-run
    python manage.py import_legacy_menu
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.legacy_import.fetch import LANGS, fetch_menu_tree
from apps.departments.models import Department
from apps.faculties.models import Faculty
from apps.menu.models import MenuItem


class Command(BaseCommand):
    help = "Import the site navigation tree from the old site's live API into MenuItem."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch and report only -- writes nothing."
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        trees = {lang: fetch_menu_tree(lang) for lang in LANGS}
        department_slugs = set(Department.objects.values_list("slug", flat=True))
        faculty_slugs = set(Faculty.objects.values_list("slug", flat=True))

        counts = {"total": 0, "resolved": 0}
        self._report(trees["uz"], counts)
        self.stdout.write(
            f"{counts['total']} menu item(s), {counts['resolved']} with a real destination "
            f"({counts['total'] - counts['resolved']} land on a page this site doesn't serve yet).\n"
        )

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry run -- nothing written."))
            return

        with transaction.atomic():
            MenuItem.objects.all().delete()
            for index, node_by_lang in enumerate(zip(trees["uz"], trees["ru"], trees["en"])):
                self._create_node(dict(zip(LANGS, node_by_lang)), parent=None, order=index,
                                   department_slugs=department_slugs, faculty_slugs=faculty_slugs)

        self.stdout.write(self.style.SUCCESS(f"Imported {counts['total']} menu item(s)."))

    # -- reporting -------------------------------------------------------

    def _report(self, uz_nodes: list[dict], counts: dict) -> None:
        for node in uz_nodes:
            counts["total"] += 1
            if node["urlType"] in ("main",) or self._resolvable(node):
                counts["resolved"] += 1
            self._report(node["children"], counts)

    @staticmethod
    def _resolvable(node: dict) -> bool:
        return node["urlType"] in ("departments", "faculty")

    # -- url resolution ----------------------------------------------------

    @staticmethod
    def _resolve_url(node: dict, department_slugs: set[str], faculty_slugs: set[str]) -> str:
        url_type = node["urlType"]
        value = node["urlValue"]
        if url_type == "main":
            return "/"
        if url_type == "departments" and value in department_slugs:
            return f"/kafedralar/{value}"
        if url_type == "faculty" and value in faculty_slugs:
            return f"/fakultetlar/{value}"
        # page / leader / c-action / category / other / "" -- no matching
        # route on this site yet.
        return "#"

    # -- import ------------------------------------------------------------

    def _create_node(
        self,
        node_by_lang: dict[str, dict],
        parent: MenuItem | None,
        order: int,
        department_slugs: set[str],
        faculty_slugs: set[str],
    ) -> None:
        uz_node = node_by_lang["uz"]
        item = MenuItem.objects.create(
            parent=parent,
            label_uz=uz_node["title"],
            label_ru=node_by_lang["ru"]["title"] or uz_node["title"],
            label_en=node_by_lang["en"]["title"] or uz_node["title"],
            url=self._resolve_url(uz_node, department_slugs, faculty_slugs),
            order=order,
        )
        children = zip(uz_node["children"], node_by_lang["ru"]["children"], node_by_lang["en"]["children"])
        for index, child_by_lang in enumerate(children):
            self._create_node(
                dict(zip(LANGS, child_by_lang)), parent=item, order=index,
                department_slugs=department_slugs, faculty_slugs=faculty_slugs,
            )
