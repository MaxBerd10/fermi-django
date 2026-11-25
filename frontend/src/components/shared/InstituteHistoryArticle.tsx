import type { SyntheticEvent } from "react";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import { optimizedImageUrl } from "@/lib/imageProxy";
import { localInstituteHistoryImage } from "@/lib/instituteHistoryImages";
import type { ContentBlock } from "@/types/blocks";

function onHistoryImageError(event: SyntheticEvent<HTMLElement>) {
  const image = event.target;
  if (!(image instanceof HTMLImageElement)) return;
  const src = image.getAttribute("src");
  if (src?.startsWith("/img-cache?")) {
    const params = new URL(src, window.location.origin).searchParams;
    const original = params.get("src");
    if (original && optimizedImageUrl(original, Number(params.get("w"))) === src) {
      image.removeAttribute("srcset");
      image.src = original;
      return;
    }
  }
  image.dataset.historyImageUnavailable = "";
}

function withLocalHistoryImage(block: ContentBlock): ContentBlock {
  if (block.block_type === "raw_html" && !block.data.slug) {
    return { ...block, data: { ...block.data, slug: "institut-tarixi" } };
  }
  if (block.block_type !== "image" || !block.data.image) return block;
  const image = block.data.image;
  const file = localInstituteHistoryImage(image.file) ?? localInstituteHistoryImage(image.alt_text ?? "");
  // The archive scan is 243 × 302, distinguishing it from the other portraits.
  if (!file && image.width === 243 && image.height === 302) {
    return { ...block, data: { ...block.data, image: { ...image, file: "/images/institute-history/rasulov.webp" } } };
  }
  return file ? { ...block, data: { ...block.data, image: { ...image, file } } } : block;
}

function readHistoryProfile(block: ContentBlock) {
  if (block.block_type !== "heading" && block.block_type !== "paragraph") return;
  const text = block.data.text.trim();
  const uppercaseName = text.match(/^\p{Lu}[\p{Lu}ʻ‘’'-]+(?:[ \t]+\p{Lu}[\p{Lu}ʻ‘’'-]+){1,3}/u)?.[0];
  const titleCaseName = /^(?:(?:Professor|Профессор)\s+)?[\p{L}ʻ‘’'.-]+(?:[ \t]+[\p{L}ʻ‘’'.-]+){1,3}$/u.test(text);
  const name = uppercaseName ?? (titleCaseName ? text : "");
  if (!name) return;
  const photo = localInstituteHistoryImage(name);
  if (!photo || photo.endsWith("/archive.webp")) return;
  return { name, photo, introduction: text.slice(name.length).trim() };
}

// "1992–1997 — ...", "2021 yildan — ...", "с 2021 года — ...", "since 2021 — ...": the same list in uz, ru and en.
const chronologyEntry = /^((?:(?:с|since)\s+)?\d{4}(?:\s*[–—-]\s*\d{4})?(?:\s+(?:yildan|года?|гг?\.?|onwards))?)\s*[–—-]\s*(.+)$/i;

function HistoryTimeline({ entries }: { entries: string[] }) {
  const dated = entries.map((entry) => entry.match(chronologyEntry));
  return (
    <div className="cms-history-timeline">
      <ul className="cms-history-timeline__events">
        {entries.map((entry, index) => dated[index] ? null : <li key={index}>{entry}</li>)}
      </ul>
      <ol className="cms-history-timeline__terms">
        {dated.map((entry, index) => entry && (
          <li key={index}><strong>{entry[1]}</strong><span>{entry[2]}</span></li>
        ))}
      </ol>
    </div>
  );
}

// Section labels of the history page in uz, ru and en (the text is the only thing that differs between the languages).
const STORY_LABEL = "tarix sahifasi|xalqaro hamkorlik|страница истории|международное сотрудничество|a page of history|international cooperation";
const SECTION_LABEL = `${STORY_LABEL}|tashkil topishi va huquqiy asoslari|rivojlanish bosqichlari|o.quv va ilmiy yo.nalishlar rahbarlari|этапы развития|руководители учебного и научного направлений|stages of development|heads of the academic and scientific directions`;
const storyLabelPattern = new RegExp(`^(?:${STORY_LABEL})\\s*[:.]?$`, "i");
const sectionLabelPattern = new RegExp(`^(?:${SECTION_LABEL})\\s*[:.]?$`, "i");

function isHistorySectionLabel(text: string) {
  return sectionLabelPattern.test(text.trim());
}

function renderHistoryBlocks(blocks: ContentBlock[]) {
  const profilePhotos = new Set(blocks.map(readHistoryProfile).flatMap((profile) => profile ? [profile.photo] : []));
  const content = blocks.filter((block) => {
    if (block.block_type === "paragraph") return Boolean(block.data.text.replace(/[\u200B-\u200D\uFEFF]/g, "").trim());
    return block.block_type !== "image" || !block.data.image || !profilePhotos.has(block.data.image.file);
  });
  const items = [];
  for (let index = 0; index < content.length; index++) {
    const block = content[index];
    if ((block.block_type === "heading" || block.block_type === "paragraph")
      && storyLabelPattern.test(block.data.text.trim())) {
      const pair = content.slice(index + 1, index + 3);
      const photo = pair.find((entry) => entry.block_type === "image" && entry.data.image);
      const text = pair.find((entry) => entry.block_type === "paragraph");
      if (photo && text && !isHistorySectionLabel(text.data.text)) {
        index += 2;
        const paragraphs: ContentBlock[] = [];
        while (index + 1 < content.length) {
          const next = content[index + 1];
          if (next.block_type !== "paragraph" || isHistorySectionLabel(next.data.text) || readHistoryProfile(next)) break;
          paragraphs.push(next);
          index++;
        }
        items.push(
          <section key={block.id} className="cms-history-story">
            <div className="cms-history-feature">
              <div>
                <h2 className="cms-section-title">{block.data.text.trim()}</h2>
                <BlockRenderer block={text} />
              </div>
              <BlockRenderer block={photo} />
            </div>
            {paragraphs.length > 0 && (
              <div className="cms-history-story__body">
                {paragraphs.map((paragraph) => <BlockRenderer key={paragraph.id} block={paragraph} />)}
              </div>
            )}
          </section>,
        );
        continue;
      }
    }
    const profile = readHistoryProfile(block);
    if (block.block_type === "list" && block.data.items.some((entry) => chronologyEntry.test(entry))) {
      items.push(<HistoryTimeline key={block.id} entries={block.data.items} />);
      continue;
    }
    if (!profile) {
      const sectionLabel = block.block_type === "paragraph" && isHistorySectionLabel(block.data.text);
      items.push(sectionLabel
        ? <h2 key={block.id} className="cms-section-title">{block.data.text.trim()}</h2>
        : <BlockRenderer key={block.id} block={block} />);
      continue;
    }

    const biography: ContentBlock[] = [];
    while (index + 1 < content.length && biography.length < 4) {
      const next = content[index + 1];
      if (readHistoryProfile(next)) break;
      if (next.block_type === "paragraph" && isHistorySectionLabel(next.data.text)) break;
      if (next.block_type === "heading" || (next.block_type === "paragraph" && next.data.bold)) {
        const text = next.data.text.trim();
        const isProfileDetail = /^(?:\d{4}|tibbiyot fanlari|p\.f\.d\.|doctor |candidate |professor|доктор |кандидат |профессор)/i.test(text);
        if (!isProfileDetail) break;
        biography.push({ ...next, block_type: "paragraph", data: { text } });
      } else {
        if (next.block_type !== "paragraph") break;
        biography.push(next);
      }
      index++;
    }

    items.push(
      <section key={block.id} className="cms-history-profile">
        <img src={profile.photo} alt="" loading="lazy" decoding="async" />
        <div className="cms-history-profile__content">
          <h3>{profile.name}</h3>
          {profile.introduction && <p>{profile.introduction}</p>}
          {biography.map((entry) => <BlockRenderer key={entry.id} block={entry} />)}
        </div>
      </section>,
    );
  }
  return items;
}

export default function InstituteHistoryArticle({ blocks }: { blocks: ContentBlock[] }) {
  const content = blocks.map(withLocalHistoryImage);

  return (
    <article
      onErrorCapture={onHistoryImageError}
      className="page-card px-5 py-4 md:px-7 md:py-5 lg:px-8 lg:py-6 cms-article cms-article--rich cms-article--history space-y-4"
    >
      {renderHistoryBlocks(content)}
    </article>
  );
}
