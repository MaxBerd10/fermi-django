"""
Imports the site navigation tree from the old site's live public API into
MenuItem.

Every item's label and tree position (parent/order) is migrated regardless
of whether this site can serve its destination yet -- the navigation's
structure and wording carry real information on their own. `url` points at
a real route when one exists for that item's urlType (departments/faculty/
leader/page/category/gallery/video/virtual-reception), and falls back to a
non-clickable "#" only for the handful of destinations genuinely not built
yet (documents, search, schedule, sitemap -- see each app's own TODO).

The route's :menuId param is the item's own parent id -- on the frontend,
resolveMenuSection(menu, menuId, slug) looks that id up and lists ITS
children as the sidebar, so this makes "my siblings under the same parent"
the sidebar for every page, not just the ~50 specifically hand-configured
sections in lib/menuSection.ts (those still get a nicer theme/intro; every
other page still gets a correct, generic sidebar instead of none).

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
from apps.content.models import Page
from apps.departments.models import Department
from apps.faculties.models import Faculty
from apps.menu.models import MenuItem
from apps.news.models import NewsCategory

# c-action is the old site's shorthand for a fixed feature page rather than
# CMS content.
_C_ACTION_ROUTES = {
    "site/gallery": "/galereya",
    "site/video": "/video",
    "site/virtual-reception": "/virtual-qabulxona",
}

# One menu category slug doesn't match its own posts' real category slug on
# the old site itself -- same mismatch the frontend already works around
# (see frontend/src/lib/newsImages.ts::NEWS_CATEGORY_SLUG_ALIASES). Kept
# here too only so _resolvable's report count reflects reality; the route
# itself doesn't need the alias since the frontend normalizes it again
# before querying.
_CATEGORY_SLUG_ALIASES = {
    "yoshlar-ittifoqi-tomonidan-otkazilgan-tadbirlar": "yoshlar-ittifoqi-tadbirlari",
}


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
        page_slugs = set(Page.objects.values_list("slug", flat=True))
        category_slugs = set(NewsCategory.objects.values_list("slug", flat=True))

        counts = {"total": 0, "resolved": 0}
        self._report(trees["uz"], counts, department_slugs, faculty_slugs, page_slugs, category_slugs)
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
                self._create_node(
                    dict(zip(LANGS, node_by_lang)), parent=None, order=index,
                    department_slugs=department_slugs, faculty_slugs=faculty_slugs, page_slugs=page_slugs,
                    category_slugs=category_slugs,
                )

        actual = MenuItem.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f"Imported {actual} menu item(s) ({counts['total'] - actual} pruned as dead+childless).")
        )

    # -- reporting -------------------------------------------------------

    def _report(self, uz_nodes, counts, department_slugs, faculty_slugs, page_slugs, category_slugs) -> None:
        for node in uz_nodes:
            counts["total"] += 1
            if self._resolvable(node, department_slugs, faculty_slugs, page_slugs, category_slugs):
                counts["resolved"] += 1
            self._report(node["children"], counts, department_slugs, faculty_slugs, page_slugs, category_slugs)

    @staticmethod
    def _resolvable(node, department_slugs, faculty_slugs, page_slugs, category_slugs) -> bool:
        url_type, value = node["urlType"], node["urlValue"]
        if url_type == "main":
            return True
        if url_type == "departments":
            return value in department_slugs
        if url_type == "faculty":
            return value in faculty_slugs
        if url_type == "page":
            return value in page_slugs
        if url_type == "leader":
            return bool(value)
        if url_type == "c-action":
            return value in _C_ACTION_ROUTES
        if url_type == "category":
            return _CATEGORY_SLUG_ALIASES.get(value, value) in category_slugs
        return False

    # -- url resolution ----------------------------------------------------

    @staticmethod
    def _resolve_url(node: dict, section_menu_id: int, department_slugs: set[str], faculty_slugs: set[str],
                      page_slugs: set[str], category_slugs: set[str]) -> str:
        url_type = node["urlType"]
        value = node["urlValue"]
        if url_type == "main":
            return "/"
        if url_type == "departments" and value in department_slugs:
            return f"/departments/{section_menu_id}/{value}"
        if url_type == "faculty" and value in faculty_slugs:
            return f"/faculty/{section_menu_id}/{value}"
        if url_type == "leader" and value:
            return f"/leader/{section_menu_id}/{value}"
        if url_type == "page" and value in page_slugs:
            return f"/blog/{section_menu_id}/{value}"
        if url_type == "c-action" and value in _C_ACTION_ROUTES:
            return _C_ACTION_ROUTES[value]
        if url_type == "category" and _CATEGORY_SLUG_ALIASES.get(value, value) in category_slugs:
            return f"/news/{section_menu_id}/{value}"
        # documents / other / "" -- no matching route (documents: no list
        # endpoint yet; other/"": the old site's own dead-end dropdown
        # headers) -- see apps.documents' own TODO rather than guessing at
        # a destination here.
        return "#"

    # -- import ------------------------------------------------------------

    def _create_node(
        self,
        node_by_lang: dict[str, dict],
        parent: MenuItem | None,
        order: int,
        department_slugs: set[str],
        faculty_slugs: set[str],
        page_slugs: set[str],
        category_slugs: set[str],
    ) -> None:
        uz_node = node_by_lang["uz"]
        # A node's own id doubles as the :menuId every one of ITS children's
        # routes carry -- see the module docstring for why (children become
        # each other's sidebar).
        section_menu_id = parent.id if parent is not None else None
        url = self._resolve_url(
            uz_node, section_menu_id if section_menu_id is not None else 0,
            department_slugs, faculty_slugs, page_slugs, category_slugs,
        )
        # A node with no real destination is still worth keeping when it has
        # real children (the same "non-clickable group header" shape as
        # "Institut"/"Tuzilma" etc.) -- but with NEITHER a destination NOR
        # children, it's pure dead weight (a handful of items are like this
        # even on the old site itself, e.g. a menu entry for a page that 404s
        # there too), so it's dropped rather than rendered as an inert link.
        if url == "#" and not uz_node["children"]:
            return
        item = MenuItem.objects.create(
            parent=parent,
            label_uz=uz_node["title"],
            label_ru=node_by_lang["ru"]["title"] or uz_node["title"],
            label_en=node_by_lang["en"]["title"] or uz_node["title"],
            url=url,
            order=order,
        )
        children = zip(uz_node["children"], node_by_lang["ru"]["children"], node_by_lang["en"]["children"])
        for index, child_by_lang in enumerate(children):
            self._create_node(
                dict(zip(LANGS, child_by_lang)), parent=item, order=index,
                department_slugs=department_slugs, faculty_slugs=faculty_slugs, page_slugs=page_slugs,
                category_slugs=category_slugs,
            )
