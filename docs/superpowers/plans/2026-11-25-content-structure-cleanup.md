# "Institut haqida" content cleanup: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** All 25 pages of "Institut haqida" are typed blocks with pictures in the media library, drawn by one tested layout engine, with the per-page code deleted.

**Architecture:** A pure function `layoutBlocks` reads block types and order and returns sections; `ArticleBody` draws them; `blog/page.tsx` uses it for every typed page. Content moves from `raw_html`, translation files and repository images into `ContentBlock` and `Image` rows through dry/apply/undo scripts built on one shared toolkit (`apps/content/migration_tools.py`). Each task leaves the site working.

**Tech Stack:** React 18 + TypeScript + Vite (frontend, add `vitest`), Django 6 + pytest (backend), `manage.py shell < apply.py` content scripts.

**Spec:** `docs/superpowers/specs/2026-11-25-content-structure-cleanup-design.md`

## Global Constraints

- Scripts run as `MODE=dry|apply|undo .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-NN/apply.py`: dry is the default and writes nothing; apply is one transaction, saves a backup to `/var/backups/fermi-django/<name>.json`, is refused a second time, and skips (and lists) a block whose payload no longer matches the fingerprint in `plan.json`; undo restores only blocks still holding what the script wrote.
- Script numbers 39-44 are used by this plan. Scripts 36, 37, 38 are NOT applied on the server; script 41 reads their `plan.json` files and supersedes them.
- Uzbek text uses one apostrophe, U+02BB (`ʻ`). No Latin/Cyrillic mixed words in Russian text.
- A script run as root leaves every created file and folder owned by `www-data`.
- Only fermi files and rows are touched on the shared server.
- Nothing is pushed, deployed or applied on the server until the user says so.
- `npm run type-check`, `npm run lint`, `npm test` and `pytest` pass; no console error; Lighthouse is checked on the production build, never in dev mode.
- Layout rules never read the slug and never read the language of a text.

## Review Focus

1. A block edited in the admin after the plan was made: the script skips it and says so (pinned in Task 3).
2. Pictures before the first heading, or a section with many pictures and almost no text: drawn as a row, never an empty side column (Task 1).
3. The same page in a language whose text is three times longer: same sections and same side/row choice (Task 1).
4. An `image` block whose `image` is null (file gone): skipped, no console error, no empty box (Task 1, Task 2).
5. A page that mixes typed blocks and a `raw_html` block, and an empty page: nothing crashes, the `raw_html` block is drawn as before (Task 1, Task 2).

## File Structure

Frontend
- `frontend/src/lib/layoutBlocks.ts` (+ `layoutBlocks.test.ts`): the engine, pure, no React.
- `frontend/src/components/shared/ArticleBody.tsx`: draws `Section[]`.
- `frontend/src/pages/blog/page.tsx`: uses `ArticleBody`; loses `isMissionPage`, `isInstituteAboutPage`, `isAnnualReportPage`, `ANNUAL_REPORT_SLUGS`.
- `frontend/src/styles/inner-page.css`: `annual-*` classes renamed `article-*`; regulations/mission/usmle-specific rules replaced by generic heading and list rules.
- Deleted by the end: `components/shared/AnnualReportArticle.tsx`, `InstituteHistoryArticle.tsx`, `lib/instituteHistoryImages.ts`, the builders and slug branches for these pages in `lib/enhanceCmsHtml.ts`, the `institut.*` keys of the three `i18n/local/*/common.ts`.

Backend
- `apps/content/migration_tools.py` (+ `apps/content/test_migration_tools.py`): shared toolkit for the scripts.
- `deploy/content/yillik-hisobot-2026-39 ... -44/{plan.json,apply.py}`.
- `scripts/audit_section.py`: the rerunnable audit (structure, language, links).

---

### Task 1: Test tooling and the layout engine

**Files:**
- Modify: `frontend/package.json` (dev dependency `vitest`, script `"test": "vitest run"`)
- Create: `frontend/src/lib/layoutBlocks.ts`, `frontend/src/lib/layoutBlocks.test.ts`

**Interfaces:**
- Produces:
  ```ts
  export type Picture = { src: string; alt: string; width: number | null; height: number | null; tall: boolean };
  export type Section =
    | { kind: "opening"; text: ContentBlock; picture: Picture }
    | { kind: "quote"; text: ContentBlock; picture: Picture }
    | { kind: "person"; heading: ContentBlock; picture: Picture; text: ContentBlock[] }
    | { kind: "section"; blocks: ContentBlock[]; pictures: Picture[]; side: boolean }
    | { kind: "footer"; source: ContentBlock; slogan: ContentBlock; contact: ContentBlock }
    | { kind: "block"; block: ContentBlock };
  export function picturesOf(block: ContentBlock): Picture[]; // image block, unstyled gallery block, legacy image-only raw_html
  export function layoutBlocks(blocks: ContentBlock[]): Section[];
  export const LINES_PER_SIDE_PICTURE = 5.5;
  ```
  Weights (never characters): heading 2, paragraph 3, list 3 per item, table 1.8 per row + 1. A section is `side` when its weight >= pictures × `LINES_PER_SIDE_PICTURE`.

- [ ] **Step 1: Add vitest and the `test` script; run `npm test`** Expected: "No test files found" (exit 1 is fine here).
- [ ] **Step 2: Write the failing tests** in `layoutBlocks.test.ts` (fixtures built with small helpers `p(text)`, `h(text, level)`, `img(file, w, h)`, `list(n)`, `table(rows)`):
  - `opening: first paragraph followed by an image`: `layoutBlocks([p("a"), img("x", 960, 640), h("H", 2)])[0].kind === "opening"`.
  - `quote needs « » or " "`: `[p("«Words» — Name"), img]` gives `quote`; `[p("plain"), img]` gives a `section`/`block`, not `quote`.
  - `person: level-3 heading, image, paragraphs`: kind `person` with `text.length === 2`.
  - `section with long text puts pictures beside it`: heading + list(4) + 4 images, `side === true`; heading + paragraph + 3 images, `side === false`.
  - `layout does not change with text length`: the same blocks with every text tripled give the same `kind`/`side` sequence.
  - `pictures before the first heading are a row, not a side column`: `side === false`.
  - `exactly three trailing paragraphs after the last list or table are the footer`; two are not.
  - `image with image: null is ignored`: no throw, no picture.
  - `raw_html text block and an empty page`: `kind: "block"`; `layoutBlocks([])` is `[]`.
  - `tall picture`: `img("x", 540, 690)` has `tall === true`.
- [ ] **Step 3: Run `npm test`** Expected: FAIL (module missing).
- [ ] **Step 4: Implement `layoutBlocks` and `picturesOf`.** Rules in the spec's order; consecutive image blocks of a section form one picture group; legacy image-only `raw_html` is read through `picturesOf` (deleted in Task 10).
- [ ] **Step 5: Run `npm test`, `npm run type-check`, `npm run lint`** Expected: all pass.
- [ ] **Step 6: Commit** `git add frontend/package.json frontend/package-lock.json frontend/src/lib/layoutBlocks*.ts && git commit -m "feat: layout engine reads block types and order, with tests"`

### Task 2: `ArticleBody` renderer; the report pages move to it

**Files:**
- Create: `frontend/src/components/shared/ArticleBody.tsx`
- Modify: `frontend/src/pages/blog/page.tsx`, `frontend/src/styles/inner-page.css`
- Delete: `frontend/src/components/shared/AnnualReportArticle.tsx`

**Interfaces:**
- Consumes: `layoutBlocks`, `Section`, `Picture` (Task 1).
- Produces: `export default function ArticleBody({ blocks }: { blocks: ContentBlock[] }): JSX.Element`; CSS classes `article-hero`, `article-quote`, `article-person`, `article-split`, `article-aside`, `article-row`, `article-footer-*` (the existing `annual-*` rules renamed).

- [ ] **Step 1: Implement `ArticleBody`** drawing every `Section` kind; `block` sections go through `BlockRenderer` (so `raw_html`, documents, tables, lists keep their drawing); a picture whose file fails to load is hidden (`onError`), no console error.
- [ ] **Step 2: In `blog/page.tsx` use `ArticleBody` for every page that has blocks**, delete `isAnnualReportPage`, `ANNUAL_REPORT_SLUGS` and the import of `AnnualReportArticle`; keep `isMissionPage`/`isInstituteAboutPage` until Tasks 5-6.
- [ ] **Step 3: Rename `annual-*` to `article-*` in `inner-page.css`; delete `AnnualReportArticle.tsx`.**
- [ ] **Step 4: Verify** `npm run type-check && npm run lint && npm test`. Then, in the browser at 1400px, for `yillik-hisobot-2026`, `ilmiy-va-innovatsion-faoliyat`, `moliya-oquv-uslubiy-ishlar-va-raqamlashtirish`: same look as before this task (hero, quote cards, rector portrait, side pictures, footer); `read_console_messages` shows no error. Open 5 typed pages outside this section (pick from `scripts` list of slugs with no `raw_html`) and note any change in the commit message.
- [ ] **Step 5: Commit** `refactor: one ArticleBody for every typed page, AnnualReportArticle removed`

### Task 3: Migration toolkit

**Files:**
- Create: `apps/content/migration_tools.py`, `apps/content/test_migration_tools.py`

**Interfaces:**
- Produces:
  ```python
  def sha(payload) -> str
  def make_image(path: str, alt_text: str = "") -> Image                    # from a local file; sets width/height; chown to www-data when root
  def replace_block(page: Page, order: int, new_blocks: list[dict]) -> list[int]
      # deletes the block at `order`, inserts new_blocks ({"block_type", "data"}) there, shifts later orders up; returns the new pks
  class Backup:  # JSON file in BACKUP_DIR
      def __init__(self, name: str): ...
      def exists(self) -> bool
      def save(self, **rows) -> None
      def load(self) -> dict
      def retire(self) -> None                                              # renames to .undone-<timestamp>
  def fingerprint_ok(block: ContentBlock, expected: dict[str, str]) -> bool # per-language sha of block.data[lang]
  def run_modes(name: str, build, undo) -> None                             # dry / apply / undo skeleton used by every script
  ```

- [ ] **Step 1: Write the failing tests** (pytest, `@pytest.mark.django_db`):
  - `test_replace_block_shifts_later_orders`: a page with orders 1..4, replace order 2 with 3 blocks → orders 1,2,3,4,5,6 with no `unique_block_order_per_page` violation, content order preserved.
  - `test_fingerprint_ok_detects_admin_edit`: after changing `data["ru"]`, `fingerprint_ok` is False.
  - `test_backup_second_apply_is_refused`: `Backup.exists()` True after `save`; `retire()` makes it False.
  - `test_typed_structure_survives_the_admin_editor`: a page built with `heading` level 2 and 3, `paragraph`, `list`, and two consecutive `image` blocks passes through `blocks_to_html` then `write_blocks_from_html` (from `apps/content/admin_content.py`) for all three languages and the blocks are equal afterwards (same types, levels, image ids, texts).
- [ ] **Step 2: Run `pytest apps/content/test_migration_tools.py -v`** Expected: FAIL.
- [ ] **Step 3: Implement the toolkit** following the existing script pattern (`deploy/content/yillik-hisobot-2026-36/apply.py`: plan.json, `MODE`, backup, one `transaction.atomic()`); `make_image` follows `deploy/content/korrupsiya-video/apply.py`.
- [ ] **Step 4: Run the tests** Expected: PASS.
- [ ] **Step 5: Commit** `feat: migration toolkit for content scripts, with tests`

### Task 4: Media library and the report pages (script 39)

**Files:**
- Create: `deploy/content/yillik-hisobot-2026-39/{plan.json,apply.py}`, `deploy/content/_report_images.py` (builds the plan: reads each `raw_html` image block of the 9 report pages)
- No frontend change: the engine already reads `image` blocks.

**Interfaces:**
- Consumes: `migration_tools.run_modes`, `make_image`, `replace_block`, `fingerprint_ok`.
- Produces: for each of the 9 report pages every `<img src="/images/hisobot/...">` of a `raw_html` block becomes one `image` block (consecutive images stay consecutive; `data[lang] = {"image_id": N, "alt": <that language's alt>}`), the 98 files from `frontend/public/images/hisobot/` become `Image` rows (alt text from the uz alt).

- [ ] **Step 1: Build `plan.json`** (one entry per page: block order, `image` list `(file, alt_uz, alt_ru, alt_en)`, fingerprints); print the count: expect 9 pages and the same number of pictures as `grep -c "<img" ` over the 9 pages' blocks.
- [ ] **Step 2: Write `apply.py`** using the toolkit; `dry` prints per page "N pictures -> N image blocks".
- [ ] **Step 3: Test on the scratch database** (`runtest.sh 39` harness: seed from the live API, dry, apply, second apply refused, undo, hash equal to before).
- [ ] **Step 4: Render check**: with the converted blocks served by the local proxy for the 9 slugs, `layoutBlocks` output has the same section kinds as before (record kinds per page before and after; they must match); type-check/lint/test pass.
- [ ] **Step 5: Commit** `content: report photos move to the media library as image blocks (script 39)`

### Task 5: Institut xaqida (script 40)

**Files:**
- Create: `deploy/content/yillik-hisobot-2026-40/{plan.json,apply.py}`
- Modify: `frontend/src/pages/blog/page.tsx` (remove the `isInstituteAboutPage` branch and `documentTitle`), `frontend/src/lib/enhanceCmsHtml.ts` (remove `buildAboutHeroLayout` and its slug branch), `frontend/src/i18n/local/{uz,ru,en}/common.ts` (remove `institut.fullName`, `institut.aboutParagraph1`, `institut.aboutParagraph2`, `institut.ecaqaDocument`)

**Interfaces:**
- Produces: page `institut-xaqida` = `paragraph` (the two texts of `institut.aboutParagraph1/2`, one block each, three languages), one `image` block (the photo `frontend/public/images/institut-about.jpg` as an `Image` row), and the existing ECAQA `document` block, now with `data[lang].caption` = the old `institut.ecaqaDocument` text.

- [ ] **Step 1: Build `plan.json` from the three `common.ts` files** (read the strings, not retype them); the heading text is `institut.fullName`.
- [ ] **Step 2: Write `apply.py`** (replace the dead `raw_html` block by heading, paragraph, paragraph, image; set the document caption).
- [ ] **Step 3: Scratch-database test** as in Task 4.
- [ ] **Step 4: Remove the code and the four i18n keys; in the browser the page shows the heading, both paragraphs, the photo and the ECAQA card in uz, ru, en**; editing a paragraph in the admin changes the site (check on the scratch data).
- [ ] **Step 5: `npm run type-check && npm run lint && npm test`, then commit** `content: Institut xaqida moves to the database, its special code removed (script 40)`

### Task 6: The four text pages (script 41)

**Files:**
- Create: `deploy/content/yillik-hisobot-2026-41/{plan.json,apply.py}`, `deploy/content/_html_to_blocks.py` (builds the typed blocks)
- Modify: `frontend/src/lib/enhanceCmsHtml.ts` (remove `buildUsmleLayout`, `buildRegulationsLayout`, `buildEthicsCodeLayout`, mission and regulations branches, their entries in `getCmsArticleModifier` and `TEXT_LAYOUT_SLUGS`), `frontend/src/pages/blog/page.tsx` (remove `isMissionPage`), `frontend/src/styles/inner-page.css` (generic heading rules replace the regulations/usmle/mission rules)

**Interfaces:**
- Consumes: the `plan.json` files of scripts 36, 37, 38 (their `set.html` per language), the live HTML of `ichki-tartib-qoidalar`.
- Produces: pages `institut-missiyasi-va-kelajak-tasavvuri`, `usmle-dasturi`, `ichki-tartib-qoidalar`, `institut-odob-axloq-kodeksi` as `heading` (level 2 = section/chapter, level 3 = article), `paragraph`, `list` blocks, **the same block types and counts in uz, ru and en**; USMLE English leftovers ("Step 3[edit]", "Main article", Wikipedia links) are dropped; the Kodeks keeps its `document` block; Ichki tartib keeps all its existing text (rules fragment, the first two articles of the Code, its PDF link as a `document` block if one exists, else the text only).
- Generic styles: `h2` plain bold with the thin yellow line between sections; `h3` bold navy with the small yellow mark (the look of the regulations articles, now for every page).

- [ ] **Step 1: `_html_to_blocks.build(html_by_lang) -> list[dict]`** with a test (`apps/content/test_migration_tools.py::test_html_to_blocks_same_structure_in_three_languages`): the uz/ru/en results have equal `block_type` sequences, heading levels and list lengths for the Missiya plan.
- [ ] **Step 2: Build `plan.json`** (one entry per page: new blocks, fingerprint of the old block); for Ichki tartib the block list is written out by hand in the script (about 15 units) because uz and ru/en lines differ.
- [ ] **Step 3: `apply.py` and the scratch-database test** as in Task 4.
- [ ] **Step 4: Remove the code listed above; browser check at 1400px** of the four pages in uz, ru, en: headings, lists as cards, Kodeks 10 chapters and 35 articles, no console error; `scripts/audit_section.py` (Task 10) shows no structure or language problem for them.
- [ ] **Step 5: type-check, lint, tests; commit** `content: Missiya, USMLE, Ichki tartib and Kodeks become typed blocks in three languages (script 41)`

### Task 7: Image-only pages (script 42)

**Files:**
- Create: `deploy/content/yillik-hisobot-2026-42/{plan.json,apply.py}`

**Interfaces:**
- Produces: pages `lavozim-yoriqnomasi`, `kredit-modul-nizomi`, `institut-test-markazi-nizomi`, `talabalar-kengashi-nizomi`, `institut-talim-yonalishlari-va-imkoniyatlari`, `ecaqa-xalqaro-maxsus-akkreditatsiya`: each `raw_html` picture block becomes `image` blocks (the two booklet pictures of "ta'lim yo'nalishlari" stay two consecutive `image` blocks; the stray "v" and the extra `<hr>` of the ru HTML disappear); the picture files come from `/home/fermi-django/media/migrated/...` through `make_image`.

- [ ] **Step 1: Build the plan from the live HTML; assert every referenced file exists on the source path (dry reports a missing file and stops).**
- [ ] **Step 2: `apply.py` and the scratch-database test.**
- [ ] **Step 3: Browser check of the six pages in three languages (picture + document card as before).**
- [ ] **Step 4: Commit** `content: image-only pages become image blocks (script 42)`

### Task 8: Institut tarixi (script 43) and the history code

**Files:**
- Create: `deploy/content/yillik-hisobot-2026-43/{plan.json,apply.py}`
- Modify: `frontend/src/lib/layoutBlocks.ts` and its test (rule: a `list` whose every item has a year before a dash is a `dated` list), `frontend/src/components/shared/ArticleBody.tsx`, `frontend/src/components/shared/DepartmentPageContent.tsx`, `frontend/src/pages/blog/page.tsx`
- Delete: `frontend/src/components/shared/InstituteHistoryArticle.tsx`, `frontend/src/lib/instituteHistoryImages.ts`

**Interfaces:**
- Produces: the history blocks reordered to `heading` level 3 (the person's name), `image` (the portrait, new `Image` row from `frontend/public/images/institute-history/*.webp`), `paragraph`s per person; the first list split into a prose list and a dated list; section labels ("Rivojlanish bosqichlari", "Tarix sahifasi", "Xalqaro hamkorlik", "O'quv va ilmiy yo'nalishlar rahbarlari") as `heading` level 2. `Section` gets `{ kind: "dated"; block: ContentBlock }`.

- [ ] **Step 1: Failing test** `dated list: every item has a year before a dash` (`["1992–1997 — A", "2021 yildan — B", "с 2021 года — C", "since 2021 — D"]` is dated; one prose item makes it not dated).
- [ ] **Step 2: Implement the rule and draw it as the dated table.**
- [ ] **Step 3: Build the plan from the live `departments/institut-tarixi` blocks** (names known from the current heading/paragraph blocks; the script asserts every portrait file exists and every person block group is complete).
- [ ] **Step 4: `apply.py` and scratch-database test.**
- [ ] **Step 5: Make the departments page draw `institut-tarixi` through `ArticleBody`; delete the two files; browser check in three languages (13 person cards, 2 story sections, dated list), same look as today.**
- [ ] **Step 6: Commit** `content: Institut tarixi in block order, history code removed (script 43)`

### Task 9: Menu labels (script 44)

**Files:**
- Create: `deploy/content/yillik-hisobot-2026-44/{plan.json,apply.py}`

**Interfaces:**
- Produces: corrected `label` (ru, en) of the menu items: Kredit modul nizomi, Test markazi nizomi, Talabalar kengashi nizomi ("Положение о ...", "Regulations on the ..."), Institut yo'riqnomasi ("Должностная инструкция", "Job description"), "тестированного" fixed; applied on both menu entries that exist for Kredit modul (ids 1836 and under Me'yoriy hujjatlar).

- [ ] **Step 1: Write the plan from the live menu (ids and old labels, fingerprints); `apply.py` with dry/apply/undo; scratch test; commit** `content: menu labels in ru and en corrected (script 44)`

### Task 10: Cleanup, the rerunnable audit, final verification

**Files:**
- Create: `scripts/audit_section.py` (the audit used on 2026-11-25: structure per block in three languages, language of every text, broken links; argument: the section's menu label)
- Modify: `frontend/src/lib/layoutBlocks.ts` (delete the legacy `raw_html` branch of `picturesOf`), `frontend/src/lib/enhanceCmsHtml.ts`, `frontend/src/styles/cms-content.css`, `frontend/src/styles/inner-page.css`, `frontend/src/i18n/local/*/common.ts`, `docs/` runbook

- [ ] **Step 1: Delete the legacy `raw_html` branch; `npm test` still passes (tests that used it are rewritten to `image` blocks).**
- [ ] **Step 2: Dead CSS**: for each class of `cms-content.css` and `inner-page.css` not found in `frontend/src` (ts, tsx) nor in the content of the database pages, delete its rules; classes built as `` `prefix-${x}` `` are checked by hand first.
- [ ] **Step 3: Remove the slug branches that no longer have a page**; `grep -rn 'slug === "' frontend/src | wc -l` is lower than 61 and no branch names a page of "Institut haqida".
- [ ] **Step 4: Production build and checks**: `npm run build`, then serve it (`fermi-django-frontend-prod`) and on 3 pages of each type check: no console error, Lighthouse performance not lower than before (the score recorded before Task 1 on `yillik-hisobot-2026` and `institut-tarixi`).
- [ ] **Step 5: Full local run on the scratch database**: apply scripts 39-44 in order, run `scripts/audit_section.py` against the served pages: Expected: no structure, language or link problem on the 25 pages in uz, ru and en (except the two documents the user does not have: the PDF of the internal rules and of the Student Council regulations).
- [ ] **Step 6: Write the server runbook** (`docs/superpowers/plans/2026-11-25-content-structure-cleanup-runbook.md`): the order is: deploy the new frontend first (it still draws old blocks as plain `block` sections), then apply scripts 39, 40, 41, 42, 43, 44 with a dry run before each; the images in `frontend/public/images/hisobot`, `institut-about.jpg` and `institute-history` are read by the scripts from the repository checkout on the server and can be deleted from `public` afterwards; `chown` check, undo command per script, a `chown` check of the new media, and the undo command per script.
- [ ] **Step 7: Commit** `chore: dead code and CSS removed, section audit saved, runbook written`
