import type { EntityConfig, ListColumn } from "./genericTypes";

export const facultyConfig: EntityConfig = {
  resource: "faculty",
  title: "Fakultetlar",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
    { kind: "media", key: "img", label: "Rasm", required: true },
    { kind: "lang-html", base: "content", label: "Matn" },
  ],
};

export const departmentsConfig: EntityConfig = {
  resource: "departments",
  title: "Kafedralar",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
    { kind: "media", key: "img", label: "Rasm", required: true },
    { kind: "lang-html", base: "content", label: "Matn" },
  ],
};

export const leaderConfig: EntityConfig = {
  resource: "leaders",
  title: "Rahbariyat",
  listColumns: [{ key: "id", label: "ID" }, { key: "name_uz", label: "F.I.SH" }, { key: "position_uz", label: "Lavozim" }],
  deleteConfirmField: "name_uz",
  fields: [
    { kind: "lang-text", base: "name", label: "F.I.SH", requiredUz: true },
    { kind: "lang-text", base: "position", label: "Lavozim", requiredUz: true },
    { kind: "async-select", key: "category_id", label: "Toifa", required: true, optionsResource: "leadercategories", optionsLabelKey: "title_uz" },
    { kind: "media", key: "rasm", label: "Foto", required: true },
    { kind: "text", key: "phone", label: "Telefon", required: true },
    { kind: "text", key: "email", label: "Email", required: true },
    { kind: "lang-text", base: "reception_days", label: "Qabul kunlari", requiredUz: true },
    { kind: "lang-html", base: "activity", label: "Faoliyati" },
    { kind: "lang-html", base: "biography", label: "Tarjimai holi" },
  ],
};

export const documentsConfig: EntityConfig = {
  resource: "documents",
  title: "Hujjatlar to'plami",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
  ],
};

export const documentsitemConfig: EntityConfig = {
  resource: "documents-items",
  title: "Hujjat elementlari",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "async-select", key: "document_id", label: "Hujjatlar to'plami", required: true, optionsResource: "documents", optionsLabelKey: "title_uz" },
    { kind: "lang-text", base: "title", label: "Nomi" },
    { kind: "lang-html", base: "content", label: "Matn" },
  ],
};

export const imgConfig: EntityConfig = {
  resource: "gallery-images",
  title: "Foto galereya",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "media", key: "img", label: "Rasm", required: true },
    { kind: "lang-text", base: "title", label: "Nomi" },
  ],
};

export const videoConfig: EntityConfig = {
  resource: "videos",
  title: "Video",
  listColumns: [{ key: "id", label: "ID" }, { key: "url", label: "URL" }],
  deleteConfirmField: "url",
  fields: [
    { kind: "text", key: "video", label: "Video fayl yo'li" },
    { kind: "text", key: "url", label: "Tashqi video URL (YouTube va h.k.)" },
  ],
};

export const courseConfig: EntityConfig = {
  resource: "courses",
  title: "Kurslar",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
  ],
};

export const scheduleConfig: EntityConfig = {
  resource: "schedules",
  title: "Dars jadvali",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
    { kind: "async-select", key: "course_id", label: "Kurs", required: true, optionsResource: "courses", optionsLabelKey: "title_uz" },
    { kind: "media", key: "file", label: "Fayl (PDF)", required: true },
  ],
};

export const resultCategoryConfig: EntityConfig = {
  resource: "result-categories",
  title: "Qabul natijalari — yo'nalishlar",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
  ],
};

export const resultFileConfig: EntityConfig = {
  resource: "result-files",
  title: "Qabul natijalari — fayllar",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
    { kind: "async-select", key: "category_id", label: "Yo'nalish", required: true, optionsResource: "result-categories", optionsLabelKey: "title_uz" },
    { kind: "media", key: "file", label: "Fayl (PDF)", required: true },
  ],
};

export const coruselConfig: EntityConfig = {
  resource: "corusel",
  title: "Bosh sahifa banneri",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi" },
    { kind: "media", key: "img", label: "Rasm" },
    { kind: "lang-html", base: "content", label: "Matn" },
  ],
};

export const networkConfig: EntityConfig = {
  resource: "networks",
  title: "Ijtimoiy tarmoqlar",
  listColumns: [{ key: "id", label: "ID" }, { key: "titlte", label: "Nomi" }, { key: "url", label: "Havola" }],
  deleteConfirmField: "titlte",
  fields: [
    { kind: "text", key: "titlte", label: "Nomi", required: true },
    { kind: "text", key: "icon", label: "Ikonka (masalan: ri-telegram-line)", required: true },
    { kind: "text", key: "url", label: "Havola", required: true },
  ],
};

export const usefulSitesConfig: EntityConfig = {
  resource: "useful-sites",
  title: "Foydali havolalar",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }, { key: "url", label: "Havola" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
    { kind: "media", key: "img", label: "Rasm", required: true },
    { kind: "text", key: "url", label: "Havola", required: true },
  ],
};

// --- Inbound submissions (public forms) -----------------------------------------------------
// These arrive from the site's own forms, so nobody creates them here (noCreate) and the
// submitted content is shown read-only. Only the review state is editable: `status` is 1 while
// unread and 0 once looked at (opening a record marks it read -- apps/admin_api/forms_views.py).

const SUBMISSION_STATUS_OPTIONS = [
  { value: 1, label: "Yangi (ko'rilmagan)" },
  { value: 0, label: "Ko'rib chiqilgan" },
];

const SUBMISSION_BADGES: NonNullable<ListColumn["badges"]> = {
  "1": { label: "Yangi", tone: "amber" },
  "0": { label: "Ko'rilgan", tone: "gray" },
};

export const contactConfig: EntityConfig = {
  resource: "contacts",
  title: "Murojaatlar (Aloqa formasi)",
  noCreate: true,
  listColumns: [
    { key: "id", label: "ID" },
    { key: "created_at", label: "Sana", kind: "datetime" },
    { key: "name", label: "Ism" },
    { key: "subject", label: "Mavzu" },
    { key: "phone", label: "Telefon" },
    { key: "status", label: "Holat", kind: "badge", badges: SUBMISSION_BADGES },
  ],
  deleteConfirmField: "name",
  fields: [
    { kind: "readonly", key: "created_at", label: "Kelgan vaqti", format: "datetime" },
    { kind: "readonly", key: "name", label: "Ism" },
    { kind: "readonly", key: "subject", label: "Mavzu" },
    { kind: "readonly", key: "phone", label: "Telefon" },
    { kind: "readonly", key: "email", label: "Email" },
    { kind: "readonly", key: "message", label: "Xabar matni" },
    { kind: "select", key: "status", label: "Holat", options: SUBMISSION_STATUS_OPTIONS },
  ],
};

export const acceptanceConfig: EntityConfig = {
  resource: "acceptances",
  title: "Qabul arizalari",
  noCreate: true,
  listColumns: [
    { key: "id", label: "ID" },
    { key: "created_at", label: "Sana", kind: "datetime" },
    { key: "fish", label: "F.I.SH" },
    { key: "subject", label: "Mavzu" },
    { key: "phone", label: "Telefon" },
    { key: "status", label: "Holat", kind: "badge", badges: SUBMISSION_BADGES },
  ],
  deleteConfirmField: "fish",
  fields: [
    { kind: "readonly", key: "created_at", label: "Kelgan vaqti", format: "datetime" },
    { kind: "readonly", key: "fish", label: "F.I.SH" },
    { kind: "readonly", key: "subject", label: "Mavzu" },
    { kind: "readonly", key: "phone", label: "Telefon" },
    { kind: "readonly", key: "email", label: "Email" },
    { kind: "select", key: "status", label: "Holat", options: SUBMISSION_STATUS_OPTIONS },
  ],
};

export const virtualConfig: EntityConfig = {
  resource: "virtual-submissions",
  title: "Virtual qabulxona murojaatlari",
  noCreate: true,
  listColumns: [
    { key: "id", label: "ID" },
    { key: "created_at", label: "Sana", kind: "datetime" },
    { key: "fish", label: "F.I.SH" },
    { key: "phone", label: "Telefon" },
    { key: "email", label: "Email" },
    { key: "status", label: "Holat", kind: "badge", badges: SUBMISSION_BADGES },
  ],
  deleteConfirmField: "fish",
  fields: [
    { kind: "readonly", key: "created_at", label: "Kelgan vaqti", format: "datetime" },
    { kind: "readonly", key: "fish", label: "F.I.SH" },
    { kind: "readonly", key: "phone", label: "Telefon" },
    { kind: "readonly", key: "email", label: "Email" },
    { kind: "readonly", key: "gender", label: "Jinsi" },
    { kind: "readonly", key: "address", label: "Manzil" },
    { kind: "readonly", key: "text", label: "Murojaat matni" },
    { kind: "file-link", key: "file", label: "Biriktirilgan fayl", nameKey: "file_name" },
    { kind: "select", key: "status", label: "Holat", options: SUBMISSION_STATUS_OPTIONS },
  ],
};

export const contestConfig: EntityConfig = {
  resource: "contest-submissions",
  title: "Tanlov arizalari",
  noCreate: true,
  listColumns: [
    { key: "id", label: "ID" },
    { key: "created_at", label: "Sana", kind: "datetime" },
    { key: "full_name", label: "F.I.SH" },
    { key: "contest_title", label: "Tanlov" },
    { key: "phone", label: "Telefon" },
    { key: "status", label: "Holat", kind: "badge", badges: SUBMISSION_BADGES },
  ],
  deleteConfirmField: "full_name",
  fields: [
    { kind: "readonly", key: "created_at", label: "Kelgan vaqti", format: "datetime" },
    { kind: "readonly", key: "contest_title", label: "Qaysi tanlovga" },
    { kind: "readonly", key: "full_name", label: "F.I.SH" },
    { kind: "readonly", key: "phone", label: "Telefon" },
    { kind: "readonly", key: "email", label: "Email" },
    { kind: "readonly", key: "message", label: "Izoh" },
    { kind: "file-link", key: "file", label: "Yuborilgan hujjat", nameKey: "file_name" },
    { kind: "select", key: "status", label: "Holat", options: SUBMISSION_STATUS_OPTIONS },
  ],
};

export const connectLeaderConfig: EntityConfig = {
  resource: "connect-leaders",
  title: "Aloqa uchun mas'ullar",
  listColumns: [{ key: "id", label: "ID" }, { key: "name", label: "Nomi" }],
  deleteConfirmField: "name",
  fields: [
    { kind: "text", key: "name", label: "Nomi", required: true },
  ],
};

export const counterConfig: EntityConfig = {
  resource: "counter",
  title: "Statistika (bosh sahifa raqamlari)",
  listColumns: [],
  deleteConfirmField: "id",
  fields: [
    { kind: "number", key: "professor_teachers", label: "Professor-o'qituvchilar soni", required: true },
    { kind: "number", key: "students", label: "Talabalar soni", required: true },
    { kind: "number", key: "graduaters", label: "Bitiruvchilar soni", required: true },
    { kind: "number", key: "book_fund", label: "Kitob fondi", required: true },
  ],
};

export const settingConfig: EntityConfig = {
  resource: "setting",
  title: "Umumiy sozlamalar",
  listColumns: [],
  deleteConfirmField: "id",
  fields: [
    { kind: "text", key: "phone", label: "Telefon", required: true },
    { kind: "text", key: "faks", label: "Faks" },
    { kind: "text", key: "email", label: "Email", required: true },
    { kind: "lang-text", base: "address", label: "Manzil", requiredUz: true },
  ],
};

export const logoConfig: EntityConfig = {
  resource: "logo",
  title: "Logotip",
  listColumns: [],
  deleteConfirmField: "id",
  fields: [
    { kind: "media", key: "img", label: "Logotip rasmi", required: true },
    { kind: "lang-text", base: "title", label: "Sarlavha" },
    { kind: "lang-text", base: "subtitle", label: "Kichik sarlavha" },
  ],
};

export const resultsPageConfig: EntityConfig = {
  resource: "results-page",
  title: "Qabul natijalari — sahifa matni",
  listColumns: [],
  deleteConfirmField: "id",
  fields: [
    { kind: "lang-text", base: "heading", label: "Sarlavha" },
    { kind: "lang-text", base: "intro", label: "Qisqa tavsif" },
    { kind: "lang-textarea", base: "announcement", label: "E'lon matni" },
  ],
};

export const ALL_ENTITY_CONFIGS = [
  facultyConfig,
  departmentsConfig,
  leaderConfig,
  documentsConfig,
  documentsitemConfig,
  imgConfig,
  videoConfig,
  courseConfig,
  scheduleConfig,
  resultCategoryConfig,
  resultFileConfig,
  coruselConfig,
  networkConfig,
  usefulSitesConfig,
  contactConfig,
  acceptanceConfig,
  virtualConfig,
  contestConfig,
  connectLeaderConfig,
];

export const SINGLETON_CONFIGS = [counterConfig, settingConfig, logoConfig, resultsPageConfig];
