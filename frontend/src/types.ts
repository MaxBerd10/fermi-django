export type Lang = "uz" | "ru" | "en";

export interface LocalizedImage {
  id: number;
  file: string;
  width: number | null;
  height: number | null;
  alt_text: string;
}

export interface HeadingData {
  text: string;
}
export interface ParagraphData {
  text: string;
}
export interface ListData {
  items: string[];
}
export interface StaffCardData {
  full_name: string;
  title?: string;
}
export interface ImageBlockData {
  image_id: number;
  alt?: string;
  image: LocalizedImage | null;
}

export type BlockType = "heading" | "paragraph" | "list" | "staff_card" | "image";

interface BlockBase<T extends BlockType, D> {
  id: number;
  order: number;
  block_type: T;
  data: Record<Lang, D>;
}

export type ContentBlock =
  | BlockBase<"heading", HeadingData>
  | BlockBase<"paragraph", ParagraphData>
  | BlockBase<"list", ListData>
  | BlockBase<"staff_card", StaffCardData>
  | BlockBase<"image", ImageBlockData>;

export interface Page {
  id: number;
  slug: string;
  blocks: ContentBlock[];
}

export interface StaffMember {
  id: number;
  full_name: string;
  title: Record<Lang, string>;
  bio: Record<Lang, string>;
  photo: LocalizedImage | null;
  is_head: boolean;
  order: number;
}

export interface DepartmentDetail {
  id: number;
  slug: string;
  name: Record<Lang, string>;
  logo: LocalizedImage | null;
  page: Page;
  staff: StaffMember[];
}

export interface NewsPostListItem {
  id: number;
  slug: string;
  title: Record<Lang, string>;
  excerpt: Record<Lang, string>;
  cover: LocalizedImage | null;
  published_at: string;
}

export interface NewsPostDetail extends NewsPostListItem {
  page: Page;
}

export interface FacultyListItem {
  id: number;
  slug: string;
  name: Record<Lang, string>;
  order: number;
}

export interface FacultyDepartmentRef {
  id: number;
  slug: string;
  name_uz: string;
}

export interface FacultyDetail extends FacultyListItem {
  page: Page;
  departments: FacultyDepartmentRef[];
}

export interface MenuItem {
  id: number;
  label: Record<Lang, string>;
  url: string;
  order: number;
  children: MenuItem[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
