// Shapes mostly mirror api/controllers/*.php response payloads 1:1 (see that
// directory in the old Yii2 project for the exact source query per field) —
// EXCEPT Department/Faculty/NewsArticle/Leader/MenuNode, which are now backed
// by the Django REST API instead (apps.departments/faculties/news/menu). The
// adapter functions in src/api/{departments,faculty,news,menu}.ts map Django's
// real field names (name/logo/page.blocks/full_name/label/...) onto these
// same type shapes, so every page/component consuming them is unchanged; only
// `content: string` behaves differently now — see ContentPage below.

import type { ContentBlock } from "./blocks";

export interface MenuBranch {
  id: number;
  title: string;
  subMenus: { id: number; title: string; urlType: string; urlValue: string }[];
}

export interface About {
  id: number;
  title: string;
  content: string;
  img: string;
  slug: string;
  url?: string;
}

export interface Counter {
  professor_teachers: number;
  students: number;
  graduaters: number;
  book_fund: number;
}

export interface NewsCategoryRef {
  id: number;
  title: string;
  slug: string;
}

export interface NewsArticle {
  id: number;
  title: string;
  /** Plain-text join of `blocks` (list items) or the excerpt (list items don't fetch blocks) — see blocksToPlainText. */
  content: string;
  /** The real structured content on a detail fetch — render with BlockRenderer. Absent on list items. */
  blocks?: ContentBlock[];
  img: string;
  slug: string;
  date: string;
  seen: number;
  category: NewsCategoryRef | null;
  menuId?: number;
  file?: string | null;
  telegramUrl?: string;
  translated?: boolean;
  isVideo?: boolean;
  hasDocument?: boolean;
}

export interface FacultyListItem {
  id: number;
  title: string;
  img: string;
  slug: string;
}

export interface FacultyDetail extends FacultyListItem {
  /** Plain-text join of `blocks`, for excerpts/meta descriptions only — see blocksToPlainText. */
  content: string;
  /** The real structured content — render with BlockRenderer, not `content`. */
  blocks: ContentBlock[];
  menu: MenuBranch | null;
  leaders: Leader[];
}

export interface DepartmentListItem {
  title: string;
  img: string;
  slug: string;
}

export interface DepartmentDetail extends DepartmentListItem {
  id: number;
  /** Plain-text join of `blocks`, for excerpts/meta descriptions only — see blocksToPlainText. */
  content: string;
  /** The real structured content — render with BlockRenderer, not `content`. */
  blocks: ContentBlock[];
  menu: MenuBranch | null;
  leaders: Leader[];
}

export interface Leader {
  id: number;
  name: string;
  position: string;
  /** Short "what they do" line — apps.departments.StaffMember.activity_*, blank until backfilled. */
  activity: string;
  /** The full bio — apps.departments.StaffMember.bio_*. */
  biography: string;
  receptionDays: string;
  phone: string;
  faks: string | null;
  email: string;
  photo: string;
}

export interface CoruselSlide {
  id: number;
  title: string;
  content: string;
  img: string;
  href: string | null;
}

export interface GalleryImage {
  id: number;
  title: string;
  img: string;
  slug: string;
  content?: string;
}

export interface VideoItem {
  id: number;
  video: string | null;
  url: string | null;
}

export interface HomeData {
  corusel: CoruselSlide[];
  about: About | null;
  counter: Counter;
  news: NewsArticle[];
  images: { id: number; img: string }[];
  videos: { id: number; video: string | null; url: string | null }[];
  faculties: FacultyListItem[];
  departments: DepartmentListItem[];
}

export interface Page {
  id: number;
  slug: string;
  blocks: ContentBlock[];
}

export interface DocumentItem {
  id: number;
  title: string;
  content: string;
  slug: string;
}

export interface DocumentDetail {
  id: number;
  title: string;
  menu: MenuBranch | null;
  items: DocumentItem[];
}

export interface LeadersResponse {
  /** Django's institute_role slug ("rektor"/"prorektor"), not a numeric id. */
  category: { id: string; title: string };
  menu: MenuBranch | null;
  leaders: Leader[];
}

export interface Schedule {
  id: number;
  title: string;
  file: string;
}

export interface CourseSchedule {
  id: number;
  title: string;
  schedules: Schedule[];
}

export interface SearchResults {
  posts: NewsArticle[];
  pages: { title: string; slug: string }[];
}

export interface SitemapNode {
  id: number;
  title: string;
  children: SitemapNode[];
}

export interface Setting {
  phone: string;
  email: string;
  faks: string | null;
  address: string;
}

export interface Logo {
  img: string;
  title: string;
  subtitle: string | null;
}

export interface Network {
  title: string;
  icon: string;
  url: string;
}

export interface UsefulSite {
  title: string;
  img: string;
  url: string;
}

export interface SiteSettings {
  setting: Setting | null;
  logo: Logo | null;
  networks: Network[];
  usefulSites: UsefulSite[];
  counter: Counter;
}

export interface Region {
  id: number;
  name: string;
}

export interface District {
  id: number;
  regionId: number;
  name: string;
}

export interface Quarter {
  id: number;
  districtId: number;
  name: string;
}

export interface ConnectLeader {
  id: number;
  name: string;
}

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  status: number;
  role: "user" | "admin";
}
