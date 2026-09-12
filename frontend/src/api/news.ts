import { apiClient } from "./client";
import type { NewsArticle, NewsCategoryRef } from "../types/content";
import { blocksToPlainText } from "@/lib/blocksToText";
import type { ContentBlock } from "../types/blocks";
import {
  enrichNewsArticle,
  enrichNewsArticles,
  normalizeNewsCategorySlug,
} from "@/lib/newsImages";
import { getTelegramArticle } from "./telegram";
import { isTelegramNewsSlug } from "@/lib/telegramNews";

// Django's real shapes (locale already resolved by the API client).
interface DjangoImage {
  id: number;
  file: string;
  width: number | null;
  height: number | null;
  alt_text: string;
}
interface DjangoNewsListItem {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  cover: DjangoImage | null;
  published_at: string;
}
interface DjangoNewsDetail extends DjangoNewsListItem {
  page: { id: number; slug: string; blocks: ContentBlock[] };
}

function mapListItem(post: DjangoNewsListItem): NewsArticle {
  return {
    id: post.id,
    title: post.title,
    content: post.excerpt, // list items don't fetch blocks — the excerpt is the only body text available here.
    img: post.cover?.file ?? "",
    slug: post.slug,
    date: post.published_at,
    seen: 0, // Django doesn't track view counts today.
    category: null, // Django's news app has no category concept yet — see getNewsCategory below.
  };
}

function mapDetail(post: DjangoNewsDetail): NewsArticle {
  return {
    ...mapListItem(post),
    content: blocksToPlainText(post.page.blocks),
    blocks: post.page.blocks,
  };
}

export async function listNews(page = 1, _menuId?: number) {
  const res = await apiClient.get<DjangoNewsListItem[]>("news", { page });
  return { ...res, data: enrichNewsArticles(res.data.map(mapListItem)) };
}

// Django's news app has no category model yet (the old CMS's news/category/:slug
// concept doesn't exist here) — this degrades to "all news, unfiltered" rather
// than erroring, so the category-list page still shows something real instead
// of a dead end. Revisit once/if a real category model gets added.
export async function getNewsCategory(slug: string, page = 1, _menuId?: number) {
  const apiSlug = normalizeNewsCategorySlug(slug);
  const res = await apiClient.get<DjangoNewsListItem[]>("news", { page });
  const category: NewsCategoryRef = { id: 0, title: apiSlug, slug: apiSlug };
  return {
    ...res,
    data: {
      category,
      menuId: null,
      items: enrichNewsArticles(res.data.map(mapListItem)),
    },
  };
}

export async function getNewsArticle(slug: string, _menuId?: number) {
  if (isTelegramNewsSlug(slug)) {
    return enrichNewsArticle(await getTelegramArticle(slug));
  }
  const { data } = await apiClient.get<DjangoNewsDetail>(`news/${slug}`);
  return enrichNewsArticle(mapDetail(data));
}
