import type { EntityConfig, FieldSpec, ListColumn } from "./genericTypes";

export const facultyConfig: EntityConfig = {
  resource: "faculty",
  title: "Fakultetlar",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  deleteWarning: "Fakultet o'chsa, uning sahifasi va rahbarlari (dekan, o'rinbosarlar) ham o'chadi.",
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
  deleteWarning: "Kafedra o'chsa, uning sahifasi va BARCHA xodimlari (mudir, o'qituvchilar) ham o'chadi.",
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
  deleteWarning: "Xodim saytdagi kafedra/fakultet sahifasidan ham yo'qoladi.",
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
  deleteWarning: "To'plam o'chsa, uning ichidagi barcha hujjat elementlari ham o'chadi.",
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
    { kind: "text", key: "url", label: "YouTube video havolasi (tavsiya etiladi, masalan https://youtu.be/…)" },
    { kind: "text", key: "video", label: "Yuklangan video fayl yo'li (texnik maydon: odatda bo'sh qoldiring)" },
  ],
};

export const courseConfig: EntityConfig = {
  resource: "courses",
  title: "Kurslar",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }],
  deleteConfirmField: "title_uz",
  deleteWarning: "Kurs o'chsa, unga biriktirilgan dars jadvallari ham o'chadi.",
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
  deleteWarning: "Yo'nalish o'chsa, undagi barcha natija fayllari ham o'chadi.",
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
  title: "Foydali saytlar",
  listColumns: [{ key: "id", label: "ID" }, { key: "title_uz", label: "Nomi" }, { key: "url", label: "Havola" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
    { kind: "media", key: "img", label: "Logotip (ixtiyoriy)" },
    { kind: "text", key: "url", label: "Havola (https://...)", required: true },
  ],
};

// --- Home-page lists (apps/admin_api/home_views.py) --------------------------------------------
// Only icons that are in the site's icon font subset (public/vendor/remixicon/remixicon-used.css) can be
// picked: a class outside it would show nothing on the public page. Add a new one to the subset first.
const HOME_ICON_OPTIONS = [
  { value: "ri-government-line", label: "Hukumat" },
  { value: "ri-file-list-line", label: "Hujjatlar" },
  { value: "ri-building-line", label: "Bino" },
  { value: "ri-hospital-line", label: "Shifoxona" },
  { value: "ri-graduation-cap-line", label: "Ta'lim" },
  { value: "ri-book-open-line", label: "Kitob" },
  { value: "ri-heart-pulse-line", label: "Salomatlik" },
  { value: "ri-stethoscope-line", label: "Stetoskop" },
  { value: "ri-microscope-line", label: "Mikroskop" },
  { value: "ri-flask-line", label: "Laboratoriya" },
  { value: "ri-global-line", label: "Xalqaro" },
  { value: "ri-shield-check-line", label: "Himoya" },
  { value: "ri-database-2-line", label: "Ma'lumotlar bazasi" },
  { value: "ri-user-star-line", label: "Mentor" },
  { value: "ri-team-line", label: "Jamoa" },
  { value: "ri-questionnaire-line", label: "Test" },
  { value: "ri-vidicon-line", label: "Video" },
  { value: "ri-cpu-line", label: "Texnologiya" },
  { value: "ri-camera-line", label: "Kamera" },
  { value: "ri-award-line", label: "Mukofot" },
  { value: "ri-newspaper-line", label: "Yangiliklar" },
  { value: "ri-mail-line", label: "Pochta" },
  { value: "ri-links-line", label: "Havola" },
];

const ORDER_FIELD: FieldSpec = { kind: "number", key: "order", label: "Tartib raqami (kichigi birinchi; bo'sh = oxiriga)" };
const HIDDEN_FIELD: FieldSpec = { kind: "checkbox", key: "hidden", label: "Saytda ko'rsatilmasin (yashirish)" };

export const homePartnersConfig: EntityConfig = {
  resource: "home-partners",
  title: "Bosh sahifa — Hamkorlar",
  listColumns: [{ key: "order", label: "Tartib" }, { key: "title_uz", label: "Nomi" }, { key: "url", label: "Havola" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
    { kind: "text", key: "url", label: "Havola (https://... yoki /sahifa)", required: true },
    { kind: "select", key: "icon", label: "Belgi", options: HOME_ICON_OPTIONS },
    ORDER_FIELD,
    HIDDEN_FIELD,
  ],
};

export const homeProjectsConfig: EntityConfig = {
  resource: "home-projects",
  title: "Bosh sahifa — Bizning loyihalar",
  listColumns: [{ key: "order", label: "Tartib" }, { key: "title_uz", label: "Nomi" }, { key: "url", label: "Havola" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Nomi", requiredUz: true },
    { kind: "text", key: "url", label: "Havola (bo'sh qoldirilsa kartada \"Tayyorlanmoqda\" chiqadi)" },
    { kind: "media", key: "img", label: "Rasm (4:3 nisbatda, kamida 480×360)" },
    { kind: "select", key: "icon", label: "Belgi", options: HOME_ICON_OPTIONS },
    ORDER_FIELD,
    HIDDEN_FIELD,
  ],
};

export const homeVoicesConfig: EntityConfig = {
  resource: "home-voices",
  title: "Bosh sahifa — Talabalar fikri",
  listColumns: [{ key: "order", label: "Tartib" }, { key: "title_uz", label: "Ism" }, { key: "subtitle_uz", label: "Kurs / lavozim" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-textarea", base: "text", label: "Fikr (iqtibos)", requiredUz: true },
    { kind: "lang-text", base: "title", label: "Ism", requiredUz: true },
    { kind: "lang-text", base: "subtitle", label: "Kurs / lavozim (masalan: 3-kurs talabasi)" },
    ORDER_FIELD,
    HIDDEN_FIELD,
  ],
};

export const homeFactsConfig: EntityConfig = {
  resource: "home-facts",
  title: "Bosh sahifa — Raqamlar (talabalar fikri yonida)",
  listColumns: [{ key: "order", label: "Tartib" }, { key: "value", label: "Raqam" }, { key: "title_uz", label: "Izoh" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "text", key: "value", label: "Raqam (masalan: 92% yoki 20+)", required: true },
    { kind: "lang-text", base: "title", label: "Izoh", requiredUz: true },
    ORDER_FIELD,
    HIDDEN_FIELD,
  ],
};

export const homeWhyConfig: EntityConfig = {
  resource: "home-why",
  title: "Bosh sahifa — Nega bizni tanlashadi",
  listColumns: [{ key: "order", label: "Tartib" }, { key: "title_uz", label: "Sarlavha" }, { key: "value", label: "Raqam" }],
  deleteConfirmField: "title_uz",
  fields: [
    { kind: "lang-text", base: "title", label: "Sarlavha", requiredUz: true },
    { kind: "lang-textarea", base: "text", label: "Qisqa tavsif", requiredUz: true },
    { kind: "text", key: "value", label: "Raqam (masalan: 275+; bo'sh bo'lishi mumkin)" },
    { kind: "lang-text", base: "subtitle", label: "Raqam izohi (masalan: Professorlar)" },
    ORDER_FIELD,
    HIDDEN_FIELD,
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
  inbox: true,
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
  inbox: true,
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
  inbox: true,
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
  inbox: true,
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
  homePartnersConfig,
  homeProjectsConfig,
  homeVoicesConfig,
  homeFactsConfig,
  homeWhyConfig,
  contactConfig,
  acceptanceConfig,
  virtualConfig,
  contestConfig,
  connectLeaderConfig,
];

export const SINGLETON_CONFIGS = [counterConfig, settingConfig, logoConfig, resultsPageConfig];
