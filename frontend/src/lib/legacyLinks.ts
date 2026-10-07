/**
 * Links typed into the old site's pages that no longer lead anywhere, or were never valid addresses.
 * Content editors cannot see these from the page, so they are repaired when the page is shown; the stored
 * text is left alone (when an editor fixes it there, the repair simply has nothing left to do).
 */

/** Pages of the old site that moved: the link keeps its meaning, only the address changed. */
const MOVED_PAGES: Array<[RegExp, string]> = [
  // the old site's home page ("/uz", "/ru", "/en") is this site's home page
  [/^\/(?:uz|ru|en)\/?$/i, "/"],
  // "2-Fargʻona Abu Ali ibn Sino ... texnikumi" is listed in the menu as the Fargʻona city college
  [
    /^\/blog\/\d+\/2-fargona-abu-ali-ibn-sino-nomidagi-jamoat-salomatligi-texnikumi\/?$/i,
    "/blog/1967/fargona-shahar-abu-ali-ibn-sino-nomidagi-jamoat-salomatligi-texnikumi",
  ],
  // "Yashil Universitet tadbirlari" (two misspelled copies of one address): the events live in the gallery
  [/^\/blog\/\d+\/e(?:ka|ko)foaol-talabalar-va-yashil-universitet-tadbirlari\/?$/i, "/galereya"],
];

/** The repaired address, or null when the link is fine as typed. */
export function repairLegacyHref(href: string): string | null {
  const value = href.trim();
  if (!value) return null;

  // an e-mail address typed as a web link ("http://info@fjsti.uz")
  const mail = /^(?:https?:\/\/)([^\s/@:]+@[^\s/]+?)\/?$/i.exec(value);
  if (mail) return `mailto:${mail[1]}`;

  // "http://https://tmbm.ssv.uz/", "http://(https://my.gov.uz/oz/service/870)": the real address sits inside
  const nested = /^https?:\/\/\(?(https?:?\/\/[^\s)]+)\)?$/i.exec(value);
  if (nested) return nested[1].replace(/^(https?):?\/\//i, "$1://");

  // a mistyped host ("fsjti" for "fjsti")
  if (/^https?:\/\/hemis\.fsjti\.uz(?=[/?#]|$)/i.test(value)) return value.replace(/fsjti/i, "fjsti");

  let path = value;
  try {
    const url = new URL(value, "https://fermi.uz");
    if (url.origin === "https://fermi.uz") path = url.pathname;
  } catch {
    return null;
  }
  for (const [pattern, target] of MOVED_PAGES) {
    if (pattern.test(path)) return target;
  }
  return null;
}
