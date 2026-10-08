import type { NewsArticle } from "@/types/content";
import { isTelegramNewsSlug } from "@/lib/telegramNews";
import { stripHtml } from "@/lib/html";

const memory = new Map<string, string>();

function cacheKey(lang: string, text: string) {
  return `${lang.slice(0, 2)}:${text}`;
}

function readStore(key: string) {
  try {
    return sessionStorage.getItem(`fermi-tr:${key.slice(0, 180)}`) || "";
  } catch {
    return "";
  }
}

function writeStore(key: string, value: string) {
  try {
    sessionStorage.setItem(`fermi-tr:${key.slice(0, 180)}`, value);
  } catch {
    /* quota */
  }
}

async function translateChunk(text: string, lang: string): Promise<string> {
  const source = String(text || "").trim();
  const code = lang.slice(0, 2);
  if (!source || code === "uz") return source;
  const key = cacheKey(code, source);
  if (memory.has(key)) return memory.get(key) || source;
  const stored = readStore(key);
  if (stored) {
    memory.set(key, stored);
    return stored;
  }

  const tryUrls = [
    `https://api.mymemory.translated.net/get?langpair=${encodeURIComponent(`uz|${code}`)}&q=${encodeURIComponent(source.slice(0, 450))}`,
    `/telegram-feed/translate?lang=${encodeURIComponent(code)}&q=${encodeURIComponent(source.slice(0, 450))}`,
  ];

  for (const url of tryUrls) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(4000) });
      if (!response.ok) continue;
      const payload = await response.json();
      const translated = String(
        payload?.success === false ? "" : payload?.data || payload?.responseData?.translatedText || "",
      ).trim();
      if (!translated || /MYMEMORY WARNING/i.test(translated) || translated === source) continue;
      memory.set(key, translated);
      writeStore(key, translated);
      return translated;
    } catch {
      /* next */
    }
  }
  return source;
}

/** Pieces of at most `max` characters, cut at sentence ends (or spaces), never in the middle of a word. */
function splitAtSentences(text: string, max = 420): string[] {
  const pieces: string[] = [];
  let rest = text.trim();
  while (rest.length > max) {
    const window = rest.slice(0, max);
    const cut = Math.max(window.lastIndexOf(". "), window.lastIndexOf("! "), window.lastIndexOf("? "), window.lastIndexOf("; "));
    const at = cut > max * 0.4 ? cut + 1 : Math.max(window.lastIndexOf(" "), max * 0.4);
    pieces.push(rest.slice(0, at).trim());
    rest = rest.slice(at).trim();
  }
  if (rest) pieces.push(rest);
  return pieces;
}

async function translateLine(text: string, lang: string): Promise<string> {
  const parts: string[] = [];
  for (const piece of splitAtSentences(text)) parts.push(await translateChunk(piece, lang));
  return parts.join(" ");
}

/** The article's lines as plain text, one per line (<br> and the end of a block start a new line). */
function htmlLines(html: string): string[] {
  const separator = "\u0001";
  const withBreaks = html.replace(/<br\s*\/?>/gi, separator).replace(/<\/(p|div|li|h[1-6])>/gi, separator);
  return stripHtml(withBreaks)
    .split(separator)
    .map((line) => line.trim())
    .filter(Boolean);
}

export async function localizeTelegramCards(items: NewsArticle[], lang: string): Promise<NewsArticle[]> {
  const code = lang.slice(0, 2);
  if (code === "uz") return items;
  const out = [];
  for (const item of items) {
    if (!isTelegramNewsSlug(item.slug) || item.translated) {
      out.push(item);
      continue;
    }
    const title = await translateChunk(item.title, code);
    out.push({ ...item, title, translated: title !== item.title });
  }
  return out;
}

export async function localizeTelegramArticle(article: NewsArticle, lang: string): Promise<NewsArticle> {
  const code = lang.slice(0, 2);
  if (code === "uz" || !isTelegramNewsSlug(article.slug)) return article;
  const title = await translateChunk(article.title, code);
  const lines = htmlLines(article.content);
  const translatedLines: string[] = [];
  for (const line of lines) translatedLines.push(await translateLine(line, code));
  return {
    ...article,
    title,
    content:
      translatedLines
        .map((line) => `<p>${line.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</p>`)
        .join("") || article.content,
    translated: title !== article.title,
  };
}
