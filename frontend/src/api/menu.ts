import { apiClient } from "./client";
import type { MenuNode } from "../types/menu";
import i18n from "../i18n";

// CMS content gap: menu item id 442 ("Green university 2021-2026") has Uzbek and
// English titles filled in but was never given a Russian one, so the API falls
// back to the English text for lang=ru. Override here until it's filled in via
// the admin panel's menu editor (/admin/menu-tree) — remove this once that's done.
const RU_TITLE_OVERRIDES: Record<number, string> = {
  442: "Зелёный университет 2021-2026",
};

// Django's real shape (locale already resolved by the API client), see
// apps.menu.serializers.MenuItemSerializer. Navbar.tsx only ever reads
// `.title`/`.href`/`.children` on a MenuNode (urlType/urlValue are never
// branched on in rendering), so the adapter below only needs to fill those.
interface DjangoMenuItem {
  id: number;
  label: string;
  url: string;
  order: number;
  children: DjangoMenuItem[];
}

function mapMenuItem(item: DjangoMenuItem): MenuNode {
  return {
    id: item.id,
    title: item.label,
    urlType: "",
    urlValue: "",
    href: item.url,
    children: item.children.map(mapMenuItem),
  };
}

export async function getMenu(lang?: string) {
  const { data } = await apiClient.get<DjangoMenuItem[]>("menu", lang ? { lang } : undefined);
  const mapped = data.map(mapMenuItem);
  const effectiveLang = (lang || i18n.language)?.slice(0, 2);
  if (effectiveLang !== "ru") return mapped;
  return mapped.map((node) => (RU_TITLE_OVERRIDES[node.id] ? { ...node, title: RU_TITLE_OVERRIDES[node.id] } : node));
}
