// Our own Django DB's id for the "Xorijiy-talabalar" top-level menu section
// -- not the old Yii2 site's id (6). See lib/menuSection.ts's
// NAV_ROOT_THEMES comment.
export const XORIJIY_NEWS_MENU_ID = 2157;
// ... and for the "Tanlovlar" top-level menu entry (Ochiq tanlovlar, Tanlovlar arxivi).
export const TANLOVLAR_MENU_ID = 2183;



export type NewsCategoryFallback = "menu-list";



export type NewsCategoryConfig = {

  theme: string;

  /** CMS kategoriyasi yo'q bo'lsa — menuId bo'yicha yangiliklar ro'yxati */

  fallback?: NewsCategoryFallback;

  menuSectionId?: number;

  titleKey?: string;

};



const CATEGORY_CONFIG: Record<string, NewsCategoryConfig> = {

  tadbirlar: {

    theme: "events",

  },

  tanlovlar: {

    theme: "contest",
    menuSectionId: TANLOVLAR_MENU_ID,

  },

  "tanlovlar-arxivi": {

    theme: "contest",
    menuSectionId: TANLOVLAR_MENU_ID,

  },

  "kimlarga-piyoz-yeyish-mumkin-emas": {

    theme: "xorijiy",

    fallback: "menu-list",

    menuSectionId: XORIJIY_NEWS_MENU_ID,

    titleKey: "nav.section.xorijiy",

  },

};



export function getNewsCategoryConfig(slug?: string): NewsCategoryConfig | null {

  if (!slug) return null;

  return CATEGORY_CONFIG[slug] ?? null;

}



export function isNewsCategoryConfigured(slug?: string): boolean {

  return getNewsCategoryConfig(slug) !== null;

}



export function isNewsMenuLanding(slug?: string, menuId?: number): boolean {

  const config = getNewsCategoryConfig(slug);

  return config?.fallback === "menu-list" && config.menuSectionId === menuId;

}


