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

/**
 * The old site had one page per year of state programme ("dd.gov.uz/uz/pages/2016"); the programme's decree sits on
 * lex.uz, and the ru/en texts of the same page already link there. Year -> lex.uz document (checked by title).
 */
const PROGRAMME_DECREES: Record<string, number> = {
  "2016": 2903502, "2015": 2575143, "2014": 2347400, "2013": 2135768, "2012": 1967131, "2011": 1745082,
  "2009": 1437232, "2008": 1323062, "2006": 973445, "2005": 436991, "2002": 1743746, "2001": 388442,
  "2000": 261518, "1999": 2291986, "1998": 692590,
};
const PROGRAMME_PAGE_RE = /^https?:\/\/(?:www\.)?dd\.gov\.uz\/uz\/pages\/(\d{4})\/?$/i;

function programmeDecree(href: string): string | null {
  const year = PROGRAMME_PAGE_RE.exec(href.trim())?.[1];
  return year && PROGRAMME_DECREES[year] ? `https://lex.uz/docs/-${PROGRAMME_DECREES[year]}` : null;
}

/** Sites of other institutions whose address changed (the old one no longer resolves). */
const MOVED_HOSTS: Array<[RegExp, string]> = [
  [/^(https?:\/\/)(?:www\.)?tdsi\.uz(?=[/?#]|$)/i, "$1tsdi.uz"], // Toshkent davlat stomatologiya instituti
  [/^(https?:\/\/)(?:www\.)?kkmeduniver\.uz(?=[/?#]|$)/i, "$1kkmi.uz"], // Qoraqalpogʻiston tibbiyot instituti
];

/**
 * Addresses that lead nowhere and have no replacement: files of the old site that were never copied over, a
 * portal that no longer exists, and two lex.uz documents that were withdrawn (the ru texts of the higher-education
 * standard and classifier orders). A link to them is worse than no link, so the text stays and the link goes.
 */
const DEAD_LINK_RE =
  /^https?:\/\/(?:www\.)?(?:sammi\.uz\/|dd\.gov\.uz(?:[/?#]|$)|api\.fermi\.uz\/uploads\/|fjsti\.uz\/uploads\/|lex\.uz\/(?:(?:uz|ru)\/)?docs\/-?(?:5705038|5701176)(?:[/?#]|$))/i;

export function isDeadHref(href: string): boolean {
  return DEAD_LINK_RE.test(href.trim()) && !programmeDecree(href);
}

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

  const decree = programmeDecree(value);
  if (decree) return decree;

  for (const [pattern, replacement] of MOVED_HOSTS) {
    if (pattern.test(value)) return value.replace(pattern, replacement);
  }

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
