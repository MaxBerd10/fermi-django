# deploy/content — one-off content scripts

Every folder here changed the **data** of the site once (pages, menu, news, media). They are history now: all of them
have been applied on the server. They stay in the repository because each one can still be **undone** and each one
explains what was changed and why. Do not move or rename a folder: a script finds its `plan.json` by its own name, and
its backup file (`/var/backups/fermi-django/<name>.json`) is named after it too.

## How a script runs (all of them, the same way)

```bash
cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/<name>/apply.py   # writes nothing
MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/<name>/apply.py   # one transaction + backup
MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/<name>/apply.py   # puts the old data back
```

* Run as `www-data` (never as root): the site runs as `www-data`, a root-owned file under `media/` breaks uploads.
* A second `apply` is refused while the backup exists; `undo` renames the backup, so the script can be applied again.
* A script changes a block only if it still is exactly what the plan was made from (fingerprints); otherwise the
  block is listed as `SKIPPED` and left alone.

## What is here

| Folder | What it did |
|---|---|
| `yillik-hisobot-2026-36 … -38` | first drafts of the text pages of "Institut haqida" (replaced by 41) |
| `yillik-hisobot-2026-39 … -71` | **the conversion**: every page of every menu from old HTML to typed blocks (heading, paragraph, list, table, image, gallery, document, video), the same structure in uz / ru / en. Apply in numeric order. 72 is a separate one-line menu fix |
| `yillik-hisobot-2026-72` | the Russian menu label "Научно-исследовательские работы…" |
| `yillik-hisobot-2026` | the annual report pages (plans, evidence, drafts) |
| `homoglyph-*`, `uzbek-apostrophes-2026-11-18`, `en-content-fixes-*`, `kongress-text-fixes-*`, `institut-haqida-translation-fixes` | text clean-ups (look-alike letters, the single Uzbek apostrophe `ʻ`, English/Russian fixes) |
| `news-*`, `doc-*`, `archive-*`, `menu-*`, `monografiya-2025`, `korrupsiya-video`, `institut-tarixi-image-fixes` | single news items, documents, menu entries, media |

## Tools (files starting with `_`)

Used only to **make** a plan, never at the server:

* `_html_to_blocks.py` — old HTML → blocks; `_auto_plan.py`, `_auto_pages.py` — the generic converter;
* `_align.py`, `_merge3.py`, `_manual_pages.py` — hand-alignment of pages whose three languages differ in structure
  (keys of a `translations.json`: `slug|row|lang`, `slug|blocks`, `slug|order|lang`, `|drop_notes`, `|uz_only`, `|join`);
* `_plan_tools.py`, `_report_images.py` — helpers.

Rules that cost time before:

* `yillik-hisobot-2026-63/make_plan.py` must **not** be run again: its row numbers no longer match the converter. Edit `plan.json` directly.
* Uzbek text in a plan uses only `ʻ` (U+02BB) as the apostrophe.
* Texts that were translated by hand are listed in each folder's `tarjima-kerak.md`: a native reader must check them.

The shared library is `apps/content/migration_tools.py` (dry / apply / undo skeleton, fingerprints, backup, image helpers).
The picture-weight tool is `deploy/optimize_images.py` (same dry / apply / undo idea).
