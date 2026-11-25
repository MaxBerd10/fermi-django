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
  | { kind: "person"; heading: ContentBlock; picture: Picture; text: ContentBlock[] }
  | { kind: "section"; blocks: ContentBlock[]; pictures: Picture[]; side: boolean }
  | { kind: "footer"; source: ContentBlock; slogan: ContentBlock; contact: ContentBlock }
  | { kind: "dated"; entries: { period: string; text: string }[] }
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

/** A block the engine draws on its own (a document card, old HTML, a video, a styled picture group...). */
function isStandalone(block: ContentBlock): boolean {
  if (block.block_type === "raw_html") return true;
  if (block.block_type === "image") return block.data.style === "diagram";
  if (block.block_type === "gallery") return Boolean(block.data.style);
  return block.block_type === "document" || block.block_type === "video" || block.block_type === "staff_card";
}

/** An image or gallery with nothing to show (its file is gone). */
function isEmptyPicture(block: ContentBlock): boolean {
  return (block.block_type === "image" && !block.data.image) || (block.block_type === "gallery" && !block.data.style && picturesOf(block).length === 0);
}

function weight(block: ContentBlock): number {
  if (block.block_type === "heading") return 2;
  if (block.block_type === "paragraph") return 3;
  if (block.block_type === "list") return block.data.items.length * 3;
  if (block.block_type === "table") return block.data.rows.length * 1.8 + 1;
  return 0;
}

type Open = { blocks: ContentBlock[]; pictures: Picture[]; hasHeading: boolean };

export function layoutBlocks(blocks: ContentBlock[]): Section[] {
  const items = blocks.filter((block) => !isEmptyPicture(block));
  const sections: Section[] = [];
  let open: Open | null = null;

  const flush = () => {
    if (open && (open.blocks.length > 0 || open.pictures.length > 0)) {
      const lines = open.blocks.reduce((sum, block) => sum + weight(block), 0);
      sections.push({
        kind: "section",
        blocks: open.blocks,
        pictures: open.pictures,
        side: open.hasHeading && open.pictures.length > 0 && lines >= open.pictures.length * LINES_PER_SIDE_PICTURE,
      });
    }
    open = null;
  };
  const start = (hasHeading: boolean): Open => (open ??= { blocks: [], pictures: [], hasHeading });

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
      if (block.data.dated ?? isDatedList(block.data.items)) {
        flush();
        sections.push({ kind: "dated", entries: datedEntries(block.data.items) });
        i++;
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
        sections.push({ kind: "person", heading: block, picture, text });
        i = j;
        continue;
      }
    }
    if (block.block_type === "heading" && block.data.level !== 3) {
      flush();
      start(true).blocks.push(block);
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
  return sections;
}
