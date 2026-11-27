import type { MenuNode } from "@/types/menu";
import { normalizeMenuHref } from "@/lib/siteConstants";

// Our own Django DB's id for the "Rahbariyat" menu container -- not the old
// Yii2 site's id (35). See lib/menuSection.ts's NAV_ROOT_THEMES comment.
export const LEADER_SECTION_MENU_ID = 1905;
// Public URLs from the Yii site still use this parent id. The imported Django
// menu starts at a different id, but both address the same leadership section.
export const LEGACY_LEADER_SECTION_MENU_ID = 35;

/** The three leadership pages the site draws in their own way (their titles, role labels, toolbars and intro text differ); every other slug is "other". */
export type LeaderPageKind = "rector" | "prorectors" | "departmentHeads" | "other";

const LEADER_PAGE_KIND_BY_SLUG: Record<string, LeaderPageKind> = {
  rektor: "rector",
  prorektorlar: "prorectors",
  "kafedra-mudirlari": "departmentHeads",
};

export function getLeaderPageKind(slug?: string): LeaderPageKind {
  return (slug && LEADER_PAGE_KIND_BY_SLUG[slug]) || "other";
}

export function isLeaderFeaturedPage(slug?: string, count?: number): boolean {
  return getLeaderPageKind(slug) === "rector" && count === 1;
}

export function findLeaderSectionMenu(menu: MenuNode[]): { title: string; items: MenuNode[] } | null {
  for (const top of menu) {
    if (top.id === LEADER_SECTION_MENU_ID) {
      return { title: top.title, items: top.children ?? [] };
    }
    for (const section of top.children ?? []) {
      if (section.id === LEADER_SECTION_MENU_ID) {
        return { title: section.title, items: section.children ?? [] };
      }
    }
  }
  return null;
}

export function isLeaderNavItemActive(item: MenuNode, pathname: string, slug?: string): boolean {
  const href = normalizeMenuHref(item.href);
  if (pathname === href) return true;
  return Boolean(slug && href.endsWith(`/${slug}`));
}

export function getLeaderPageIntroKey(slug?: string): string | null {
  switch (getLeaderPageKind(slug)) {
    case "rector":
      return "leader.intro.rector";
    case "prorectors":
      return "leader.intro.prorektorlar";
    case "departmentHeads":
      return "leader.intro.departmentHeads";
    default:
      return "leader.intro.default";
  }
}

export function isVacantLeader(name: string): boolean {
  return /^vakant$/i.test(name.trim());
}
