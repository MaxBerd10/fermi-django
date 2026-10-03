"""Read-only: lists the Cyrillic that fix_uz_script leaves behind in Uzbek (`uz`) slots, with enough
context (record id, owner, admin link, a snippet) for a person to decide what each one should be.

    rus     -- the text is (almost) entirely Cyrillic with no Uzbek-only letters: Russian prose sitting in the uz slot
    aralash -- Latin Uzbek text with a Cyrillic phrase inside it (often a quoted Russian title)
    uzun    -- Cyrillic Uzbek whose Latin spelling would not fit the column (cut it down, then save in the admin)

    .venv/bin/python manage.py list_uz_leftovers
"""
import re
from collections import defaultdict

from django.core.management.base import BaseCommand

from apps.admin_api.uz_script import has_cyrillic, repair
from apps.content.models import ContentBlock
from apps.departments.models import StaffMember
from apps.menu.models import MenuItem
from apps.news.models import NewsPost

_CYR_RUN_RE = re.compile(r"[Ѐ-ӿ][Ѐ-ӿ\s.,;:!?«»“”\"'()-]*")


def _classify(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    cyr = sum(1 for c in letters if has_cyrillic(c))
    return "rus" if cyr * 4 >= len(letters) * 3 else "aralash"


def _snippet(text: str, width: int = 70) -> str:
    match = _CYR_RUN_RE.search(text)
    start = match.start() if match else 0
    return re.sub(r"\s+", " ", text[start:start + width]).strip()


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


class Command(BaseCommand):
    help = "Read-only list of Cyrillic left in Uzbek slots after fix_uz_script."

    def handle(self, *args, **options):
        self.stdout.write("== NEWS (admin: /admin/news/<id>) ==")
        for post in NewsPost.objects.order_by("id"):
            for field, limit in (("title_uz", 255), ("excerpt_uz", 500)):
                text = getattr(post, field) or ""
                if not has_cyrillic(text):
                    continue
                new, kind = repair(text)
                if kind == "leave":
                    label = _classify(text)
                elif len(new) > limit:
                    label = "uzun"
                else:
                    continue
                self.stdout.write(f"news {post.id} {field} [{label}] {post.slug[:45]} :: {_snippet(text)}")

        self.stdout.write("\n== STAFF (admin: Rahbariyat / kafedra xodimlari) ==")
        for member in StaffMember.objects.order_by("id"):
            for field in ("full_name_uz", "bio_uz", "activity_uz"):
                text = getattr(member, field) or ""
                if has_cyrillic(text) and repair(text)[1] == "leave":
                    self.stdout.write(f"staff {member.id} {field} [{_classify(text)}] {member.full_name_uz[:30]} :: {_snippet(text)}")

        self.stdout.write("\n== MENU ==")
        for item in MenuItem.objects.order_by("id"):
            if has_cyrillic(item.label_uz) and repair(item.label_uz)[1] == "leave":
                self.stdout.write(f"menu {item.id} label_uz [{_classify(item.label_uz)}] :: {_snippet(item.label_uz)}")

        self.stdout.write("\n== PAGE BLOCKS (admin: /admin/pages/<page id>), grouped by page ==")
        per_page = defaultdict(list)
        for block in ContentBlock.objects.select_related("page").order_by("page_id", "order"):
            text = " ".join(_strings((block.data or {}).get("uz")))
            if has_cyrillic(text):
                new, kind = repair(text)
                if kind == "leave" or has_cyrillic(new):
                    per_page[(block.page_id, block.page.slug)].append((block.id, _classify(text), _snippet(text, 55)))
        for (page_id, slug), items in per_page.items():
            kinds = sorted({k for _, k, _ in items})
            self.stdout.write(f"page {page_id} {slug[:50]}: {len(items)} blok {kinds} :: {items[0][2]}")
        self.stdout.write(f"\n({sum(len(v) for v in per_page.values())} blocks on {len(per_page)} pages)")
