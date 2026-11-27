import type { ContentBlock } from "@/types/blocks";

/**
 * The layout engine: reads the TYPE and ORDER of a page's blocks and returns the sections to draw. It never reads the slug of the
 * page and never the language of a text (only block, row and list-item counts), so a page looks the same in uz, ru and en.
 * A page it has no rule for comes out as one plain section (blocks one under another).
 */
export type Picture = { src: string; alt: string; width: number | null; height: number | null; tall: boolean };

export type Section =
  | { kind: "opening"; text: ContentBlock; picture: Picture }
  | { kind: "quote"; text: ContentBlock; picture: Picture }
  | { kind: "person"; heading: ContentBlock; picture: Picture; text: ContentBlock[]; card: boolean }
  | { kind: "story"; heading: ContentBlock; picture: Picture; lead: ContentBlock; body: ContentBlock[] }
  | { kind: "step"; heading: ContentBlock; number: string; text: ContentBlock[] }
  | { kind: "section"; blocks: ContentBlock[]; pictures: Picture[]; side: boolean; lead: boolean; panel: boolean }
  | { kind: "footer"; source: ContentBlock; slogan: ContentBlock; contact: ContentBlock }
  | { kind: "dated"; entries: { period: string; text: string }[]; before?: ContentBlock }
  | { kind: "block"; block: ContentBlock };

/** A picture in the side column is about 160px (5.7 lines of text) high plus the gap. */
export const LINES_PER_SIDE_PICTURE = 5.5;

/** "1992–1997 — A", "2021 yildan — B", "с 2021 года — C": a year (or a range) and then a dash with spaces around it. "2027-yil aprel: ..." is not a dated line. */
const datedEntry = /^((?:(?:с|since|from)\s+)?\d{4}(?:\s*[–—-]\s*\d{4})?(?:\s+(?:yildan|года?|гг?\.?|onwards))?)\s+[–—-]\s+(.+)$/iu;

/** True when every item is a dated line. The api (`resolveLocale`) decides this once from the Uzbek list and gives the answer to every language. */
export function isDatedList(items: string[]): boolean {
  return items.length > 0 && items.every((item) => datedEntry.test(item.trim()));
}

function datedEntries(items: string[]) {
  return items.map((item) => {
    const entry = item.trim().match(datedEntry);
    return entry ? { period: entry[1], text: entry[2] } : { period: "", text: item.trim() };
  });
}

function toPicture(src: string, alt: string, width: number | null, height: number | null): Picture {
  return { src, alt, width, height, tall: width !== null && height !== null && height >= width };
}

/** The pictures a block stands for: an image block or an unstyled gallery. */
export function picturesOf(block: ContentBlock): Picture[] {
  if (block.block_type === "image") {
    const { image, alt, style } = block.data;
    if (!image || style === "diagram") return [];
    return [toPicture(image.file, alt ?? image.alt_text ?? "", image.width, image.height)];
  }
  if (block.block_type === "gallery") {
    if (block.data.style) return [];
    return block.data.items.flatMap((item) => (item.image ? [toPicture(item.image.file, item.alt ?? item.image.alt_text ?? "", item.image.width, item.image.height)] : []));
  }
  return [];
}

/** The pictures of a `plain` gallery block: a group that keeps its place in the page (see GalleryBlockData). */
export function plainGalleryPictures(block: ContentBlock): Picture[] {
  if (block.block_type !== "gallery" || block.data.style !== "plain") return [];
  return block.data.items.flatMap((item) => (item.image ? [toPicture(item.image.file, item.alt ?? item.image.alt_text ?? "", item.image.width, item.image.height)] : []));
}

/** A block the engine draws on its own (a document card, old HTML, a video, a styled picture group...). */
function isStandalone(block: ContentBlock): boolean {
  if (block.block_type === "raw_html" || block.block_type === "embed") return true;
  if (block.block_type === "image") return block.data.style === "diagram";
  if (block.block_type === "gallery") return Boolean(block.data.style);
  return block.block_type === "document" || block.block_type === "video" || block.block_type === "staff_card";
}

/** An image or gallery with nothing to show (its file is gone). */
function isEmptyPicture(block: ContentBlock): boolean {
  return (block.block_type === "image" && !block.data.image) || (block.block_type === "gallery" && !block.data.style && picturesOf(block).length === 0);
}

/** A clearly landscape picture (at least 5:4): a nearly square portrait, like the rector's, is not. */
function isWide(picture: Picture): boolean {
  return picture.width !== null && picture.height !== null && picture.width >= picture.height * 1.25;
}

/** "1-bob. ...", "Глава 1", "Chapter 1": the heading of a numbered chapter of a code (drawn as a band). */
export function isChapterHeading(text: string): boolean {
  return /^\s*(?:\d+\s*[-–.]?\s*bob\b|глава\s+\d+|chapter\s+\d+)/iu.test(text);
}

function isSectionHeading(block: ContentBlock): boolean {
  return block.block_type === "heading" && block.data.level !== 3;
}

function isDated(block: ContentBlock): boolean {
  return block.block_type === "list" && (block.data.dated ?? isDatedList(block.data.items));
}

function weight(block: ContentBlock): number {
  if (block.block_type === "heading") return 2;
  if (block.block_type === "paragraph") return 3;
  if (block.block_type === "list") return block.data.items.length * 3;
  if (block.block_type === "table") return block.data.rows.length * 1.8 + 1;
  return 0;
}

type Open = { blocks: ContentBlock[]; pictures: Picture[]; hasHeading: boolean; panel: boolean };

export function layoutBlocks(blocks: ContentBlock[]): Section[] {
  const items = blocks.filter((block) => !isEmptyPicture(block));
  const sections: Section[] = [];
  let open: Open | null = null;

  const flush = () => {
    if (open && (open.blocks.length > 0 || open.pictures.length > 0)) {
      const lines = open.blocks.reduce((sum, block) => sum + weight(block), 0);
      const side = open.hasHeading && open.pictures.length > 0 && lines >= open.pictures.length * LINES_PER_SIDE_PICTURE;
      sections.push({
        kind: "section",
        blocks: open.blocks,
        pictures: open.pictures,
        side,
        // the first section of the page with one picture beside its text: the introduction of the page, the picture is big
        lead: side && open.pictures.length === 1 && sections.length === 0,
        panel: open.panel,
      });
    }
    open = null;
  };
  const start = (hasHeading: boolean, panel = false): Open => (open ??= { blocks: [], pictures: [], hasHeading, panel });

  // the closing source / slogan / contacts: exactly three paragraphs after the last list or table
  let lastData = -1;
  items.forEach((block, index) => {
    if (block.block_type === "list" || block.block_type === "table") lastData = index;
  });
  let footerAt = -1;
  if (lastData >= 0 && items.slice(lastData + 1, lastData + 4).every((b) => b.block_type === "paragraph") && items.slice(lastData + 1, lastData + 4).length === 3) {
    const after = items[lastData + 4];
    if (!after || after.block_type !== "paragraph") footerAt = lastData + 1;
  }

  /** The one picture that follows block `from` when the picture blocks right after it add up to exactly one; a run of several is a gallery. */
  const singlePictureAfter = (from: number) => {
    const pictures: Picture[] = [];
    for (let j = from + 1; j < items.length && !isStandalone(items[j]); j++) {
      const found = picturesOf(items[j]);
      if (found.length === 0) break;
      pictures.push(...found);
    }
    return pictures.length === 1 ? pictures[0] : null;
  };

  let i = 0;
  while (i < items.length) {
    const block = items[i];

    if (i === footerAt) {
      flush();
      sections.push({ kind: "footer", source: items[i], slogan: items[i + 1], contact: items[i + 2] });
      i += 3;
      continue;
    }
    if (block.block_type === "list") {
      if (isDated(block)) {
        flush();
        sections.push({ kind: "dated", entries: datedEntries(block.data.items) });
        i++;
        continue;
      }
      const next = items[i + 1];
      if (next && next.block_type === "list" && isDated(next)) {
        flush();
        sections.push({ kind: "dated", entries: datedEntries(next.data.items), before: block });
        i += 2;
        continue;
      }
    }
    if (isStandalone(block)) {
      flush();
      sections.push({ kind: "block", block });
      i++;
      continue;
    }
    if (block.block_type === "paragraph" && sections.length === 0 && open === null) {
      const picture = singlePictureAfter(i);
      if (picture) {
        sections.push({ kind: "opening", text: block, picture });
        i += 2;
        continue;
      }
    }
    if (block.block_type === "paragraph" && block.data.quote === true) {
      const picture = singlePictureAfter(i);
      if (picture) {
        flush();
        sections.push({ kind: "quote", text: block, picture });
        i += 2;
        continue;
      }
    }
    if (block.block_type === "heading" && block.data.level === 3) {
      const picture = singlePictureAfter(i);
      if (picture) {
        flush();
        const text: ContentBlock[] = [];
        let j = i + 2;
        while (j < items.length && items[j].block_type === "paragraph" && j !== footerAt) text.push(items[j++]);
        sections.push({ kind: "person", heading: block, picture, text, card: false });
        i = j;
        continue;
      }
      const number = block.data.text.trim().length <= 30 ? block.data.text.trim().match(/\s(\d{1,2})$/)?.[1] : undefined;
      if (number) {
        flush();
        const text: ContentBlock[] = [];
        let j = i + 1;
        while (j < items.length && items[j].block_type === "paragraph" && j !== footerAt) text.push(items[j++]);
        sections.push({ kind: "step", heading: block, number, text });
        i = j;
        continue;
      }
    }
    if (block.block_type === "heading" && block.data.level !== 3) {
      // heading, paragraphs only and exactly one clearly landscape picture (first or last): a story, the first paragraph beside the picture
      let end = i + 1;
      while (end < items.length && !isSectionHeading(items[end]) && end !== footerAt) end++;
      const body = items.slice(i + 1, end);
      const pictureBlocks = body.filter((b) => picturesOf(b).length > 0);
      const paragraphs = body.filter((b) => b.block_type === "paragraph");
      const picture = pictureBlocks.length === 1 ? picturesOf(pictureBlocks[0]) : [];
      const atEdge = body[0] === pictureBlocks[0] || body[body.length - 1] === pictureBlocks[0];
      if ((sections.length > 0 || open !== null) && picture.length === 1 && isWide(picture[0]) && atEdge && paragraphs.length >= 1 && paragraphs.length + 1 === body.length && !paragraphs.some((b) => b.block_type === "paragraph" && b.data.quote === true)) {
        flush();
        sections.push({ kind: "story", heading: block, picture: picture[0], lead: paragraphs[0], body: paragraphs.slice(1) });
        i = end;
        continue;
      }
      flush();
      start(true, block.block_type === "heading" && block.data.panel === true).blocks.push(block);
      i++;
      continue;
    }
    const pictures = picturesOf(block);
    if (pictures.length > 0) {
      start(false).pictures.push(...pictures);
      i++;
      continue;
    }
    start(false).blocks.push(block);
    i++;
  }
  flush();
  // two or more people one after another (a history of rectors) are profile cards; one person alone (the rector's address) is not
  sections.forEach((section, index) => {
    if (section.kind !== "person") return;
    section.card = sections[index - 1]?.kind === "person" || sections[index + 1]?.kind === "person";
  });
  return sections;
}
