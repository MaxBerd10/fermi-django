/**
 * Legacy CKEditor HTML → clean semantic markup for `.cms-article` styling.
 * Runs in the browser (DOMParser); safe no-op during SSR/build.
 */
import { isDeadHref, repairLegacyHref } from "@/lib/legacyLinks";

export type CmsEnhanceOptions = {
  slug?: string;
  /** The menu's label for the /blog page with this slug, or null when the menu has none. */
  pageTitle?: (slug: string) => string | null;
};

export function getCmsArticleModifier(slug?: string): string {
  if (slug === "institut-ilmiy-kengashi") return "cms-article--council";
  if (slug === "ilmiy-kengash-nizomi" || slug === "ilmiy-kengash-tarkibi" || slug === "kengash-kun-tartibi") {
    return "cms-article--council-pdf";
  }
  if (slug === "ilmiy-kengash") return "cms-article--council-decisions";
  if (slug === "avtoreferatlar") return "cms-article--autoreferat";
  if (slug === "tahrir-hayati-kengashi") return "cms-article--journal-editorial";
  if (slug === "jcpm-2023" || slug === "jcpm-2024" || slug === "jcpm-2025") return "cms-article--journal-archive";
  if (
    slug === "institut-ijtimoy-tibbiy-gazetasi" ||
    slug?.startsWith("institut-gazetasi-arxivi-") ||
    slug === "institut-gazetasi-2025"
  ) {
    return "cms-article--newspaper";
  }
  if (
    slug === "talim-togrisia" ||
    slug === "prezident-farmon-va-qarorlari" ||
    slug === "taraqqiyot-strategiyasi" ||
    slug === "davlat-dasturlari" ||
    slug === "oliy-talimning-davlat-talim-standarti" ||
    slug === "oliy-talim-yonalishlari-va-mutaxassisliklari-klassifikatori" ||
    slug === "ozbeksiton-respublikasi-ssv-buyruqlari"
  ) {
    return "cms-article--regulatory";
  }
  if (
    slug === "ilmiy-konferensiyalar" ||
    slug === "respublika-ilmiy-konferensiyalari" ||
    slug === "fan-olimpiadalari"
  ) {
    return "cms-article--conference";
  }
  if (
    slug === "rektorat" ||
    slug === "oquv-binolari" ||
    slug === "2-oquv-kampusi" ||
    slug === "vivariy" ||
    slug === "simulatsiya-markazi" ||
    slug === "kongress-majmuasi" ||
    slug === "sport-majmualari" ||
    slug === "talabalar-turar-joylari-4"
  ) {
    return "cms-article--buildings";
  }
  if (
    slug === "klinik-va-profilaktik-tibbiyot-jurnali" ||
    slug === "jurnal-xaqida" ||
    slug === "maqola-namunasi"
  ) {
    return "cms-article--journal-pdf";
  }
  return "";
}

/**
 * An editor's stray link around nothing but a space ("<a href='...docx'>&nbsp;</a>") shows no text, yet the
 * file-type badge CSS still paints "DOC" there and the click lands on a (usually long dead) file. The link
 * goes, its content stays.
 */
function unwrapBlankLinks(root: HTMLElement): void {
  root.querySelectorAll("a[href]").forEach((anchor) => {
    if (anchor.querySelector("img, picture, svg, video, iframe, i[class]")) return;
    if ((anchor.textContent ?? "").replace(/[\s\u00a0\u200b]+/g, "") !== "") return;
    anchor.replaceWith(...Array.from(anchor.childNodes));
  });
}

/** Addresses that were mistyped or moved with the old site (see legacyLinks.ts) point to where they were meant to. */
function repairLinks(root: HTMLElement): void {
  const bare = (url: string) => url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, "").replace(/\/$/, "");
  root.querySelectorAll("a[href]").forEach((anchor) => {
    const href = anchor.getAttribute("href") || "";
    if (isDeadHref(href)) {
      anchor.replaceWith(...Array.from(anchor.childNodes));
      return;
    }
    const repaired = repairLegacyHref(href);
    if (!repaired) return;
    // a link whose text is its own address ("www.tdsi.uz") shows the new address too
    const shownAsAddress = bare((anchor.textContent ?? "").trim()) === bare(href);
    anchor.setAttribute("href", repaired);
    if (shownAsAddress && /^https?:\/\//i.test(repaired) && !anchor.querySelector("img")) anchor.textContent = bare(repaired);
  });
}

/** A path of this site's own pages (the same ones RichContent opens in the app). */
const SITE_PAGE_RE =
  /^(?:https?:\/\/(?:www\.)?fermi\.uz)?\/(?:blog|departments|faculty|leader|news|detail|documents|galereya|video|full-gallery|yangiliklar)(?:[/?#]|$)/i;

/**
 * A paragraph that is nothing but one link to another page of the site ("related reading" lines typed between the
 * rules of an article) reads as plain text. It becomes a link row (see .cms-page-link in cms-content.css) and the
 * rules between two such rows go, so a run of them is one tidy group.
 */
function markPageLinkLines(body: HTMLElement): void {
  const norm = (text: string | null) => (text ?? "").replace(/[\s\u00a0\u200b]+/g, " ").trim();
  body.querySelectorAll("p").forEach((p) => {
    if (p.closest("li, table, blockquote, [data-file-card]") || p.querySelector("img")) return;
    const anchors = Array.from(p.querySelectorAll("a[href]"));
    if (anchors.length !== 1 || !SITE_PAGE_RE.test(anchors[0].getAttribute("href") || "")) return;
    const linkText = norm(anchors[0].textContent);
    if (!linkText || linkText.length > 220 || norm(p.textContent) !== linkText) return;
    // rebuilt from scratch: the editor's spans, bold and inline style would otherwise be read as a heading by later passes
    const row = p.ownerDocument.createElement("div");
    row.className = "cms-page-link";
    const link = p.ownerDocument.createElement("a");
    link.setAttribute("href", anchors[0].getAttribute("href") || "");
    link.textContent = linkText;
    row.appendChild(link);
    p.replaceWith(row);
  });
  // rules and blank lines between two link rows go: a run of rows is one group
  const isSeparator = (el: Element) =>
    el.matches("hr, .cms-section-divider") || (el.tagName === "P" && !norm(el.textContent) && !el.querySelector("img, iframe, video"));
  body.querySelectorAll(".cms-page-link").forEach((row) => {
    const between: Element[] = [];
    let next = row.nextElementSibling;
    while (next && isSeparator(next)) {
      between.push(next);
      next = next.nextElementSibling;
    }
    if (next?.classList.contains("cms-page-link")) between.forEach((el) => el.remove());
  });
}

/**
 * A link to a video (YouTube) opens the video in its own tab, so the lesson list stays where it is, and carries a
 * play mark (see .cms-video-link in cms-content.css) so it reads as a video before it is clicked.
 */
function markVideoLinks(root: HTMLElement): void {
  root.querySelectorAll("a[href]").forEach((anchor) => {
    if (!/^https?:\/\/(?:www\.|m\.)?(?:youtu\.be|youtube\.com)\//i.test(anchor.getAttribute("href") || "")) return;
    if (anchor.querySelector("img, iframe")) return;
    anchor.setAttribute("target", "_blank");
    anchor.setAttribute("rel", "noopener noreferrer");
    anchor.classList.add("cms-video-link");
  });
}

/**
 * "Klinik fikrlashga doir video darslar": seven sections, each a "... bo'limi mavzulari" line followed by a numbered
 * list of lesson links. The lines had been typed as <div>, <p> or bold text and the items as bold lines; every section
 * line becomes one kind of heading, and an item is just its text (a lesson without a video yet reads as plain text).
 */
const VIDEO_LESSON_SLUGS = new Set(["klinik-fikrlashga-doir-video-darslar"]);

function normalizeVideoLessons(body: HTMLElement) {
  body.querySelectorAll("div, p, h2, h3").forEach((el) => {
    if (el.closest("li") || el.querySelector("div, p, ol, ul, a[href]")) return;
    const text = (el.textContent ?? "").replace(/[\s\u00a0\u200b]+/g, " ").trim();
    if (text.length > 120 || !/bo['\u2018\u2019\u02bb`]limi mavzulari/i.test(text)) return;
    const h2 = el.ownerDocument.createElement("h2");
    h2.className = "cms-section-title";
    h2.textContent = text.replace(/\.$/, "");
    el.replaceWith(h2);
  });
  body.querySelectorAll("ol > li").forEach((li) => {
    li.querySelectorAll("strong, b").forEach((bold) => bold.replaceWith(...Array.from(bold.childNodes)));
    if (!li.querySelector("a[href]")) li.classList.add("cms-video-pending");
  });
  body.querySelectorAll("ol").forEach((list) => list.classList.add("cms-video-list"));
}

const BLOG_ADDRESS_RE = /^(?:https?:\/\/[^/\s]+)?\/blog\/\d+\/([^/?#\s]+)\/?$/;

/**
 * An editor pasted the page address as the link's own text ("/blog/378/horijiy-fuqarolar-...-tartibi"). The
 * menu knows the page's real name, so the link reads that instead; a text that names a different page than the
 * href, or a page the menu does not list, is left as typed.
 */
function labelAddressLinks(root: HTMLElement, pageTitle: (slug: string) => string | null): void {
  root.querySelectorAll("a[href]").forEach((anchor) => {
    if (anchor.querySelector("img, picture, svg, video, iframe, i[class]")) return;
    const shown = BLOG_ADDRESS_RE.exec((anchor.textContent ?? "").replace(/[\s\u00a0\u200b]+/g, ""));
    const target = BLOG_ADDRESS_RE.exec(anchor.getAttribute("href") || "");
    if (!shown || !target || shown[1] !== target[1]) return;
    let slug = target[1];
    try {
      slug = decodeURIComponent(slug);
    } catch {
      // keep the raw slug
    }
    const title = pageTitle(slug);
    if (title) anchor.textContent = title;
  });
}

export function enhanceCmsHtml(html: string, options?: CmsEnhanceOptions): string {
  if (!html?.trim()) return html;
  if (typeof DOMParser === "undefined") return html;

  const slug = options?.slug ?? "";
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");
  const body = doc.body;

  stripLegacyStyles(body);
  unwrapBlankLinks(body);
  repairLinks(body);
  markVideoLinks(body);
  if (options?.pageTitle) labelAddressLinks(body, options.pageTitle);

  if (slug === "ilmiy-konferensiyalar") moveVideoToTop(body);

  if (slug === "institut-ilmiy-kengashi") {
    buildCouncilMainLayout(body);
    return body.innerHTML;
  }

  if (slug === "ilmiy-kengash") {
    buildCouncilDecisionsLayout(body);
    return body.innerHTML;
  }

  if (slug === "avtoreferatlar") {
    buildAutoreferatLayout(body);
    return body.innerHTML;
  }

  if (slug === "tahrir-hayati-kengashi") {
    buildJournalEditorialLayout(body);
    return body.innerHTML;
  }

  if (slug === "jcpm-2023" || slug === "jcpm-2024" || slug === "jcpm-2025") {
    buildJournalArchiveLayout(body, slug.replace("jcpm-", ""));
    return body.innerHTML;
  }

  if (slug === "mutaxassisliklar-boyicha-testlar-toplami") normalizeStudentTestCover(body);
  else if (slug === "monografiya") normalizeBookCover(body);
  else normalizeHeroImage(body);
  fixHorizontalRulesInLists(body);
  markPageLinkLines(body);
  if (VIDEO_LESSON_SLUGS.has(slug)) normalizeVideoLessons(body);
  if (FACULTY_ACTIVITY_SLUGS.has(slug)) liftBoldTitleLines(body);
  promoteCenteredHeadings(body);
  promoteDivHeadings(body);
  promoteSubsectionHeadings(body);
  promoteMissionCallout(body);
  convertBrListsToUl(body);
  convertDashElementsToLists(body);
  convertNumberedBlocks(body);
  unwrapListParagraphs(body);
  promoteNumberedHeadings(body);
  promoteValueHeadings(body);
  markIntroParagraph(body);
  markLeadParagraph(body);
  body.querySelectorAll("ul, ol").forEach((list) => {
    if (!list.classList.contains("cms-stat-grid") && !list.classList.contains("cms-timeline")) {
      list.classList.add("cms-feature-list");
    }
  });
  if (FACULTY_ACTIVITY_SLUGS.has(slug)) unifyHeadingStyle(body);

  return body.innerHTML;
}

/**
 * The faculty "activity" pages (credit-module system, competencies, strategic plan, mission) were typed with
 * a title line per section, some as <p>, some as <div>, one of them centred: after the generic promotions
 * some titles came out as boxed headings, some as plain bold text, the first one in yet another style.
 * Here every bold, upper-case title line becomes one kind of heading, and whatever the generic pass made
 * of the others is brought to the same one.
 */
const FACULTY_ACTIVITY_SLUGS = new Set([
  "fakultet-talim-faoliyati",
  "xalqaro-talim-faoliyati",
  "pediatriya-fakulteti-faoliyati",
]);

function liftBoldTitleLines(body: HTMLElement) {
  body.querySelectorAll("p, div").forEach((el) => {
    if (el.closest("[data-file-card]") || el.querySelector("a[href], img, p, div, ul, table")) return;
    // the bold text may be cut into several <strong>s and wrapped in any number of font <span>s
    const strongs = Array.from(el.querySelectorAll("strong"));
    if (!strongs.length) return;
    const text = (el.textContent ?? "").replace(/\u00a0/g, " ").trim();
    const strongText = strongs.map((st) => st.textContent ?? "").join("").replace(/\u00a0/g, " ").trim();
    if (!text || text !== strongText || text.length > 120) return;
    if (text !== text.toUpperCase() || !/\p{L}/u.test(text)) return;
    const h2 = el.ownerDocument.createElement("h2");
    h2.className = "cms-section-title";
    h2.textContent = text;
    el.replaceWith(h2);
  });
}

function unifyHeadingStyle(body: HTMLElement) {
  body.querySelectorAll("h2.cms-institute-title, h3.cms-subsection-title").forEach((el) => {
    const h2 = el.ownerDocument.createElement("h2");
    h2.className = "cms-section-title";
    h2.innerHTML = el.innerHTML;
    el.replaceWith(h2);
  });
}

/** A pixel length from legacy markup ("789.594px", "15mm", "36pt") as CSS px, or 0 when it is not an absolute length. */
function toPx(length: string): number {
  const match = /^(-?\d*\.?\d+)(px|pt|mm|cm|in)$/i.exec(length.trim());
  if (!match) return 0;
  const n = parseFloat(match[1]);
  const factor = { px: 1, pt: 4 / 3, mm: 96 / 25.4, cm: 96 / 2.54, in: 96 }[match[2].toLowerCase() as "px"];
  return n * factor;
}

/**
 * Old editors saved the margins they saw on screen: "margin: 0 789px 0 0" on a short block squeezes it to
 * nothing (one letter per line) on any narrower screen. A margin shorthand whose left/right sides are wider
 * than 48px is cut down to its top and bottom values.
 */
function dropWideSideMargins(whole: string, value: string): string {
  const parts = value.trim().split(/\s+/);
  if (parts.length < 2) return whole;
  const top = parts[0];
  const right = parts[1];
  const bottom = parts[2] ?? top;
  const left = parts[3] ?? right;
  if (Math.abs(toPx(right)) <= 48 && Math.abs(toPx(left)) <= 48) return whole;
  return `margin: ${top} 0 ${bottom} 0;`;
}

function stripLegacyStyles(root: ParentNode) {
  root.querySelectorAll("[style]").forEach((el) => {
    const style = el.getAttribute("style") ?? "";
    const cleaned = style
      .replace(/font-family\s*:\s*[^;]+;?/gi, "")
      .replace(/font-size\s*:\s*[^;]+;?/gi, "")
      .replace(/color\s*:\s*[^;]+;?/gi, "")
      .replace(/text-align\s*:\s*justify;?/gi, "")
      .replace(/margin\s*:\s*([^;]+);?/gi, (whole, value: string) => dropWideSideMargins(whole, value))
      .replace(/^\s*;\s*/g, "")
      .trim();
    if (cleaned) el.setAttribute("style", cleaned);
    else el.removeAttribute("style");
  });
  root.querySelectorAll("font").forEach((el) => {
    const span = el.ownerDocument.createElement("span");
    span.innerHTML = el.innerHTML;
    el.replaceWith(span);
  });
}

/**
 * Puts a page's picture into its figure. The picture usually sits in a <p>/<div> (legacy CKEditor markup) that the
 * figure replaces; a picture saved by the admin editor stands bare at the top level, so it is replaced itself.
 */
function wrapImageInFigure(img: Element, figure: HTMLElement) {
  const container = img.closest("p, div") ?? img;
  container.replaceWith(figure);
  figure.appendChild(img);
}

function normalizeHeroImage(root: ParentNode) {
  const img = root.querySelector("img");
  if (!img) return;

  const figure = img.ownerDocument.createElement("figure");
  figure.className = "cms-hero-figure";
  img.classList.add("cms-hero-image");
  img.removeAttribute("style");
  img.removeAttribute("height");
  img.removeAttribute("width");

  wrapImageInFigure(img, figure);
}

function normalizeStudentTestCover(root: ParentNode) {
  const img = root.querySelector("img");
  if (!img) return;

  const figure = img.ownerDocument.createElement("figure");
  figure.className = "cms-student__cover";
  img.removeAttribute("style");
  img.removeAttribute("height");
  img.removeAttribute("width");
  wrapImageInFigure(img, figure);
}

/** A monograph's cover is a portrait picture: shown at book size (not stretched to the article's full width). */
function normalizeBookCover(root: ParentNode) {
  const img = root.querySelector("img");
  if (!img) return;

  const figure = img.ownerDocument.createElement("figure");
  figure.className = "cms-book-cover";
  img.removeAttribute("style"); // width/height attributes stay: they reserve the space while the picture loads
  wrapImageInFigure(img, figure);
}

function unwrapListParagraphs(root: ParentNode) {
  root.querySelectorAll("li > p").forEach((p) => {
    const li = p.parentElement;
    if (!li) return;
    while (p.firstChild) li.insertBefore(p.firstChild, p);
    p.remove();
  });
}

function fixHorizontalRulesInLists(root: ParentNode) {
  root.querySelectorAll("li").forEach((li) => {
    const hr = li.querySelector(":scope > hr");
    if (!hr) return;

    const tail: Node[] = [];
    let node = hr.nextSibling;
    while (node) {
      const next = node.nextSibling;
      tail.push(node);
      node = next;
    }
    hr.remove();
    tail.forEach((n) => li.removeChild(n));

    if (!li.textContent?.trim()) li.remove();

    const ul = li.closest("ul, ol");
    const anchor = ul ?? li;
    const divider = li.ownerDocument.createElement("div");
    divider.className = "cms-section-divider";
    divider.setAttribute("role", "separator");
    anchor.after(divider);

    const frag = li.ownerDocument.createDocumentFragment();
    tail.forEach((n) => frag.appendChild(n));
    divider.after(frag);
  });

  root.querySelectorAll("hr").forEach((hr) => {
    const divider = hr.ownerDocument.createElement("div");
    divider.className = "cms-section-divider";
    divider.setAttribute("role", "separator");
    hr.replaceWith(divider);
  });
}

function promoteCenteredHeadings(root: ParentNode) {
  let firstTitle = true;
  root.querySelectorAll("p").forEach((p) => {
    if (p.querySelector("img")) return;

    const style = p.getAttribute("style") ?? "";
    const isCenter = /text-align\s*:\s*center/i.test(style);
    // the editors wrapped the bold text in one, two or three font/size <span>s, depending on the toolbar clicks
    const strong = p.querySelector(":scope > strong, :scope span strong");
    if (!isCenter || !strong) return;

    const plain = p.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    const strongText = strong.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    if (!strongText || plain !== strongText) return;

    // the big page-title style only goes to a heading that really opens the text, not to the first one that
    // happens to be found after other content (a heading found only now, through a deeper <span>, would be one)
    let before = p.previousElementSibling;
    let opensText = p.parentElement === p.ownerDocument.body;
    while (opensText && before) {
      const isHeroImage = before.classList.contains("cms-hero-figure");
      if (!isHeroImage && (before.textContent?.trim() || before.querySelector("img"))) opensText = false;
      before = before.previousElementSibling;
    }
    const h2 = p.ownerDocument.createElement("h2");
    h2.className = firstTitle && opensText ? "cms-institute-title" : "cms-section-title";
    h2.innerHTML = strong.innerHTML.trim();
    firstTitle = false;
    p.replaceWith(h2);
  });
}

function promoteDivHeadings(root: ParentNode) {
  root.querySelectorAll("div").forEach((div) => {
    if (div.closest("li")) return; // the line of a list item is the item's text, not a section title
    if (div.querySelector(":scope > div, :scope > ul, :scope > ol, :scope > table")) return;

    const strong = div.querySelector(":scope > strong, :scope > span strong, :scope > a strong");
    if (!strong) return;

    const text = div.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    const strongText = strong.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    const isHeading =
      text === strongText ||
      text === `${strongText}:` ||
      (text.startsWith(strongText) && text.length - strongText.length <= 2);

    if (!isHeading || text.length > 140) return;

    const h2 = div.ownerDocument.createElement("h2");
    h2.className = "cms-section-title";
    h2.innerHTML = strong.innerHTML.replace(/:\s*$/, "").trim();
    div.replaceWith(h2);
  });
}

function promoteSubsectionHeadings(root: ParentNode) {
  root.querySelectorAll("p").forEach((p) => {
    if (p.closest("li")) return;
    const strong = p.querySelector(":scope > strong, :scope > span > strong");
    if (!strong) return;

    const text = p.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    const strongText = strong.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    if (text !== strongText && text !== `${strongText}:`) return;
    if (text.length > 120) return;

    const h3 = p.ownerDocument.createElement("h3");
    h3.className = "cms-subsection-title";
    h3.innerHTML = strong.innerHTML.replace(/:\s*$/, "").trim();
    p.replaceWith(h3);
  });
}

function promoteMissionCallout(root: ParentNode) {
  root.querySelectorAll("p").forEach((p) => {
    const strong = p.querySelector(":scope > strong, :scope > span > strong");
    if (!strong) return;

    const text = p.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    const strongText = strong.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    if (text !== strongText || text.length < 80) return;

    const aside = p.ownerDocument.createElement("aside");
    aside.className = "cms-mission-callout";
    aside.innerHTML = `<p>${strong.innerHTML}</p>`;
    p.replaceWith(aside);
  });
}

function convertBrListsToUl(root: ParentNode) {
  root.querySelectorAll("div, p").forEach((el) => {
    if (el.querySelector(":scope > div, :scope > ul, :scope > ol")) return;
    if (!/<br\s*\/?>/i.test(el.innerHTML)) return;

    const parts = el.innerHTML.split(/<br\s*\/?>/i).map((s) => s.trim()).filter(Boolean);
    const dashParts = parts.filter((part) => part.replace(/<[^>]+>/g, "").trim().startsWith("-"));
    if (dashParts.length < 2) return;

    const ul = el.ownerDocument.createElement("ul");
    ul.className = "cms-feature-list";
    dashParts.forEach((part) => {
      const li = el.ownerDocument.createElement("li");
      li.innerHTML = part.replace(/^-\s*/, "").trim();
      ul.appendChild(li);
    });
    el.replaceWith(ul);
  });
}

function convertDashElementsToLists(root: ParentNode) {
  root.querySelectorAll("div, p").forEach((el) => {
    if (el.closest("ul, ol, aside, figure")) return;
    if (el.querySelector(":scope > div, :scope > ul, :scope > ol, :scope > table, :scope > hr")) return;

    const text = el.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    if (!text.startsWith("-")) return;

    el.setAttribute("data-cms-dash", "1");
    const statMatch = text.match(/^-\s*(.+?)\s-\s*(.+)$/);
    if (statMatch) el.setAttribute("data-cms-stat", "1");
  });

  root.querySelectorAll("*").forEach((parent) => {
    let i = 0;
    while (i < parent.children.length) {
      const child = parent.children[i];
      if (!child.hasAttribute("data-cms-dash")) {
        i++;
        continue;
      }

      const group: Element[] = [];
      let j = i;
      while (j < parent.children.length && parent.children[j].hasAttribute("data-cms-dash")) {
        group.push(parent.children[j]);
        j++;
      }

      const isStat = group.length > 0 && group.every((g) => g.hasAttribute("data-cms-stat"));
      const ul = parent.ownerDocument.createElement("ul");
      ul.className = isStat ? "cms-stat-grid" : "cms-feature-list";

      group.forEach((g) => {
        const li = parent.ownerDocument.createElement("li");
        const raw = g.textContent?.replace(/\u00a0/g, " ").trim().replace(/^-\s*/, "") ?? "";

        if (isStat) {
          const parts = raw.match(/^(.+?)\s-\s*(.+)$/);
          if (parts) {
            li.innerHTML = `<span class="cms-stat-label">${parts[1].trim()}</span><span class="cms-stat-value">${parts[2].trim()}</span>`;
          } else {
            li.textContent = raw;
          }
        } else {
          li.innerHTML = g.innerHTML.replace(/^-\s*/, "").trim();
        }

        ul.appendChild(li);
        g.remove();
      });

      parent.insertBefore(ul, parent.children[i] ?? null);
      i++;
    }
  });
}

function convertNumberedBlocks(root: ParentNode) {
  root.querySelectorAll("div, p").forEach((el) => {
    if (el.closest("ul, ol, aside, figure")) return;
    if (el.querySelector(":scope > div, :scope > ul, :scope > ol")) return;

    const text = el.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    const match = text.match(/^(\d+)\.\s/);
    if (!match) return;

    el.classList.add("cms-dept-card");
    el.setAttribute("data-num", match[1]);
  });
}

function promoteNumberedHeadings(root: ParentNode) {
  root.querySelectorAll("p").forEach((p) => {
    const text = p.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    if (!/^\d+\)\s/.test(text)) return;
    const h3 = p.ownerDocument.createElement("h3");
    h3.className = "cms-subsection-title";
    h3.textContent = text;
    p.replaceWith(h3);
  });
}

function promoteValueHeadings(root: ParentNode) {
  root.querySelectorAll("p").forEach((p) => {
    const strong = p.querySelector(":scope > strong, :scope > span > strong");
    if (!strong || p.children.length > 2) return;

    const plain = p.textContent?.trim() ?? "";
    const strongText = strong.textContent?.trim() ?? "";
    if (plain !== strongText) return;
    if (p.getAttribute("style")?.includes("center")) return;

    const h4 = p.ownerDocument.createElement("h4");
    h4.className = "cms-value-title";
    h4.innerHTML = strong.innerHTML.trim();
    p.replaceWith(h4);
  });
}

function markIntroParagraph(root: ParentNode) {
  const title = root.querySelector(".cms-institute-title");
  const start = title ?? root.querySelector(".cms-hero-figure");
  if (!start) return;

  let next = start.nextElementSibling;
  while (next && (next.classList.contains("cms-section-divider") || next.tagName === "H2")) {
    next = next.nextElementSibling;
  }
  if (next?.tagName === "P") next.classList.add("cms-intro");
}

function markLeadParagraph(root: ParentNode) {
  const firstSection = root.querySelector("h2.cms-section-title");
  if (!firstSection) return;
  const next = firstSection.nextElementSibling;
  if (next?.tagName === "P") next.classList.add("cms-lead");
}

type HistoryDirectorMeta = {
  match: RegExp;
  period: string;
  name: string;
  degree: string;
  role: string;
  lifespan?: string;
  current?: boolean;
};

const RESTRICTED_TEXT_RE =
  /ushbu sahifani ko[''`’]?rish faqat ro[''`’]?yxatdan o[''`’]?tgan/i;

function stripRestrictedNotice(body: HTMLElement) {
  body.querySelectorAll("p, div").forEach((el) => {
    const text = el.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    if (RESTRICTED_TEXT_RE.test(text)) el.remove();
  });
}

/**
 * The conference page keeps its video at the very bottom, after twenty-odd files, and the editors had
 * wrapped it in a link to a PDF (so a click on the player could open that file). Pull the player out
 * of the link and put it first, where a visitor sees it.
 */
function moveVideoToTop(body: HTMLElement) {
  const iframe = body.querySelector("iframe");
  if (!iframe) return;
  const holder = iframe.closest("a")?.parentElement ?? iframe.parentElement;
  const wrapper = body.ownerDocument.createElement("div");
  wrapper.className = "cms-video-embed";
  wrapper.appendChild(iframe);
  body.insertBefore(wrapper, body.firstChild);
  // what is left of the old holder is an empty link and blank space
  if (holder && holder !== body && !holder.textContent?.trim()) holder.remove();
}

function buildCouncilMainLayout(body: HTMLElement) {
  stripRestrictedNotice(body);
  const paragraphs = [...body.querySelectorAll("p")].filter(
    (p) => (p.textContent?.replace(/\u00a0/g, " ").trim().length ?? 0) > 20,
  );

  if (paragraphs.length === 0) return;

  paragraphs[0].classList.add("cms-council-intro");

  const subIdx = paragraphs.findIndex((p) =>
    /kengash faoliyati|vazifalarini hal qilish/i.test(p.textContent ?? ""),
  );
  if (subIdx > 0) {
    const sub = paragraphs[subIdx];
    const h3 = body.ownerDocument.createElement("h3");
    h3.className = "cms-council-subhead";
    h3.textContent = sub.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    sub.replaceWith(h3);
  }

  [...body.querySelectorAll("p")].forEach((p) => {
    if (p.classList.contains("cms-council-intro")) return;
    const text = p.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    if (!text || text.length < 40) {
      p.remove();
      return;
    }

    if (text.includes(";")) {
      const items = text
        .split(";")
        .map((s) => s.trim())
        .filter((s) => s.length > 8);
      if (items.length >= 2) {
        const ul = body.ownerDocument.createElement("ul");
        ul.className = "cms-council-tasks";
        items.forEach((item) => {
          const li = body.ownerDocument.createElement("li");
          li.textContent = item.replace(/\.\s*$/, "");
          ul.appendChild(li);
        });
        p.replaceWith(ul);
        return;
      }
    }

    p.classList.add("cms-council-text");
  });
}

function buildCouncilDecisionsLayout(body: HTMLElement) {
  stripRestrictedNotice(body);
  const lines: string[] = [];
  const seenLines = new Set<string>();

  body.querySelectorAll("p, div").forEach((el) => {
    const text = el.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    if (!text || RESTRICTED_TEXT_RE.test(text)) return;
    text.split(/\n+/).forEach((line) => {
      const t = line.trim();
      if (t.length > 6 && /kengash|bayon|qaror/i.test(t) && !seenLines.has(t)) {
        seenLines.add(t);
        lines.push(t);
      }
    });
    el.remove();
  });

  if (lines.length === 0) return;

  const list = body.ownerDocument.createElement("ul");
  list.className = "cms-council-decisions";

  lines.forEach((line) => {
    const li = body.ownerDocument.createElement("li");
    li.className = "cms-council-decision";
    li.innerHTML = `<span class="cms-council-decision__icon" aria-hidden="true"><i class="ri-file-list-3-line"></i></span><span class="cms-council-decision__text">${escapeHtml(line)}</span>`;
    list.appendChild(li);
  });

  body.appendChild(list);
}

function buildAutoreferatLayout(body: HTMLElement) {
  stripRestrictedNotice(body);
  const lines = collectLinkedLines(body);

  body.innerHTML = "";
  const grid = body.ownerDocument.createElement("div");
  grid.className = "cms-autoreferat-grid";

  let currentHeader = "";
  let pendingAuthor = "";
  let pendingTitle = "";
  let pendingHref = "";
  let lastTopic: HTMLElement | null = null;

  const linkTopic = (topic: HTMLElement | null, href: string) => {
    if (!topic || !href || topic.querySelector("a")) return;
    topic.innerHTML = `<a ${fileLinkAttrs(href)}>${topic.innerHTML}</a>`;
  };

  const flushCard = () => {
    if (!pendingAuthor && !pendingTitle) return;
    const card = body.ownerDocument.createElement("article");
    card.className = "cms-autoreferat-card";
    card.innerHTML = `
      ${currentHeader ? `<p class="cms-autoreferat-card__council">${escapeHtml(currentHeader)}</p>` : ""}
      <h3 class="cms-autoreferat-card__author">${escapeHtml(pendingAuthor)}</h3>
      <p class="cms-autoreferat-card__topic">${escapeHtml(pendingTitle)}</p>
    `;
    lastTopic = card.querySelector<HTMLElement>(".cms-autoreferat-card__topic");
    linkTopic(lastTopic, pendingHref);
    grid.appendChild(card);
    pendingAuthor = "";
    pendingTitle = "";
    pendingHref = "";
  };

  const isHeader = (line: string) =>
    /FARG[''`’]?ONA|ILMIY DARAJALAR|ILMIY KENGASH/i.test(line) && line.length > 40;

  const isAuthor = (line: string) =>
    line.length > 6 &&
    line.length < 80 &&
    line === line.toUpperCase() &&
    /[A-Z]/.test(line) &&
    !isHeader(line);

  lines.forEach(({ text: t, href }) => {
    if (isHeader(t)) {
      flushCard();
      currentHeader = t;
      return;
    }
    if (isAuthor(t)) {
      flushCard();
      pendingAuthor = t;
      pendingHref = href ?? "";
      return;
    }
    if (pendingAuthor && !pendingTitle) {
      pendingTitle = t;
      pendingHref = pendingHref || href || "";
      flushCard();
      return;
    }
    // a link that sits on a line of its own: it belongs to the card being built, or to the one just finished
    if (href) {
      if (pendingAuthor) pendingHref = pendingHref || href;
      else linkTopic(lastTopic, href);
    }
  });

  flushCard();
  body.appendChild(grid);
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const DOCUMENT_HREF_RE = /\.(pdf|docx?|xlsx?|pptx?|zip|rar)(\?|#|$)/i;

type LinkedLine = { text: string; href?: string };

/**
 * The same lines as `body.textContent.split(/\n+/)`, but every line also remembers the document link
 * (pdf/doc/...) that sits on it. The "rebuild from text" layouts below used to read plain text only, which
 * silently dropped every PDF link on those pages (journal archives, dissertation abstracts).
 */
function collectLinkedLines(body: HTMLElement): LinkedLine[] {
  const walker = body.ownerDocument.createTreeWalker(body, NodeFilter.SHOW_TEXT);
  const raw: LinkedLine[] = [{ text: "" }];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const value = (node.nodeValue ?? "").replace(/ /g, " ");
    const anchorHref = node.parentElement?.closest("a[href]")?.getAttribute("href") ?? "";
    const href = DOCUMENT_HREF_RE.test(anchorHref) ? anchorHref : undefined;
    value.split("\n").forEach((part, i) => {
      if (i > 0) raw.push({ text: "" });
      const line = raw[raw.length - 1];
      line.text += part;
      if (href && part.trim() && !line.href) line.href = href;
    });
  }
  const lines: LinkedLine[] = [];
  raw.forEach(({ text, href }) => {
    const clean = text.trim().replace(/\s+/g, " ");
    if (!clean) return;
    const previous = lines[lines.length - 1];
    // a short "PDF" / "Ochish" line that only carries the link belongs to the title line before it
    if (href && clean.length < 12 && previous && !previous.href) {
      previous.href = href;
      return;
    }
    lines.push({ text: clean, href });
  });
  return lines;
}

function fileLinkAttrs(href: string): string {
  return `href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer"`;
}

/** Pages whose layout is rebuilt from text. Their file links must not be turned into document cards first. */
const TEXT_LAYOUT_SLUGS = new Set([
  "institut-ilmiy-kengashi",
  "ilmiy-kengash",
  "avtoreferatlar",
  "tahrir-hayati-kengashi",
  "jcpm-2023",
  "jcpm-2024",
  "jcpm-2025",
]);

export function rebuildsLayoutFromText(slug?: string): boolean {
  return !!slug && TEXT_LAYOUT_SLUGS.has(slug);
}

function buildJournalEditorialLayout(body: HTMLElement) {
  stripRestrictedNotice(body);
  const lines: { role: string; name: string }[] = [];

  body.querySelectorAll("p, div").forEach((el) => {
    const text = el.textContent?.replace(/\u00a0/g, " ").trim() ?? "";
    if (!text || /TAHRIR HAY.?ATI|ILMIY JURNALI/i.test(text) && text.length < 80) return;

    const match = text.match(/^(.{3,40}?):\s*(.+)$/);
    if (match && /muharrir|kotib|tahrir|mas.?ul/i.test(match[1])) {
      lines.push({ role: match[1].trim(), name: match[2].trim() });
      el.remove();
      return;
    }

    if (/Bosh muharrir|Mas.?ul kotib|yordamchisi/i.test(text)) {
      const idx = text.indexOf(":");
      if (idx > 0) {
        lines.push({ role: text.slice(0, idx).trim(), name: text.slice(idx + 1).trim() });
        el.remove();
      }
    }
  });

  body.innerHTML = "";
  const head = body.ownerDocument.createElement("h2");
  head.className = "cms-journal-editorial__title";
  head.textContent = "Ilmiy jurnal tahrir hay'ati";
  body.appendChild(head);

  const grid = body.ownerDocument.createElement("div");
  grid.className = "cms-journal-editorial__grid";

  lines.forEach(({ role, name }) => {
    const card = body.ownerDocument.createElement("article");
    card.className = "cms-journal-editorial__card";
    card.innerHTML = `<p class="cms-journal-editorial__role">${escapeHtml(role)}</p><p class="cms-journal-editorial__name">${escapeHtml(name)}</p>`;
    grid.appendChild(card);
  });

  body.appendChild(grid);
}

function buildJournalArchiveLayout(body: HTMLElement, year: string) {
  stripRestrictedNotice(body);
  const entries = new Map<string, LinkedLine>();

  collectLinkedLines(body).forEach((line) => {
    if (line.text.length < 12) return;
    const key = line.text.toLowerCase();
    const existing = entries.get(key);
    if (!existing) entries.set(key, { ...line });
    else if (!existing.href && line.href) existing.href = line.href;
  });
  const titles = [...entries.values()];

  body.innerHTML = "";
  const head = body.ownerDocument.createElement("div");
  head.className = "cms-journal-archive__head";
  head.innerHTML = `<span class="cms-journal-archive__year">${escapeHtml(year)}</span><span class="cms-journal-archive__count">${titles.length} ${titles.length === 1 ? "maqola" : "maqola"}</span>`;
  body.appendChild(head);

  const list = body.ownerDocument.createElement("ul");
  list.className = "cms-journal-archive__list";

  titles.forEach(({ text, href }, i) => {
    const li = body.ownerDocument.createElement("li");
    li.className = "cms-journal-archive__item";
    const title = href
      ? `<a class="cms-journal-archive__title cms-journal-archive__title--link" ${fileLinkAttrs(href)}>${escapeHtml(text)}</a>`
      : `<span class="cms-journal-archive__title">${escapeHtml(text)}</span>`;
    li.innerHTML = `<span class="cms-journal-archive__num">${i + 1}</span>${title}`;
    list.appendChild(li);
  });

  body.appendChild(list);
}
