// Uzbek Latin's oʻ/gʻ digraph needs exactly one apostrophe-shaped character
// (U+02BB, modifier letter turned comma) -- see api/client.ts's resolveLocale
// for the full rationale (shared here since Telegram-sourced news content
// bypasses resolveLocale entirely -- see lib/newsImages.ts's enrichNewsArticle).
// Deliberately minimal (no tag-stripping, no whitespace collapsing) so it's
// safe to run over real HTML, unlike normalizeCmsOrthography below.
const APOSTROPHE_VARIANTS_RE = /[‘’ʼ`´]/g;

// The plain straight apostrophe between two letters ("Ma'daniy", "o'tkazilgan"): a menu label or a heading
// typed on a keyboard that never autocorrected it. It is safe to rewrite in text, never inside markup
// (an href may contain one), so the HTML case below only walks the text between tags.
const STRAIGHT_BETWEEN_LETTERS_RE = /(\p{L})'(?=\p{L})/gu;

// The same marks spelled as HTML entities (Telegram posts: "Farg&#39;ona", editors: "o&lsquo;quv"): the browser
// decodes them only after this runs, so they would reach the page as straight/curly marks again.
const ENTITY_BETWEEN_LETTERS_RE = /(\p{L})(?:&#0*39;|&#x0*27;|&apos;|&lsquo;|&rsquo;|&#0*821[67];)(?=\p{L})/giu;

export function normalizeUzbekApostrophes(text: string): string {
  if (!text) return text;
  const tidy = (part: string) =>
    part
      .replace(ENTITY_BETWEEN_LETTERS_RE, "$1ʻ")
      .replace(APOSTROPHE_VARIANTS_RE, "ʻ")
      .replace(STRAIGHT_BETWEEN_LETTERS_RE, "$1ʻ");
  if (!text.includes("<")) return tidy(text);
  return text
    .split(/(<[^>]*>)/)
    .map((part, i) => (i % 2 === 1 ? part : tidy(part)))
    .join("");
}

/** CMS va menyu matnlaridagi imlo va belgilarni toʻgʻrilash.
 * Kanonik belgi — ʻ (U+02BB, modifier letter turned comma), butun sayt
 * shu bilan yoziladi (masalan lib/siteConstants.ts, api/client.ts's
 * resolveLocale). Ilgari bu yerda toʻgʻridan-toʻgʻri qarama-qarshi
 * konventsiya bilan ' (oddiy apostrof) ga qaytarilardi — resolveLocale
 * toʻgʻrilagan matnni xuddi shu "Oʻzbekiston" kabi soʻzlarda qayta
 * buzardi (LeaderFeaturedProfile/leaderDisplay orqali chaqirilganda). */
export function normalizeCmsOrthography(text: string): string {
  if (!text) return text;

  return (
    normalizeUzbekApostrophes(text)
      .replace(/O['ʻʼ´`]zbekiston/gi, "Oʻzbekiston")
      .replace(/O['ʻʼ´`]RQ/gi, "OʻRQ")
      .replace(/O['ʻʼ´`]z/g, "Oʻz")
      .replace(/\btogrisia\b/gi, "toʻgʻrisida")
      .replace(/\btalim togri/gi, "taʻlim toʻgʻri")
      .replace(/\bOzbeksiton\b/gi, "Oʻzbekiston")
      .replace(/\bozbeksiton\b/gi, "Oʻzbekiston")
      .replace(/\s+/g, " ")
      .trim()
  );
}

/** HTML entity + teglardan tozalangan matn */
export function decodeAndCleanCmsText(html: string): string {
  if (!html) return "";
  const withoutTags = html.replace(/<[^>]*>/g, " ");
  if (typeof document !== "undefined") {
    const textarea = document.createElement("textarea");
    textarea.innerHTML = withoutTags;
    return normalizeCmsOrthography(textarea.value.replace(/\s+/g, " ").trim());
  }
  return normalizeCmsOrthography(
    withoutTags
      .replace(/&laquo;|&#171;/g, "«")
      .replace(/&raquo;|&#187;/g, "»")
      .replace(/&lsquo;|&#8216;/g, "'")
      .replace(/&rsquo;|&#8217;/g, "'")
      .replace(/&ldquo;|&#8220;/g, '"')
      .replace(/&rdquo;|&#8221;/g, '"')
      .replace(/&mdash;|&#8212;/g, "—")
      .replace(/&nbsp;/g, " ")
      .replace(/&amp;/g, "&")
      .replace(/&quot;/g, '"')
      .replace(/\s+/g, " ")
      .trim(),
  );
}
