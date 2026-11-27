/**
 * What the page editor's block forms (table, YouTube/map embed, document card) work with: plain helpers, no React, so they can be tested.
 * A block's data is {uz, ru, en}; a form edits all three at once, and anything that changes the SHAPE of a table (a row, a column, a group)
 * changes it in every language together, so the three languages cannot drift apart (the very shifts the language audit kept finding).
 */
export type Lang = "uz" | "ru" | "en";
export const FORM_LANGS: Lang[] = ["uz", "ru", "en"];

export interface HeaderGroup { label: string; span: number }
export interface TablePayload { headers: string[]; rows: string[][]; header_groups?: HeaderGroup[] }
export type TableData = Record<Lang, TablePayload>;

export type EmbedPayload =
  | { provider: "youtube"; video_id: string; title: string }
  | { provider: "map"; src: string; height: number; title: string };
export type EmbedData = Record<Lang, EmbedPayload>;

export interface DocumentPayload { caption: string; style: string }
export type DocumentData = Record<Lang, DocumentPayload>;

export const DOCUMENT_STYLES: { value: string; label: string; hint: string }[] = [
  { value: "card", label: "Karta", hint: "Nomi va «Brauzerda ochish» / «Yuklab olish» tugmalari" },
  { value: "button", label: "Tugma", hint: "Karta bilan bir xil ko'rinish (eski sahifalarda shunday saqlangan)" },
  { value: "roadmap", label: "Sahifada ochiq", hint: "PDF sahifaning o'zida ochilib turadi (faqat hujjatning o'zi bo'lgan sahifa uchun)" },
  { value: "attachment", label: "Qo'shimcha fayl", hint: "Faqat karta, sahifada hech qachon ochilmaydi" },
];

const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
const each = <T,>(data: Record<Lang, T>, change: (payload: T, lang: Lang) => void): Record<Lang, T> => {
  const next = clone(data);
  FORM_LANGS.forEach((lang) => change(next[lang], lang));
  return next;
};

// ---------------------------------------------------------------------------------------------------------------- encoding

/** base64 of the UTF-8 JSON: what the server reads from `data-block-json` / `data-new-block` (apps/content/admin_content.py). */
export function encodeStaged(value: unknown): string {
  const bytes = new TextEncoder().encode(JSON.stringify(value));
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  return btoa(binary);
}

export function decodeStaged<T>(encoded: string): T | null {
  try {
    const binary = atob(encoded);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes)) as T;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------------------------------------------- embeds

/** The 11-character id of a YouTube video from whatever the editor pasted: the id itself, a watch / short / embed / youtu.be link. */
export function youtubeIdFrom(input: string): string | null {
  const text = input.trim();
  if (/^[A-Za-z0-9_-]{11}$/.test(text)) return text;
  const match = /(?:youtu\.be\/|youtube(?:-nocookie)?\.com\/(?:watch\?(?:[^#]*&)?v=|embed\/|shorts\/|live\/|v\/))([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])/.exec(text);
  return match ? match[1] : null;
}

const MAP_SRC_RE = /^https:\/\/www\.google\.com\/maps\/embed\?pb=[A-Za-z0-9!%._-]{10,1500}$/;

/** The Google Maps embed address from what the editor pasted: the whole <iframe ...> code Google gives ("Share > Embed a map") or the address alone. */
export function mapSrcFrom(input: string): string | null {
  const text = input.trim();
  const fromIframe = /\bsrc\s*=\s*["']([^"']+)["']/i.exec(text);
  const candidate = (fromIframe ? fromIframe[1] : text).replace(/&amp;/g, "&").trim();
  return MAP_SRC_RE.test(candidate) ? candidate : null;
}

export const MAP_HEIGHT = { min: 200, max: 1000, default: 450 };

export function emptyEmbed(provider: "youtube" | "map"): EmbedData {
  const make = (): EmbedPayload => (provider === "youtube" ? { provider, video_id: "", title: "" } : { provider, src: "", height: MAP_HEIGHT.default, title: "" });
  return { uz: make(), ru: make(), en: make() };
}

export function embedProblem(data: EmbedData): string | null {
  const first = data.uz;
  if (first.provider === "youtube") return /^[A-Za-z0-9_-]{11}$/.test(first.video_id) ? null : "YouTube havolasini kiriting (video manzili yoki 11 belgili kod).";
  if (!MAP_SRC_RE.test(first.src)) return "Google xarita kodini kiriting: «Ulashish → Xaritani joylashtirish» dagi <iframe …> kodini yoki undagi src manzilini.";
  if (!(Number.isInteger(first.height) && first.height >= MAP_HEIGHT.min && first.height <= MAP_HEIGHT.max)) return `Xarita balandligi ${MAP_HEIGHT.min}–${MAP_HEIGHT.max} px orasida bo'lsin.`;
  return null;
}

/** The video / map address is one for all languages; the title (the accessible name of the frame) is each language's own. */
export function setEmbedField(data: EmbedData, field: "video_id" | "src" | "height", value: string | number): EmbedData {
  return each(data, (payload) => { (payload as unknown as Record<string, unknown>)[field] = value; });
}

// ---------------------------------------------------------------------------------------------------------------- tables

export function emptyTable(columns = 3, rows = 2): TableData {
  const make = (): TablePayload => ({
    headers: Array.from({ length: columns }, (_, i) => (i === 0 ? "№" : "")),
    rows: Array.from({ length: rows }, (_, r) => Array.from({ length: columns }, (_, c) => (c === 0 ? String(r + 1) : ""))),
  });
  return { uz: make(), ru: make(), en: make() };
}

export const addRow = (data: TableData): TableData => each(data, (t) => { t.rows.push(t.headers.map(() => "")); });
export const removeRow = (data: TableData, row: number): TableData => each(data, (t) => { if (t.rows.length > 1) t.rows.splice(row, 1); });
export const addColumn = (data: TableData): TableData => each(data, (t) => {
  t.headers.push("");
  t.rows.forEach((row) => row.push(""));
  if (t.header_groups) t.header_groups.push({ label: "", span: 1 });
});
export function removeColumn(data: TableData, column: number): TableData {
  if (data.uz.headers.length <= 1) return data;
  return each(data, (t) => {
    t.headers.splice(column, 1);
    t.rows.forEach((row) => row.splice(column, 1));
    if (t.header_groups) t.header_groups = shrinkGroups(t.header_groups, column);
  });
}
/** The group heading that covers the removed column gets narrower (and goes away when it covered only that one). */
function shrinkGroups(groups: HeaderGroup[], column: number): HeaderGroup[] {
  let start = 0;
  const next: HeaderGroup[] = [];
  groups.forEach((group) => {
    const covers = column >= start && column < start + group.span;
    start += group.span;
    if (!covers) next.push(group);
    else if (group.span > 1) next.push({ ...group, span: group.span - 1 });
  });
  return next;
}
export const setHeader = (data: TableData, lang: Lang, column: number, value: string): TableData => each(data, (t, l) => { if (l === lang) t.headers[column] = value; });
export const setCell = (data: TableData, lang: Lang, row: number, column: number, value: string): TableData => each(data, (t, l) => { if (l === lang) t.rows[row][column] = value; });

/** A row of group headings above the column headings: `groups` is the list of spans (their sum is the number of columns); the labels are each language's own. */
export function setGroupSpans(data: TableData, spans: number[]): TableData {
  return each(data, (t) => {
    if (!spans.length) { delete t.header_groups; return; }
    t.header_groups = spans.map((span, i) => ({ label: t.header_groups?.[i]?.label ?? "", span }));
  });
}
export const setGroupLabel = (data: TableData, lang: Lang, group: number, value: string): TableData => each(data, (t, l) => { if (l === lang && t.header_groups) t.header_groups[group].label = value; });

export function tableProblem(data: TableData): string | null {
  for (const lang of FORM_LANGS) {
    const t = data[lang];
    if (!t.headers.length || t.headers.some((h) => !h.trim())) return `${lang.toUpperCase()}: har bir ustunning sarlavhasi bo'lishi kerak.`;
    if (!t.rows.length) return `${lang.toUpperCase()}: kamida bitta qator kerak.`;
    if (t.rows.some((row) => row.length !== t.headers.length)) return `${lang.toUpperCase()}: qatorlar ustunlar soniga mos kelmaydi.`;
    if (t.header_groups && t.header_groups.reduce((sum, group) => sum + group.span, 0) !== t.headers.length) return `${lang.toUpperCase()}: guruh sarlavhalari barcha ustunlarni qoplashi kerak.`;
  }
  return null;
}

// ---------------------------------------------------------------------------------------------------------------- documents

export const setDocumentStyle = (data: DocumentData, style: string): DocumentData => each(data, (payload) => { payload.style = style; });
export const setDocumentCaption = (data: DocumentData, lang: Lang, caption: string): DocumentData => each(data, (payload, l) => { if (l === lang) payload.caption = caption; });

/** The form's view of a document card's payload: only the two fields a person can change. */
export function documentFormData(raw: Record<Lang, { caption?: string; style?: string }>): DocumentData {
  const make = (lang: Lang): DocumentPayload => ({ caption: raw[lang]?.caption ?? "", style: raw[lang]?.style ?? "card" });
  return { uz: make("uz"), ru: make("ru"), en: make("en") };
}

// ---------------------------------------------------------------------------------------------------------------- galleries

export interface GalleryPicture {
  /** A picture the site already has ... */
  image_id?: number;
  /** ... or a file just picked / uploaded (the server makes its row when the page is saved). */
  path?: string;
  /** Where to show it in the form. */
  url: string;
  alt: Record<Lang, string>;
}
export interface GalleryForm { style: "" | "certificate" | "plain"; pictures: GalleryPicture[] }
type StagedGallery = Record<Lang, { style?: string; items: { image_id?: number; path?: string; alt?: string; url?: string }[] }>;

export const GALLERY_STYLES: { value: GalleryForm["style"]; label: string; hint: string }[] = [
  { value: "", label: "Oddiy", hint: "Rasmlar matn oxirida bitta qatorga yig'iladi" },
  { value: "plain", label: "Joyida", hint: "Rasmlar galereyasi aynan shu joyda, o'z sarlavhasi ostida turadi" },
  { value: "certificate", label: "Sertifikatlar", hint: "Raqamli, sarlavhali sertifikat kartalari" },
];

/** The gallery form from a saved block: the pictures are the Uzbek list (the server keeps the three languages' pictures the same), each with every language's alt text. */
export function galleryFormFromServer(data: StagedGallery, images: Record<string, { file: string }>): GalleryForm {
  const first = data.uz.items;
  return {
    style: (data.uz.style as GalleryForm["style"]) || "",
    pictures: first.map((item, index) => ({
      image_id: item.image_id,
      url: images[String(item.image_id)]?.file ?? "",
      alt: { uz: item.alt ?? "", ru: data.ru.items[index]?.alt ?? "", en: data.en.items[index]?.alt ?? "" },
    })),
  };
}

/** What the editor puts in the chip (and the server reads on save): every language gets the same pictures in the same order, its own alt text. */
export function galleryStaged(form: GalleryForm): StagedGallery {
  const make = (lang: Lang) => ({
    ...(form.style ? { style: form.style } : {}),
    items: form.pictures.map((picture) => ({
      ...(picture.image_id !== undefined ? { image_id: picture.image_id } : { path: picture.path }),
      alt: picture.alt[lang],
      url: picture.url,
    })),
  });
  return { uz: make("uz"), ru: make("ru"), en: make("en") };
}

export function galleryFormFromStaged(staged: StagedGallery): GalleryForm {
  return {
    style: (staged.uz.style as GalleryForm["style"]) || "",
    pictures: staged.uz.items.map((item, index) => ({
      ...(item.image_id !== undefined ? { image_id: item.image_id } : { path: item.path }),
      url: item.url ?? "",
      alt: { uz: item.alt ?? "", ru: staged.ru.items[index]?.alt ?? "", en: staged.en.items[index]?.alt ?? "" },
    })),
  };
}

export const addPictures = (form: GalleryForm, picked: { path: string; url: string }[]): GalleryForm => ({
  ...form,
  pictures: [...form.pictures, ...picked.map((file) => ({ path: file.path, url: file.url, alt: { uz: "", ru: "", en: "" } }))],
});
export const removePicture = (form: GalleryForm, index: number): GalleryForm => ({ ...form, pictures: form.pictures.filter((_, i) => i !== index) });
export function movePicture(form: GalleryForm, index: number, delta: number): GalleryForm {
  const target = index + delta;
  if (target < 0 || target >= form.pictures.length) return form;
  const pictures = [...form.pictures];
  [pictures[index], pictures[target]] = [pictures[target], pictures[index]];
  return { ...form, pictures };
}
export const setPictureAlt = (form: GalleryForm, lang: Lang, index: number, alt: string): GalleryForm => ({
  ...form,
  pictures: form.pictures.map((picture, i) => (i === index ? { ...picture, alt: { ...picture.alt, [lang]: alt } } : picture)),
});
export const setGalleryStyle = (form: GalleryForm, style: GalleryForm["style"]): GalleryForm => ({ ...form, style });
export const galleryProblem = (form: GalleryForm): string | null => (form.pictures.length ? null : "Galereyada kamida bitta rasm bo'lishi kerak (butun galereyani olib tashlash uchun chipni o'chiring).");

/** What the chip says about itself in the editor (the server writes the same words for a saved block). */
export function chipLabel(blockType: string, data: Record<Lang, unknown>, staged = true): string {
  const tail = staged ? " (saqlaganingizda yangilanadi)" : " — tahrirlash uchun bosing";
  if (blockType === "table") return `Jadval (${(data.uz as TablePayload).rows.length} qator)${tail}`;
  if (blockType === "embed") {
    const embed = data.uz as EmbedPayload;
    return `${embed.provider === "map" ? "Xarita" : "YouTube video"} ${embed.title || ""}${tail}`.replace("  ", " ");
  }
  if (blockType === "gallery") return `Rasmlar galereyasi (${(data as unknown as StagedGallery).uz.items.length} ta)${tail}`;
  const document = data.uz as DocumentPayload;
  return `Hujjat (PDF/fayl) ${document.caption || ""}${tail}`.replace("  ", " ");
}
