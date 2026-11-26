"""Builds plan.json from the database AFTER scripts 39-76 (read-only):
    python manage.py shell < deploy/content/yillik-hisobot-2026-77/make_plan.py
titles_en.json: for each of the 157 articles of the journal archives its Russian title (as it stands in the page) and the English title."""
import json
from pathlib import Path

from apps.content.models import ContentBlock

HERE = Path("deploy/content/yillik-hisobot-2026-77")
rows = json.loads((HERE / "titles_en.json").read_text(encoding="utf8"))
entries = []
for row in rows:
    block = ContentBlock.objects.get(page__slug=row["slug"], order=row["order"], block_type="document")
    ru, en = block.data["ru"]["caption"], block.data["en"]["caption"]
    assert ru == row["ru"], (row["slug"], row["order"], "the Russian title differs from the one that was translated")
    assert en == ru, (row["slug"], row["order"], "the English caption is not the Russian one any more")
    entries.append({"slug": row["slug"], "order": row["order"], "old": en, "new": row["en"]})
(HERE / "plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=0), encoding="utf8")
print(len(entries), "captions")
