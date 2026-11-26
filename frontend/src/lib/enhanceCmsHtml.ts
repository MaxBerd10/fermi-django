/**
 * Legacy CKEditor HTML → clean semantic markup for `.cms-article` styling.
 * Runs in the browser (DOMParser); safe no-op during SSR/build.
 */
import { isDeadHref, repairLegacyHref } from "@/lib/legacyLinks";

export type CmsEnhanceOptions = {
  /** The menu's label for the /blog page with this slug, or null when the menu has none. */
  pageTitle?: (slug: string) => string | null;
};

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

  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");
  const body = doc.body;

  stripLegacyStyles(body);
  unwrapBlankLinks(body);
  repairLinks(body);
  markVideoLinks(body);
  if (options?.pageTitle) labelAddressLinks(body, options.pageTitle);

  normalizeHeroImage(body);
  fixHorizontalRulesInLists(body);
  markPageLinkLines(body);
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

  return body.innerHTML;
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
