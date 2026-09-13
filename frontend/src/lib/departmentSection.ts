import type { Leader } from "@/types/content";

export const DEPARTMENT_MENU_ID = 38;

export type DepartmentTheme =
  | "preventive"
  | "basic"
  | "clinical"
  | "social"
  | "tech"
  | "nursing";

/** Slugs that currently 500 on GET /departments/{slug} — use list + leader fallback */
export const DEPARTMENT_API_BROKEN_SLUGS = new Set([
  "normal-anatomiya-kafedrasi",
  "umumiy-jarrohlik-kafedrasi",
  "urologiya-va-onkologiya-kafedrasi",
  "tibbiy-va-biologik-kimyo-kafedrasi",
]);

export function getDepartmentTheme(slug: string): DepartmentTheme {
  if (/gigiyena|preventiv|epidemiologiya|jamoat-salomatligi|hamshiralik|profilaktika/.test(slug)) {
    return /hamshiralik/.test(slug) ? "nursing" : "preventive";
  }
  if (/anatomiya|gistologiya|fiziologiya|patologik|biologik-kimyo|mikrobiologiya/.test(slug)) {
    return "basic";
  }
  if (/biotibbiyot|biofizik|axborot-texnologiya/.test(slug)) return "tech";
  if (/ozbek|lotin|ijtimoiy|tillar|pedagogika|psixologiya/.test(slug)) return "social";
  return "clinical";
}

export function buildDepartmentFallbackContent(leader: Leader | null): string {
  if (!leader) return "";
  const parts: string[] = [];
  if (leader.activity?.trim()) {
    parts.push(`<h3 class="department-fallback-heading">Asosiy vazifalar</h3>${leader.activity}`);
  }
  if (leader.biography?.trim()) {
    parts.push(`<h3 class="department-fallback-heading">Tarjimai hol</h3>${leader.biography}`);
  }
  return parts.join("");
}
