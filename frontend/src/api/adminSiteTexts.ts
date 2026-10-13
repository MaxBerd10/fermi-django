import { apiClient } from "./client";

export interface SiteTextRow {
  key: string;
  text_uz: string;
  text_ru: string;
  text_en: string;
  updated_at?: string;
}

export async function listSiteTexts(): Promise<SiteTextRow[]> {
  const { data } = await apiClient.get<SiteTextRow[]>("admin/site-texts", undefined, true);
  return Array.isArray(data) ? data : [];
}

/** Saves one text; blanking all three languages removes the override ("deleted": true) and restores the default. */
export async function saveSiteText(row: Pick<SiteTextRow, "key" | "text_uz" | "text_ru" | "text_en">) {
  const { data } = await apiClient.put<SiteTextRow & { deleted?: boolean }>("admin/site-texts", row, true);
  return data;
}
