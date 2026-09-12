import type { NewsArticle } from "../types/content";
import { ApiError } from "../types/api";
import i18n from "../i18n";
import { FEATURES } from "@/lib/featureFlags";

function activeLang() {
  return (i18n.resolvedLanguage || i18n.language || "uz").slice(0, 2);
}

async function readEnvelope<T>(response: Response): Promise<T> {
  const envelope = (await response.json()) as {
    success: boolean;
    data?: T;
    error?: { message?: string; code?: string };
  };

  if (!envelope.success || envelope.data === undefined) {
    throw new ApiError(envelope.error?.message || "Telegram oqimi olinmadi", envelope.error?.code || "TELEGRAM", response.status);
  }

  return envelope.data;
}

export async function listTelegramNews(): Promise<NewsArticle[]> {
  // No Telegram bot session configured for this deployment — every call site
  // already treats "no telegram items" as the normal case (that's what
  // happens today whenever the real feed is slow/down), so this needs no
  // page-level changes, just returning the same empty-success shape.
  if (!FEATURES.telegram) return [];
  const lang = activeLang();
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), lang === "uz" ? 5000 : 10000);
  try {
    const response = await fetch(`/telegram-feed?lang=${encodeURIComponent(lang)}`, {
      signal: controller.signal,
      cache: lang === "uz" ? "default" : "no-store",
    });
    return await readEnvelope<NewsArticle[]>(response);
  } finally {
    window.clearTimeout(timer);
  }
}

export async function getTelegramArticle(slug: string): Promise<NewsArticle> {
  if (!FEATURES.telegram) {
    throw new ApiError("Telegram feed is not available in this deployment", "TELEGRAM_DISABLED", 404);
  }
  const lang = activeLang();
  const response = await fetch(
    `/telegram-feed/${encodeURIComponent(slug)}?lang=${encodeURIComponent(lang)}&_=${Date.now()}`,
    { cache: "no-store" },
  );
  return readEnvelope<NewsArticle>(response);
}
