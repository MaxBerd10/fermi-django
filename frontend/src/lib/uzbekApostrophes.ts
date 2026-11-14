/**
 * Uzbek Latin writes the letters o and g with a modifier mark: oʻ gʻ (U+02BB, "okina"). The question bank that the
 * test pages show comes from another service and spells it every which way -- a plain ' (U+0027), ‘ or ’ (U+2018 /
 * U+2019), a backtick, an acute accent -- so one test page shows several different marks side by side, each in
 * whatever glyph the font happens to have. This turns them all into the one correct mark.
 *
 * It only touches o/g followed by a mark and then a letter of the same case ("ko'rish", "O'zbekiston"; in words written
 * in capitals "TO'G'RI", "O'ZBEKISTON"), and leaves the English possessive alone ("Cushing's", "CUSHING'S"), mixed-case
 * names ("O'Brien") and closing quotes ("dog'").
 */
const MARKS = "'‘’`´ʼ";
const O_G_MARK = new RegExp(`([oOgG])[${MARKS}](?=[a-z])(?!s\\b)`, "g");
// words written in capitals: TO'G'RI, O'ZBEKISTON (but not the English possessive CUSHING'S)
const CAPS_WORD = new RegExp(`\\b[A-Z][A-Z${MARKS}]*[A-Z]\\b`, "g");
const CAPS_O_G_MARK = new RegExp(`([OG])[${MARKS}](?=[A-Z])(?!S\\b)`, "g");
const ANY_MARK = new RegExp(`[${MARKS}ʻ]`, "g");

// Fields that identify something rather than display it: never rewrite them (a changed code would break the next request).
const IDENTIFYING_KEY = /(^|_)(id|ids|code|slug|key|url|href|src|file|path|link|token|uuid)$/i;

export function uzbekApostrophes(text: string): string {
  return text.replace(O_G_MARK, "$1ʻ").replace(CAPS_WORD, (word) => word.replace(CAPS_O_G_MARK, "$1ʻ"));
}

/** Every string inside `value` (objects, arrays, nested), except identifying fields, with the marks normalised. */
export function normalizeUzbekText<T>(value: T, key = ""): T {
  if (typeof value === "string") {
    return (IDENTIFYING_KEY.test(key) ? value : uzbekApostrophes(value)) as T;
  }
  if (Array.isArray(value)) return value.map((item) => normalizeUzbekText(item, key)) as T;
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) out[k] = normalizeUzbekText(v, k);
    return out as T;
  }
  return value;
}

/**
 * For searching: lower-cased, and every kind of apostrophe counts as the same one, so "o'qish", "o‘qish" and "oʻqish"
 * all find the same subject whichever mark the visitor's keyboard makes.
 */
export function searchKey(text: string): string {
  return text.toLowerCase().replace(ANY_MARK, "'");
}
