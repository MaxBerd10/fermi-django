import type { MenuNode } from "@/types/menu";
import { normalizeMenuHref } from "@/lib/siteConstants";

/** Top-level navbar roots shown in main navigation.
 *
 * Keyed by MenuItem.id -- these are OUR Django DB's own auto-increment ids
 * (the 9 top-level nodes, in menu order), not the old Yii2 site's ids. They
 * don't survive import, so a table built against the old site's numbers
 * (71/17/28/...) silently matches nothing here: every generic /blog/ page's
 * breadcrumb and theme would quietly fall back to "default" no matter which
 * section it's actually under. See findRootTheme(), which is what makes
 * this table apply even to a deeply-nested page that isn't listed in
 * MENU_SECTION_THEMES below. */
export const NAV_ROOT_THEMES: Record<number, { theme: string; breadcrumbKey: string }> = {
  1826: { theme: "institut", breadcrumbKey: "nav.section.institut" },
  1904: { theme: "tuzilma", breadcrumbKey: "nav.section.tuzilma" },
  1992: { theme: "faoliyat", breadcrumbKey: "nav.section.faoliyat" },
  2047: { theme: "abiturient", breadcrumbKey: "nav.section.abiturient" },
  2124: { theme: "talabalar", breadcrumbKey: "nav.section.talabalar" },
  2157: { theme: "xorijiy", breadcrumbKey: "nav.section.xorijiy" },
  2163: { theme: "interaktiv", breadcrumbKey: "nav.section.interaktiv" },
  2170: { theme: "kongress", breadcrumbKey: "nav.section.kongress" },
  2172: { theme: "green", breadcrumbKey: "nav.section.green" },
};

/** Sub-sections with dedicated sidebar (under Tuzilma etc.).
 *
 * Same stale-id caveat as NAV_ROOT_THEMES above -- every key below except
 * 2172 (added when fixing the Yashil Universitet page) is still an old
 * Yii2 id with no match in our DB, so a page under one of these
 * unmigrated sub-sections still gets the generic "nav.section.default"
 * breadcrumb text (its sidebar and theme color are already correct via
 * collectLinks()/findRootTheme(), independent of this table). Re-deriving
 * the rest is a bigger, separate pass -- each entry needs its real DB id
 * looked up individually, not a one-off during a single bug's fix. */
export const MENU_SECTION_THEMES: Record<number, { theme: string; breadcrumbKey: string; introKey?: string }> = {
  33: { theme: "institut", breadcrumbKey: "nav.section.institutAbout", introKey: "section.intro.institutAbout" },
  35: { theme: "rahbariyat", breadcrumbKey: "leader.breadcrumb" },
  37: { theme: "fakultet", breadcrumbKey: "nav.section.fakultetlar", introKey: "section.intro.fakultetlar" },
  38: { theme: "kafedra", breadcrumbKey: "nav.section.kafedralar", introKey: "section.intro.kafedralar" },
  75: { theme: "tuzilma", breadcrumbKey: "nav.section.bolimlar", introKey: "section.intro.bolimlar" },
  316: { theme: "moliya", breadcrumbKey: "nav.section.moliya", introKey: "section.intro.moliya" },
  322: { theme: "markazlar", breadcrumbKey: "nav.section.markazlar", introKey: "section.intro.markazlar" },
  99: { theme: "abiturient", breadcrumbKey: "nav.section.bakalavriat", introKey: "section.intro.bakalavriat" },
  100: { theme: "abiturient", breadcrumbKey: "nav.section.magistratura", introKey: "section.intro.magistratura" },
  215: { theme: "abiturient", breadcrumbKey: "nav.section.ordinatura", introKey: "section.intro.ordinatura" },
  233: { theme: "abiturient", breadcrumbKey: "nav.section.qoshma", introKey: "section.intro.qoshma" },
  241: { theme: "abiturient", breadcrumbKey: "nav.section.kochirish", introKey: "section.intro.kochirish" },
  262: { theme: "abiturient", breadcrumbKey: "nav.section.doktorantura", introKey: "section.intro.doktorantura" },
  375: { theme: "abiturient", breadcrumbKey: "nav.section.internatura", introKey: "section.intro.internatura" },
  378: { theme: "xorijiy", breadcrumbKey: "nav.section.xorijiyQabul", introKey: "section.intro.xorijiyQabul" },
  29: { theme: "talabalar", breadcrumbKey: "nav.section.bakalavriatStudent", introKey: "section.intro.bakalavriatStudent" },
  115: { theme: "talabalar", breadcrumbKey: "nav.section.magistraturaStudent", introKey: "section.intro.magistraturaStudent" },
  173: { theme: "talabalar", breadcrumbKey: "nav.section.ordinaturaStudent", introKey: "section.intro.ordinaturaStudent" },
  344: { theme: "talabalar", breadcrumbKey: "nav.section.xorijiyStudent", introKey: "section.intro.xorijiyStudent" },
  414: { theme: "talabalar", breadcrumbKey: "nav.section.iqtidorli", introKey: "section.intro.iqtidorli" },
  573: { theme: "talabalar", breadcrumbKey: "nav.section.klinikFikrlash", introKey: "section.intro.klinikFikrlash" },
  166: { theme: "interaktiv", breadcrumbKey: "nav.section.murojaatlar", introKey: "section.intro.murojaatlar" },
  489: { theme: "interaktiv", breadcrumbKey: "nav.section.malaka", introKey: "section.intro.malaka" },
  329: { theme: "ilmiyOquv", breadcrumbKey: "nav.section.ilmiyOquv", introKey: "section.intro.ilmiyOquv" },
  337: { theme: "texnikum", breadcrumbKey: "nav.section.texnikum", introKey: "section.intro.texnikum" },
  367: { theme: "karyera", breadcrumbKey: "nav.section.karyera", introKey: "section.intro.karyera" },
  514: { theme: "matbuot", breadcrumbKey: "nav.section.matbuot", introKey: "section.intro.matbuot" },
  530: { theme: "registrator", breadcrumbKey: "nav.section.registrator", introKey: "section.intro.registrator" },
  48: { theme: "faoliyat", breadcrumbKey: "nav.section.ilmiyFaoliyat", introKey: "section.intro.ilmiyFaoliyat" },
  49: { theme: "faoliyat", breadcrumbKey: "nav.section.xalqaroFaoliyat", introKey: "section.intro.xalqaroFaoliyat" },
  50: { theme: "faoliyat", breadcrumbKey: "nav.section.moliyaviyFaoliyat", introKey: "section.intro.moliyaviyFaoliyat" },
  51: { theme: "faoliyat", breadcrumbKey: "nav.section.madaniyFaoliyat", introKey: "section.intro.madaniyFaoliyat" },
  245: { theme: "faoliyat", breadcrumbKey: "nav.section.oquvFaoliyat", introKey: "section.intro.oquvFaoliyat" },
  409: { theme: "faoliyat", breadcrumbKey: "nav.section.fakultetFaoliyat", introKey: "section.intro.fakultetFaoliyat" },
  515: { theme: "faoliyat", breadcrumbKey: "nav.section.korrupsiya", introKey: "section.intro.korrupsiya" },
  581: { theme: "faoliyat", breadcrumbKey: "nav.section.loyihalar", introKey: "section.intro.loyihalar" },
  591: { theme: "faoliyat", breadcrumbKey: "nav.section.doktoranturaFaoliyat", introKey: "section.intro.doktoranturaFaoliyat" },
  495: { theme: "abiturient", breadcrumbKey: "nav.section.texnikumBitiruv", introKey: "section.intro.texnikumBitiruv" },
  2170: { theme: "kongress", breadcrumbKey: "nav.section.kongress", introKey: "section.intro.kongress" },
  2172: { theme: "green", breadcrumbKey: "nav.section.green", introKey: "section.intro.green" },
  2157: { theme: "xorijiy", breadcrumbKey: "nav.section.xorijiy", introKey: "section.intro.xorijiy" },
};

export interface MenuSectionLink {
  id: number;
  title: string;
  href: string;
  depth: number;
}

export interface MenuSectionContext {
  sectionId: number;
  title: string;
  theme: string;
  breadcrumbKey: string;
  introKey?: string;
  links: MenuSectionLink[];
}

function findNodeById(nodes: MenuNode[], id: number): MenuNode | null {
  for (const n of nodes) {
    if (n.id === id) return n;
    const found = findNodeById(n.children ?? [], id);
    if (found) return found;
  }
  return null;
}

function findRootTheme(menu: MenuNode[], sectionId: number): string {
  for (const root of menu) {
    if (root.id === sectionId) return NAV_ROOT_THEMES[root.id]?.theme ?? "default";
    if (findNodeById(root.children ?? [], sectionId)) {
      return NAV_ROOT_THEMES[root.id]?.theme ?? "default";
    }
  }
  return "default";
}

function resolveNodeHref(node: MenuNode, sectionMenuId: number): string | null {
  const rawValue = node.urlValue ?? "";
  if (
    sectionMenuId === 48 &&
    (rawValue === "/blog/48/" || rawValue === "/blog/48" || node.id === 598)
  ) {
    return normalizeMenuHref("/blog/48/dissertatsiya-himoyalari");
  }
  if (sectionMenuId === 591 && (rawValue === "/blog/591/" || rawValue === "/blog/591" || node.id === 594)) {
    return normalizeMenuHref("/blog/591/dissertatsiyalar");
  }

  const href = normalizeMenuHref(node.href);
  if (href && href !== "#" && href !== "/") return href;
  if (!node.urlType || !node.urlValue) return null;
  if (node.urlType === "faculty") return normalizeMenuHref(`/faculty/${sectionMenuId}/${node.urlValue}`);
  if (node.urlType === "departments") return normalizeMenuHref(`/departments/${sectionMenuId}/${node.urlValue}`);
  if (node.urlType === "leader") return normalizeMenuHref(`/leader/${sectionMenuId}/${node.urlValue}`);
  if (node.urlType === "documents") return normalizeMenuHref(`/documents/${sectionMenuId}/${node.urlValue}`);
  if (node.urlValue.startsWith("/") || node.urlValue.startsWith("http")) return normalizeMenuHref(node.urlValue);
  return normalizeMenuHref(`/blog/${sectionMenuId}/${node.urlValue}`);
}

function collectLinks(nodes: MenuNode[], sectionMenuId: number, depth = 0, maxDepth = 3): MenuSectionLink[] {
  const out: MenuSectionLink[] = [];
  for (const n of nodes) {
    const href = resolveNodeHref(n, sectionMenuId);
    if (href) {
      out.push({
        id: n.id,
        title: n.title.trim(),
        href,
        depth,
      });
    }
    if (n.children?.length && depth < maxDepth) {
      out.push(...collectLinks(n.children, sectionMenuId, depth + 1, maxDepth));
    }
  }
  return out;
}

function findSectionContainingSlug(nodes: MenuNode[], slug: string, menuId: number): MenuNode | null {
  for (const n of nodes) {
    const href = normalizeMenuHref(n.href);
    if (href.endsWith(`/${slug}`) || n.urlValue === slug) return findNodeById(nodes, menuId) ?? n;
    if (n.children?.length) {
      const child = findSectionContainingSlug(n.children, slug, menuId);
      if (child) return findNodeById(nodes, menuId) ?? n;
    }
  }
  return null;
}

/**
 * Imported menu rows receive new Django primary keys, while search engines and
 * old bookmarks still carry their Yii menu id in `/blog/:menuId/:slug`.
 * Resolve the closest parent that owns the slug so those legacy URLs retain
 * their real sidebar instead of silently rendering as an unsectioned page.
 */
function findSectionForSlug(nodes: MenuNode[], slug: string): MenuNode | null {
  for (const node of nodes) {
    for (const child of node.children ?? []) {
      const href = normalizeMenuHref(child.href);
      if (href?.endsWith(`/${slug}`) || child.urlValue === slug) return node;
    }
    const nested = findSectionForSlug(node.children ?? [], slug);
    if (nested) return nested;
  }
  return null;
}

export function resolveMenuSection(
  menu: MenuNode[],
  menuId?: number,
  slug?: string,
): MenuSectionContext | null {
  const sectionNode = (menuId ? findNodeById(menu, menuId) : null) ?? (slug ? findSectionForSlug(menu, slug) : null);
  if (!sectionNode) return null;

  const sectionId = sectionNode.id;
  const configured = MENU_SECTION_THEMES[sectionId];

  let links = collectLinks(sectionNode.children ?? [], sectionId);
  if (links.length === 0 && slug) {
    const parent = findSectionContainingSlug(menu, slug, sectionId);
    if (parent?.children?.length) {
      links = collectLinks(parent.children, sectionId);
    }
  }

  if (links.length === 0 && (sectionNode.children?.length ?? 0) === 0) {
    const selfHref = resolveNodeHref(sectionNode, sectionId);
    if (selfHref) {
      links = [{ id: sectionNode.id, title: sectionNode.title.trim(), href: selfHref, depth: 0 }];
    }
  }

  if (links.length === 0) return null;

  const theme = configured?.theme ?? findRootTheme(menu, sectionId);

  return {
    sectionId,
    title: sectionNode.title.trim(),
    theme,
    breadcrumbKey: configured?.breadcrumbKey ?? NAV_ROOT_THEMES[sectionId]?.breadcrumbKey ?? "nav.section.default",
    introKey: configured?.introKey,
    links,
  };
}

export function isMenuSectionLinkActive(link: MenuSectionLink, pathname: string, slug?: string): boolean {
  if (pathname === link.href) return true;
  if (slug && link.href.endsWith(`/${slug}`)) return true;
  return false;
}

export function getMenuSectionIntroKey(menuId?: number, slug?: string): string | null {
  if (!menuId) return null;
  const cfg = MENU_SECTION_THEMES[menuId];
  if (cfg?.introKey) return cfg.introKey;
  const root = NAV_ROOT_THEMES[menuId];
  if (root) return `section.intro.${root.theme}`;
  return null;
}
