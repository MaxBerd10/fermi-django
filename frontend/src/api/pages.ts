import { apiClient } from "./client";
import type { Page } from "../types/content";

// Django's PageSerializer already returns exactly {id, slug, blocks} —
// menuId is accepted for call-site compatibility (the route always has one)
// but unused; the sidebar/breadcrumb comes from the app's own menu tree, not
// from this endpoint (see resolveMenuSection in lib/menuSection.ts).
export async function getPage(slug: string, _menuId?: number) {
  const { data } = await apiClient.get<Page>(`pages/${slug}`);
  return data;
}
