# "Institut haqida" section: content lives in the database, one layout engine, no per-page code

Date: 2026-11-25. Status: waiting for approval. Nothing in this document is built yet.

## Why

The 25 pages of "Institut haqida" were audited in all three languages (see the audit of 2026-11-25). What is wrong is not the data model, which is already clean:
`ContentBlock` has typed blocks (heading, paragraph, list, table, image, gallery, document, video), all plain text, all three languages required, and `raw_html` is
documented as "legacy". What is wrong is how far the pages are from it:

- 7 pages are still one `raw_html` blob per language (Missiya, Institut xaqida, USMLE, Ichki tartib, Kodeks, plus image-only pages), and the blobs differ between languages.
- "Institut xaqida" shows text written in the frontend translation files; the 25 KB of HTML in the database is thrown away by the code, so editing the page in the admin changes nothing.
- 98 report photos, the "Institut xaqida" photo and the 15 history portraits are files in the repository, not in the media library, so an editor cannot change them.
- The history page finds a person's photo by matching names with regular expressions (a name change removes the photo).
- 51 `slug === "..."` branches in `enhanceCmsHtml.ts` and 10 in `blog/page.tsx` draw pages by their address; two special article components (`AnnualReportArticle`, `InstituteHistoryArticle`) hold layout rules that belong to every page.
- About 55 CSS classes in `cms-content.css` are not used anywhere.

The aim is the rule: **what an editor can change lives in the database; the code knows only how to draw typed blocks.**

## Goals

1. All 25 pages are typed blocks (no `raw_html`), same structure in uz, ru and en, every picture in the media library.
2. One layout engine draws every typed-block page by general rules read from block types and order (never from the slug, never from the text language). Pages it has no rule for look as they do today (blocks one under another).
3. Per-page code for these pages is deleted: the slug branches, `AnnualReportArticle`, `InstituteHistoryArticle`, `instituteHistoryImages.ts`, the `institut.*` strings in the translation files, the unused CSS.
4. The admin keeps working with its rich-text editor: every structure the engine reads can be written in that editor (a heading, a picture under it, paragraphs).
5. The menu labels with wrong translations are corrected ("nizom" is "Положение" / "Regulations").
6. A test suite fixes the engine's rules (block fixtures in, sections out), and the audit script becomes a check that can be rerun.

## Non-goals

- The other menu sections (Tuzilma, Faoliyat, Abiturient, ...) and the news pages. The engine is general, so they can follow, but they are not changed here.
- New block types in the database or new fields in the admin. The editor stays as it is.
- Rewriting the Missiya page's design. Its look (cards, light panels) becomes the engine's general look for lists and sections.
- Anything is pushed or applied on the server before the user says so.

## Anti-goals

- No fast path that leaves the content in code "just for this page".
- No rule that works only in one language (the layout must be the same when the language changes).
- No change that makes the Lighthouse score worse or adds a console error.

## The layout engine (the rules)

A pure function `layoutBlocks(blocks)` turns the ordered blocks into sections; a small renderer draws the sections. The rules, in order:

1. **Opening**: the first paragraph followed by an image is the opening: text on one side, the picture on the other (small).
2. **Quotation**: a paragraph whose text is in « » or " " followed by an image is a quotation card: small square picture, the words beside it.
3. **Person**: a level-3 heading, an image directly under it, then paragraphs: a profile card (portrait left, text right). Used by the history page and the rector's address.
4. **Section**: a level-2 heading starts a section. Pictures of the section (image and gallery blocks) stand in a column beside its text when the text is long enough to fill the column, otherwise in a small row under the text. "Long enough" is counted in blocks, rows and list items, never in characters (the same section must come out the same in every language).
5. **Tall picture** (higher than wide): kept whole, never cropped. **Four pictures**: two by two.
6. Lists are light cards, tables have the thin frame and light header, document blocks are the file card with "Brauzerda ochish" and "Yuklab olish". (Already done in `inner-page.css`.)
7. The closing three paragraphs after the last list or table are source, closing line and contacts (quiet footer), only when there are exactly three.

These are the rules `AnnualReportArticle` already follows by position; the change is that they apply to every typed page and are tested, and the history page's person detection by name goes away.

## Data (done with the usual dry/apply/undo scripts, backup first, one transaction, skipped if a block was edited in the admin since)

1. **Media**: upload the 98 report photos, the "Institut xaqida" photo and the 15 portraits to the media library as `Image` rows (alt text per language).
2. **Report pages (9)**: the `raw_html` image blocks become `image` and `gallery` blocks.
3. **Institut xaqida**: the dead HTML block becomes heading + two paragraphs + image (the text now in the translation files, three languages) + the ECAQA document block it already has.
4. **Missiya, USMLE, Ichki tartib, Kodeks**: `raw_html` becomes heading, paragraph and list blocks, built from the Uzbek structure (the way the earlier scripts already do), text of ru and en placed unit by unit, the Kodeks in the full translation already prepared (script -38), the USMLE English leftovers removed. *Ichki tartib qoidasi* needs the real document (see open questions).
5. **Image-only pages (6)**: the `raw_html` picture becomes an `image` block.
6. **History**: the 13 portraits get their place in the order (heading, portrait, paragraphs per person) so the engine reads them without names.
7. **Menu**: six labels corrected in ru and en.

## Order, and what each step leaves behind

Each phase is complete by itself (the site works after it) and can be rolled back.

1. **Engine**: write `layoutBlocks` and the renderer with tests; switch the 9 report pages (already typed except for their photos) to it; remove `AnnualReportArticle`. Result: same look as now.
2. **Media and report data**: scripts 1 and 2; the report pages no longer depend on files in the repository.
3. **Institut xaqida** (data 3) and the code that throws its text away.
4. **The four text pages and the image-only pages** (data 4 and 5), `enhanceCmsHtml.ts` branches for them removed.
5. **History** (data 6), `InstituteHistoryArticle` and `instituteHistoryImages.ts` removed.
6. **Cleanup**: menu labels, dead CSS, the `institut.*` strings, the slug branches left over; the audit script rerun on all 25 pages in 3 languages.

## Done means

- The audit shows no structure, language or link problem on the 25 pages in uz, ru and en (apart from the open questions below).
- `npm run type-check`, `npm run lint`, the engine tests and the backend tests pass; no console error; the Lighthouse score of the pages is not lower than before (production build, not dev mode).
- No `raw_html` block on these 25 pages; no slug branch for them in the code; no content text for them in the translation files.
- Editing any of these pages in the admin changes what the site shows.

## Decisions made without the user (veto them if wrong)

- The engine applies to every typed-block `/blog` page, not to a list of slugs. Other pages with typed blocks may change slightly (pictures in a section move beside the text); a sample of them is checked in phase 1.
- The admin editor is not changed. A "picture beside the text" is read from the structure, not set by a button.
- The unused CSS is deleted only after a search of the code and of the database content for each class.

## Open questions (only the user can answer)

1. **Ichki tartib qoidasi** shows only a fragment of the internal rules and two articles of the Code of Ethics, and links the Code's PDF. Is there the full text or the PDF of the *internal rules*?
2. **Talabalar kengashi nizomi** has no document. Is there the PDF?
