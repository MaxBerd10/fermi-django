import { Fragment, type ReactNode } from "react";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import type { ContentBlock } from "@/types/blocks";

type Photo = { src: string; alt: string; width: number; height: number };

/**
 * The pictures of the annual report sit in raw_html blocks (`<p><img src="/images/hisobot/..."></p>`), so they are the same
 * in every language. The article reads them by their position and shape instead of by the text, so uz, ru and en get the same layout:
 *  - the opening text and its picture side by side,
 *  - a quotation (text in « » or " ") + the picture that follows it (the speaker) as one card,
 *  - a picture that follows a heading, then paragraphs (the rector) as a portrait with the text beside it,
 *  - the pictures of a section (the part after a heading) stand in a column beside the text of that section when the text is long
 *    enough to fill the column, and in a small row under the text when it is short,
 *  - the report file (a PDF link on its own) at the end, as the usual file card,
 *  - the last three paragraphs (source, closing line, contacts) as a quiet footer.
 */
function readPhotos(block: ContentBlock): Photo[] {
  if (block.block_type !== "raw_html") return [];
  const photos: Photo[] = [];
  for (const tag of block.data.html.match(/<img\b[^>]*>/gi) ?? []) {
    const attr = (name: string) => tag.match(new RegExp(`\\b${name}="([^"]*)"`, "i"))?.[1] ?? "";
    const src = attr("src");
    if (!src) continue;
    photos.push({ src, alt: attr("alt"), width: Number(attr("width")) || 960, height: Number(attr("height")) || 640 });
  }
  return photos;
}

function isFileLinkOnly(block: ContentBlock) {
  return block.block_type === "raw_html" && !/<img\b/i.test(block.data.html) && /href="[^"]+\.pdf"/i.test(block.data.html);
}

/**
 * About how many lines of text a block takes in the left column of a section (the column is about 620px wide). It counts blocks,
 * rows and list items, never characters: the text is longer in one language than in another, and the layout must not change
 * when the language does.
 */
function textLines(block: ContentBlock) {
  if (block.block_type === "heading") return 2;
  if (block.block_type === "paragraph") return 3;
  if (block.block_type === "list") return block.data.items.length * 3;
  if (block.block_type === "table") return block.data.rows.length * 1.8 + 1;
  return 0;
}

// a picture of the side column is about 160px (5.7 lines) high plus the gap
const LINES_PER_SIDE_PHOTO = 5.5;

function PhotoImg({ photo }: { photo: Photo }) {
  return <img src={photo.src} alt={photo.alt} width={photo.width} height={photo.height} loading="lazy" decoding="async" />;
}

export default function AnnualReportArticle({ blocks }: { blocks: ContentBlock[] }) {
  const files = blocks.filter(isFileLinkOnly);
  const body = blocks.filter((block) => !isFileLinkOnly(block));

  // the paragraphs after the last list/table, up to the closing pictures: source, closing line, contacts
  let lastData = -1;
  body.forEach((block, index) => {
    if (block.block_type === "list" || block.block_type === "table") lastData = index;
  });
  const footerRoles = new Map<number, string>();
  const tail: number[] = [];
  for (let index = lastData + 1; index < body.length && body[index].block_type === "paragraph"; index++) tail.push(index);
  if (tail.length === 3) ["source", "slogan", "contact"].forEach((role, k) => footerRoles.set(tail[k], role));

  // the page is read section by section (a heading starts a section); a tall picture of a section (a screenshot) goes beside its text
  const groups: { items: ReactNode[]; lines: number; photos: Photo[] }[] = [{ items: [], lines: 0, photos: [] }];
  const items = {
    push: (node: ReactNode) => groups[groups.length - 1].items.push(node),
    get length() { return groups.length === 1 ? groups[0].items.length : 1; },
  };
  let i = 0;
  while (i < body.length) {
    const block = body[i];
    const photos = readPhotos(block);

    // pictures after the closing lines of the report stay a row of their own
    const afterFooter = tail.length === 3 && i > tail[2];
    const ofSection = groups.length > 1 && !afterFooter;

    if (photos.length >= 2) {
      if (ofSection) groups[groups.length - 1].photos.push(...photos);
      else items.push(<PhotoRow key={block.id} photos={photos} />);
      i++;
      continue;
    }

    if (photos.length === 1) {
      const text: ContentBlock[] = [];
      let j = i + 1;
      while (j < body.length && body[j].block_type === "paragraph" && !footerRoles.has(j)) text.push(body[j++]);
      // a picture straight after a heading and before the paragraphs it belongs to: the rector's portrait
      if (text.length > 0 && body[i - 1]?.block_type === "heading") {
        items.push(
          <section key={block.id} className="annual-portrait">
            <figure><PhotoImg photo={photos[0]} /></figure>
            <div>{text.map((paragraph) => <BlockRenderer key={paragraph.id} block={paragraph} />)}</div>
          </section>,
        );
        i = j;
        continue;
      }
      if (ofSection) groups[groups.length - 1].photos.push(photos[0]);
      else items.push(<PhotoRow key={block.id} photos={photos} />);
      i++;
      continue;
    }

    const next = body[i + 1];
    const nextPhotos = next ? readPhotos(next) : [];
    // the opening text with its picture; later, a quotation (text with « » or " ") with the picture of who said it.
    // A plain paragraph followed by a picture (a chart, a screenshot) stays a paragraph, the picture follows it.
    const isOpening = items.length === 0;
    const isQuote = block.block_type === "paragraph" && /[«»“”"]/.test(block.data.text) && block.data.text.length < 600;
    if (block.block_type === "paragraph" && nextPhotos.length === 1 && !footerRoles.has(i) && (isOpening || isQuote)) {
      items.push(
        <section key={block.id} className={isOpening ? "annual-hero" : "annual-quote"}>
          <figure><PhotoImg photo={nextPhotos[0]} /></figure>
          <div><BlockRenderer block={block} /></div>
        </section>,
      );
      i += 2;
      continue;
    }

    const role = footerRoles.get(i);
    if (block.block_type === "heading") groups.push({ items: [], lines: 0, photos: [] });
    groups[groups.length - 1].lines += textLines(block);
    items.push(
      role ? <div key={block.id} className={`annual-${role}`}><BlockRenderer block={block} /></div> : <BlockRenderer key={block.id} block={block} />,
    );
    i++;
  }

  return (
    <>
      {groups.map((group, index) => {
        if (group.photos.length === 0) return <Fragment key={`group-${index}`}>{group.items}</Fragment>;
        // long text: the pictures stand beside it; short text: the pictures follow it as a small row
        if (group.lines >= group.photos.length * LINES_PER_SIDE_PHOTO) {
          return (
            <section key={`split-${index}`} className="annual-split">
              <div>{group.items}</div>
              <div className="annual-aside">
                {group.photos.map((photo) => (
                  <figure key={photo.src} className={photo.height >= photo.width ? "annual-tall" : undefined}><PhotoImg photo={photo} /></figure>
                ))}
              </div>
            </section>
          );
        }
        return (
          <Fragment key={`group-${index}`}>
            {group.items}
            <PhotoRow photos={group.photos} />
          </Fragment>
        );
      })}
      {files.map((block) => <BlockRenderer key={block.id} block={block} />)}
    </>
  );
}

/** pictures in a row of their own: one in the middle, two or more as a small gallery */
function PhotoRow({ photos }: { photos: Photo[] }) {
  if (photos.length === 1) return <figure className="annual-single"><PhotoImg photo={photos[0]} /></figure>;
  return (
    <div className="annual-gallery">
      {photos.map((photo) => <figure key={photo.src}><PhotoImg photo={photo} /></figure>)}
    </div>
  );
}
