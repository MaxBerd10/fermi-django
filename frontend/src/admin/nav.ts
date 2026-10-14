export interface NavItem {
  to: string;
  label: string;
  icon: string;
  /** Inbox key in /admin/dashboard `unread`: the count is shown next to the label. */
  badge?: string;
  /** Extra words the quick-search (Ctrl+K) matches, e.g. what an editor would type to find this section. */
  keywords?: string;
}

export interface NavGroup {
  id: string;
  label: string;
  icon: string;
  items: NavItem[];
}

/** Always visible, above the groups. */
export const NAV_TOP: NavItem[] = [
  { to: "/admin", label: "Bosh sahifa", icon: "ri-dashboard-line", keywords: "boshqaruv paneli dashboard" },
];

/** Grouped by what the editors do, not by how the data is stored. */
export const NAV_GROUPS: NavGroup[] = [
  {
    id: "work",
    label: "Kundalik ishlar",
    icon: "ri-edit-box-line",
    items: [
      { to: "/admin/news", label: "Yangiliklar", icon: "ri-newspaper-line", keywords: "xabar e'lon post" },
      { to: "/admin/pages", label: "Sahifalar", icon: "ri-file-text-line", keywords: "matn sahifa cms" },
      { to: "/admin/gallery-images", label: "Foto galereya", icon: "ri-image-line", keywords: "rasm surat" },
      { to: "/admin/videos", label: "Video", icon: "ri-video-line", keywords: "video roliklar" },
    ],
  },
  {
    id: "inbox",
    label: "Murojaatlar",
    icon: "ri-inbox-line",
    items: [
      { to: "/admin/contacts", label: "Aloqa formasi", icon: "ri-mail-line", badge: "contacts", keywords: "xabar murojaat" },
      { to: "/admin/acceptances", label: "Qabul arizalari", icon: "ri-file-edit-line", badge: "acceptances", keywords: "abituriyent ariza" },
      { to: "/admin/virtual-submissions", label: "Virtual qabulxona", icon: "ri-user-voice-line", badge: "virtual-submissions", keywords: "rektor murojaat" },
      { to: "/admin/contest-submissions", label: "Tanlov arizalari", icon: "ri-award-line", badge: "contest-submissions", keywords: "konkurs" },
    ],
  },
  {
    id: "home",
    label: "Bosh sahifa bloklari",
    icon: "ri-layout-masonry-line",
    items: [
      { to: "/admin/home-partners", label: "Hamkorlar", icon: "ri-links-line", keywords: "hamkor havola portal" },
      { to: "/admin/home-projects", label: "Bizning loyihalar", icon: "ri-stack-line", keywords: "loyiha aishifokor" },
      { to: "/admin/home-voices", label: "Talabalar fikri", icon: "ri-user-voice-line", keywords: "iqtibos fikr" },
      { to: "/admin/home-facts", label: "Raqamlar", icon: "ri-bar-chart-line", keywords: "statistika raqam" },
      { to: "/admin/home-why", label: "Nega bizni tanlashadi", icon: "ri-award-line", keywords: "afzallik" },
    ],
  },
  {
    id: "structure",
    label: "Sayt tuzilmasi",
    icon: "ri-organization-chart",
    items: [
      { to: "/admin/menu-tree", label: "Menyu daraxti", icon: "ri-list-check-2", keywords: "menyu navigatsiya" },
      { to: "/admin/faculty", label: "Fakultetlar", icon: "ri-building-line" },
      { to: "/admin/departments", label: "Kafedralar", icon: "ri-building-2-line" },
      { to: "/admin/leaders", label: "Rahbariyat", icon: "ri-team-line", keywords: "rektor prorektor" },
      { to: "/admin/connect-leaders", label: "Aloqa mas'ullari", icon: "ri-contacts-line" },
    ],
  },
  {
    id: "docs",
    label: "Hujjatlar va o'quv",
    icon: "ri-folder-line",
    items: [
      { to: "/admin/documents", label: "Hujjatlar to'plami", icon: "ri-folder-line" },
      { to: "/admin/documents-items", label: "Hujjat elementlari", icon: "ri-file-list-line", keywords: "pdf fayl" },
      { to: "/admin/courses", label: "Kurslar", icon: "ri-book-line" },
      { to: "/admin/schedules", label: "Dars jadvali", icon: "ri-calendar-line" },
    ],
  },
  {
    id: "results",
    label: "Qabul natijalari",
    icon: "ri-trophy-line",
    items: [
      { to: "/admin/result-categories", label: "Yo'nalishlar", icon: "ri-list-check-2" },
      { to: "/admin/result-files", label: "Natija fayllari", icon: "ri-file-pdf-2-line" },
      { to: "/admin/results-page", label: "Sahifa matni", icon: "ri-article-line" },
    ],
  },
  {
    id: "settings",
    label: "Sozlamalar",
    icon: "ri-settings-3-line",
    items: [
      { to: "/admin/setting", label: "Umumiy sozlamalar", icon: "ri-settings-3-line", keywords: "telefon manzil email" },
      { to: "/admin/site-texts", label: "Sayt matnlari", icon: "ri-translate-2", keywords: "tarjima tugma sarlavha" },
      { to: "/admin/logo", label: "Logotip", icon: "ri-shield-star-line" },
      { to: "/admin/networks", label: "Ijtimoiy tarmoqlar", icon: "ri-share-line", keywords: "telegram instagram facebook" },
      { to: "/admin/useful-sites", label: "Foydali saytlar", icon: "ri-links-line" },
      { to: "/admin/counter", label: "Sayt hisoblagichi", icon: "ri-bar-chart-line", keywords: "talaba raqam" },
      { to: "/admin/users", label: "Foydalanuvchilar", icon: "ri-user-settings-line", keywords: "admin parol login" },
    ],
  },
];

/** Below the groups. */
export const NAV_BOTTOM: NavItem[] = [
  { to: "/admin/statistics", label: "Statistika", icon: "ri-bar-chart-2-line", keywords: "tashrif kirish" },
  { to: "/admin/help", label: "Yordam (qo'llanma)", icon: "ri-question-line", keywords: "qanday qo'llanma yordam" },
];

/** Things an editor does often: shown first in the quick-search. */
export const QUICK_ACTIONS: NavItem[] = [
  { to: "/admin/news/new", label: "Yangilik qo'shish", icon: "ri-add-circle-line", keywords: "yangi yangilik post" },
  { to: "/admin/pages/new", label: "Sahifa qo'shish", icon: "ri-add-circle-line", keywords: "yangi sahifa" },
  { to: "/admin/gallery-images/new", label: "Rasm qo'shish (galereya)", icon: "ri-add-circle-line", keywords: "yangi rasm surat" },
];

export const ALL_NAV_ITEMS: NavItem[] = [
  ...NAV_TOP,
  ...NAV_GROUPS.flatMap((group) => group.items),
  ...NAV_BOTTOM,
];

/** The group an address belongs to (so the sidebar can open it), by longest matching section. */
export function groupOf(pathname: string): string | null {
  for (const group of NAV_GROUPS) {
    if (group.items.some((item) => pathname === item.to || pathname.startsWith(`${item.to}/`))) return group.id;
  }
  return null;
}
