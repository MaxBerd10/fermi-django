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
}
export interface ParagraphBlockData {
  text: string;
  /** Old-CMS "kafedra"/faculty content authored its pseudo-headings as a bold
   * paragraph (<p><strong>) rather than a real <h2..6> — the legacy import's
   * bold-text heuristic over-promoted these to heading blocks. `bold: true`
   * marks a block recovered back to its true paragraph role, rendered as
   * bold inline text at body size/weight, not as a section heading. */
  bold?: boolean;
}
export interface ListBlockData {
  items: string[];
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
  style?: "button";
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
  style?: "certificate";
}
export interface TableBlockData {
  headers: string[];
  rows: string[][];
}

export type BlockType =
  | "heading"
  | "paragraph"
  | "list"
  | "staff_card"
  | "image"
  | "video"
  | "document"
  | "gallery"
  | "table";

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
  | ContentBlockBase<"table", TableBlockData>;

export interface ContentPage {
  id: number;
  slug: string;
  blocks: ContentBlock[];
}
