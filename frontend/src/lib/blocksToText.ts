import type { ContentBlock } from "@/types/blocks";

/**
 * A plain-text join of a page's blocks — used everywhere the old CMS's
 * `content: string` (raw HTML) field is read for a *snippet*, not a full
 * render: meta descriptions, card excerpts, "featured article" previews
 * (see e.g. NewsCard.tsx, Hero.tsx, About.tsx — all wrap this in the
 * existing `stripHtml()`, which is a harmless no-op on text with no tags).
 * Full body rendering instead uses the real `blocks` array directly via
 * BlockRenderer — see DepartmentPageContent.tsx / FacultyPageContent.tsx.
 */
export function blocksToPlainText(blocks: ContentBlock[]): string {
  return blocks
    .map((block) => {
      switch (block.block_type) {
        case "heading":
        case "paragraph":
          return block.data.text;
        case "list":
          return block.data.items.join(" ");
        default:
          return "";
      }
    })
    .filter(Boolean)
    .join(" ");
}
