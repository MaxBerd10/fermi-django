import { NEWS_DEFAULT_MENU_ID } from "@/lib/newsSection";
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

// The two news roots -- "Institut yangiliklari" (1844) and the "Institut" nav entry (1826) -- keep the all-news
// category list beside them. A news list or article reached from ANY other menu section lists THAT section's pages.
const NEWS_ROOT_MENU_IDS = [NEWS_DEFAULT_MENU_ID, 1826];

/** The menu section whose page list belongs beside a news category list / article, or undefined for the all-news list. */
export function newsSectionMenuId(categorySlug: string | undefined, menuId: number): number | undefined {
  return (
    getNewsCategoryConfig(categorySlug)?.menuSectionId ??
    (menuId > 0 && !NEWS_ROOT_MENU_IDS.includes(menuId) ? menuId : undefined)
  );
}
