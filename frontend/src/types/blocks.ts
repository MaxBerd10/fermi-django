// The structured content-block shape Django's CMS (apps.content) actually
// returns for department/faculty/news `page.blocks`, once the API client has
// already resolved each block's {uz,ru,en} `data` down to the active
// language (see resolveLocale in ../api/client.ts) — so `data` here is just
// the one payload shape for that block_type, not a three-language record.

export interface LocalizedImage {
  id: number;
  file: string;
  width: number | null;
  height: number | null;
  alt_text: string;
}

export interface LocalizedVideo {
  id: number;
  file: string;
  poster: LocalizedImage;
}

export interface LocalizedDocument {
  id: number;
  file: string;
  title: string;
  filename: string;
  file_size: number;
}

export interface HeadingBlockData {
  text: string;
  /** Optional sub-heading level for migrated content whose original HTML had real
   * hierarchy (e.g. an h3 sub-section under an h2 section) that the generic
   * bold-text extraction heuristic otherwise flattens to one level. Renders as h2
   * (the existing default) when absent. */
  level?: 2 | 3;
  /** Set in the admin ("Karta"): this heading starts a highlighted panel that lasts until the next section heading. Decided by the Uzbek text for all languages (resolveLocale). */
  panel?: boolean;
}
export interface ParagraphBlockData {
  text: string;
  /** Quote classification shared by all translations of a block. */
  quote?: boolean;
  /** Old-CMS "kafedra"/faculty content authored its pseudo-headings as a bold
   * paragraph (<p><strong>) rather than a real <h2..6> — the legacy import's
   * bold-text heuristic over-promoted these to heading blocks. `bold: true`
   * marks a block recovered back to its true paragraph role, rendered as
   * bold inline text at body size/weight, not as a section heading. */
  bold?: boolean;
}
export interface ListBlockData {
  items: string[];
  /** Set by the api from the Uzbek list: every item is a dated line, so the list is a chronology in all languages. */
  dated?: boolean;
}
export interface StaffCardBlockData {
  full_name: string;
  title?: string;
}
export interface ImageBlockData {
  image_id: number;
  alt?: string;
  image: LocalizedImage | null;
  /** "diagram" renders the old site's large zoomable-frame + scroll-hint template
   * (see .cms-diagram-* in cms-content.css) for big org-chart/scheme images instead
   * of the default max-w-lg figure. */
  style?: "diagram";
}
export interface VideoBlockData {
  video_id: number;
  caption?: string;
  video: LocalizedVideo | null;
}
export interface DocumentBlockData {
  document_id: number;
  caption?: string;
  document: LocalizedDocument | null;
  /** "button" renders a plain navy pill link ("Hujjatni yuklab olish" on the old
   * site) instead of the default bordered document card. */
  /** `roadmap` uses the legacy in-page PDF viewer used by the institute's
   * annual road map, while `button` keeps the old plain download pill.
   * `attachment` is the document card with its open / download buttons only: the
   * page never opens the PDF inside itself (a page with one PDF otherwise does). */
  style?: "button" | "roadmap" | "card" | "attachment";
}
export interface GalleryItem {
  image_id: number;
  alt?: string;
  image: LocalizedImage | null;
}
export interface GalleryBlockData {
  items: GalleryItem[];
  /** "certificate" renders the numbered/award-badge/captioned card grid the old
   * site's bespoke certificate-page template used (see .cms-cert-* in
   * cms-content.css); absent/anything else keeps the plain square-thumbnail grid. */
  /** `plain` is a group of pictures that stays exactly where it stands in the page, under its own heading (the article layout otherwise gathers all the
   * loose pictures of a section into one row after its text), drawn as the article gallery. */
  style?: "certificate" | "plain";
}
export interface TableBlockData {
  headers: string[];
  rows: string[][];
  /** An optional row of group headings above the column headings (a label may be empty); the spans add up to the number of columns. */
  header_groups?: { label: string; span: number }[];
}
export interface RawHtmlBlockData {
  html: string;
  slug?: string;
}
/** A video or a map of another site, kept as an id / a plain address (the page builds the frame itself, there is no markup to sanitize). */
export type EmbedBlockData =
  | { provider: "youtube"; video_id: string; title?: string }
  | { provider: "map"; src: string; height?: number; title?: string };

export type BlockType =
  | "heading"
  | "paragraph"
  | "list"
  | "staff_card"
  | "image"
  | "video"
  | "document"
  | "gallery"
  | "table"
  | "raw_html"
  | "embed";

interface ContentBlockBase<T extends BlockType, D> {
  id: number;
  order: number;
  block_type: T;
  data: D;
}

export type ContentBlock =
  | ContentBlockBase<"heading", HeadingBlockData>
  | ContentBlockBase<"paragraph", ParagraphBlockData>
  | ContentBlockBase<"list", ListBlockData>
  | ContentBlockBase<"staff_card", StaffCardBlockData>
  | ContentBlockBase<"image", ImageBlockData>
  | ContentBlockBase<"video", VideoBlockData>
  | ContentBlockBase<"document", DocumentBlockData>
  | ContentBlockBase<"gallery", GalleryBlockData>
  | ContentBlockBase<"table", TableBlockData>
  | ContentBlockBase<"raw_html", RawHtmlBlockData>
  | ContentBlockBase<"embed", EmbedBlockData>;

export interface ContentPage {
  id: number;
  slug: string;
  blocks: ContentBlock[];
}
