import { normalizeCmsOrthography } from "@/lib/normalizeCmsText";
import { stripHtml } from "@/lib/html";

export function displayLeaderText(value: string): string {
  return normalizeCmsOrthography(value.replace(/`/g, "'").replace(/\s+/g, " ").trim());
}

/** CMS activity/biography — faqat bo'sh HTML (&nbsp;, teglar) bo'lmasa true */
export function hasLeaderHtmlContent(html: string | null | undefined): boolean {
  if (!html?.trim()) return false;
  return Boolean(stripHtml(html));
}

export function cleanPhoneForTel(phone: string): string {
  return phone.replace(/[^\d+]/g, "");
}
