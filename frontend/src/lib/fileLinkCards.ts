import {
  CARD_ACTIONS_CLASS,
  CARD_CLASS,
  CARD_ICON_CLASS,
  CARD_MAIN_CLASS,
  CARD_META_CLASS,
  CARD_TITLE_CLASS,
  fileIconClass,
  PRIMARY_BUTTON_CLASS,
} from "@/blocks/documentCardClasses";

const LEGAL_PORTAL_RE = /^https?:\/\/(?:www\.)?(lex\.uz|dd\.gov\.uz)\//i;
const FILE_PATH_RE = /\.(pdf|docx?|xlsx?|pptx?|zip|rar)$/i;

function fileExtension(href: string): string | null {
  const path = href.split(/[?#]/)[0];
  const match = FILE_PATH_RE.exec(path);
  if (match) return match[1].toLowerCase();
  // legal acts and the year's state programme are linked to the national portals: same card, typed by the portal
  const portal = LEGAL_PORTAL_RE.exec(path);
  return portal ? portal[1].toLowerCase() : null;
}

function normalize(text: string | null): string {
  return (text ?? "").replace(/[\s ​]+/g, " ").trim();
}

/** "Yuklab olish uchun bosing >>>>" style prompts the editors typed in front of a file link. */
const CALL_TO_ACTION_RE = /yuklab|bosing|ko['\u2018\u2019\u02bb`]?rish|\u0441\u043a\u0430\u0447\u0430\u0442\u044c|\u043d\u0430\u0436\u043c\u0438\u0442\u0435|download|click|>>/i;

/** The line is just the link, optionally behind a short "click to download >>>" prompt. */
function isLoneLinkLine(lineText: string, title: string): boolean {
  if (lineText.length <= title.length * 1.15 + 3) return true;
  const rest = lineText.replace(title, "").trim();
  return rest.length <= 60 && rest.length < lineText.length && CALL_TO_ACTION_RE.test(rest);
}

/** Only these show in a browser tab; a .pptx/.docx/.xlsx/.zip just downloads, so its card must say "download". */
function opensInBrowser(extension: string): boolean {
  return extension === "pdf" || extension.includes("."); // "." = a portal link such as lex.uz
}

/**
 * "11.2-ilova" typed as three links ("11." "2" "-ilova") whose targets disagree: pick the one file whose name
 * starts with the label's number ("11.2-ilova.pdf"). Only when exactly one distinct file matches.
 */
function hrefForNumberedLabel(anchors: Element[], label: string): string | null {
  const number = /^\s*(\d+(?:\.\d+)*)/.exec(label)?.[1];
  if (!number) return null;
  const escaped = number.replace(/\./g, "\\.");
  const starts = new RegExp("^" + escaped + "(?:[-_ ]|$)");
  const matches = new Set(
    anchors
      .map((a) => a.getAttribute("href") || "")
      .filter((href) => {
        let name = href.split(/[?#]/)[0].split("/").pop() || "";
        try {
          name = decodeURIComponent(name);
        } catch {
          /* keep the raw name */
        }
        return starts.test(name.replace(/\.[a-z0-9]+$/i, ""));
      }),
  );
  return matches.size === 1 ? Array.from(matches)[0] : null;
}

function buildCard(
  doc: Document,
  href: string,
  title: string,
  extension: string,
  openLabel: string,
  downloadLabel?: string,
): HTMLElement {
  const el = (tag: string, className: string) => {
    const node = doc.createElement(tag);
    node.className = className;
    return node;
  };
  const card = el("div", CARD_CLASS);
  card.setAttribute("data-file-card", "");

  const main = el("div", CARD_MAIN_CLASS);
  const icon = el("span", CARD_ICON_CLASS);
  icon.setAttribute("aria-hidden", "true");
  icon.appendChild(el("i", fileIconClass(extension)));
  const text = el("span", "min-w-0");
  const titleEl = el("span", CARD_TITLE_CLASS);
  titleEl.textContent = title.replace(/^https?:\/\/(www\.)?/i, "").replace(/\s*\((?:yuklab olish|download|\u0441\u043a\u0430\u0447\u0430\u0442\u044c)\)\s*$/i, "") || title;
  const meta = el("span", CARD_META_CLASS);
  meta.textContent = extension.toUpperCase();
  text.append(titleEl, meta);
  main.append(icon, text);

  const actions = el("div", CARD_ACTIONS_CLASS);
  const link = el("a", PRIMARY_BUTTON_CLASS) as HTMLAnchorElement;
  link.href = href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  const download = Boolean(downloadLabel) && !opensInBrowser(extension);
  if (download) link.setAttribute("download", "");
  const linkIcon = el("i", download ? "ri-download-2-line" : "ri-external-link-line");
  linkIcon.setAttribute("aria-hidden", "true");
  link.append(linkIcon, doc.createTextNode(download ? (downloadLabel as string) : openLabel));
  actions.appendChild(link);

  card.append(main, actions);
  return card;
}

/**
 * CMS HTML from the old site often has a file offered as one bare link on its own line
 * ("<p><strong><a href=".../x.pdf">Natijalarni yuklab olish</a></strong></p>"). The editors wrapped
 * these in whatever the toolbar gave them: a paragraph, a <div>, a heading. Each such element --
 * exactly one file link and nothing else of substance -- becomes the same card a document block
 * gets (name, type, open button), so every file reads as a file. A link inside running prose, a
 * list of many files, or an element that also holds an image/video is left exactly as it was.
 */
export function convertFileLinkParagraphs(
  html: string,
  openLabel: string,
  tidyTitle: (title: string) => string = (title) => title,
  downloadLabel?: string,
): string {
  if (!html || typeof DOMParser === "undefined" || !/\.(pdf|docx?|xlsx?|pptx?|zip|rar)|lex\.uz|dd\.gov\.uz/i.test(html)) return html;
  const doc = new DOMParser().parseFromString(html, "text/html");
  let changed = false;

  // A picture that links to a file the page already offers as a text link or a card (a poster of the same PDF):
  // the picture stays, the link around it goes -- one click target for the file, not three.
  const plainFileHrefs = new Set(
    Array.from(doc.body.querySelectorAll("a[href]"))
      .filter((a) => fileExtension(a.getAttribute("href") || "") && !a.querySelector("img") && normalize(a.textContent))
      .map((a) => a.getAttribute("href") as string),
  );
  Array.from(doc.body.querySelectorAll("a[href]")).forEach((a) => {
    const href = a.getAttribute("href") || "";
    if (!fileExtension(href) || !a.querySelector("img") || normalize(a.textContent)) return;
    if (!plainFileHrefs.has(href)) return;
    a.replaceWith(...Array.from(a.childNodes));
    changed = true;
  });

  // A picture and its label inside ONE file link ("<a href=x.pdf><img>BAKALAVR</a>"): the picture stays as a plain
  // picture (no link around it -- one click target per file) and the label becomes the file's card below it.
  doc.body.querySelectorAll("p, div").forEach((block) => {
    if (block.closest("table, blockquote, [data-file-card]") || !block.querySelector("img")) return;
    if (block.querySelector("iframe, video, ul, ol, p, div")) return;
    const labelled = Array.from(block.querySelectorAll("a[href]")).filter(
      (a) => fileExtension(a.getAttribute("href") || "") && a.querySelector("img") && normalize(a.textContent),
    );
    if (labelled.length !== 1) return;
    const anchor = labelled[0];
    const href = anchor.getAttribute("href") || "";
    const rawTitle = normalize(anchor.textContent);
    if (!isLoneLinkLine(normalize(block.textContent), rawTitle)) return;
    const wrap = doc.createElement("div");
    anchor.querySelectorAll("img").forEach((img) => {
      const holder = doc.createElement("p");
      holder.appendChild(img.cloneNode(true));
      wrap.appendChild(holder);
    });
    wrap.appendChild(buildCard(doc, href, tidyTitle(rawTitle), fileExtension(href) || "file", openLabel, downloadLabel));
    block.replaceWith(wrap);
    changed = true;
  });

  // A file-link line inside a list item is fine when the item holds nothing but such lines (the editors put a
  // heading and its files into one <li>, each file in its own <p>): the lines become cards, the item stops
  // being a boxed bullet. An item with real text, or a link inside prose, stays as it was.
  const fileLineItems = new Map<Element, boolean>();
  const holdsOnlyFileLines = (li: Element) => {
    const anchors = Array.from(li.querySelectorAll("a[href]")).filter(
      (a) => fileExtension(a.getAttribute("href") || "") && normalize(a.textContent),
    );
    const squash = (text: string | null) => normalize(text).replace(/\s+/g, "");
    return anchors.length > 0 && squash(li.textContent) === squash(anchors.map((a) => a.textContent).join(""));
  };

  doc.body.querySelectorAll("p, div, h1, h2, h3, h4, h5, h6").forEach((block) => {
    if (!block.isConnected) return; // already swallowed by an outer element that was turned into a card
    if (block.closest("table, blockquote, [data-file-card]")) return; // a card built by an earlier pass is final
    const listItem = block.closest("li");
    if (listItem) {
      // judged once per item, before its first line turns into a card (a card's own text would fail the test)
      if (!fileLineItems.has(listItem)) fileLineItems.set(listItem, holdsOnlyFileLines(listItem));
      if (block.parentElement !== listItem || !fileLineItems.get(listItem)) return;
    }
    if (block.querySelector("img, iframe, video")) return;
    // an anchor with no visible text (an editor's stray "&nbsp;" link, sometimes pointing at a different file) is not a link
    const fileAnchors = Array.from(block.querySelectorAll("a[href]")).filter(
      (a) => fileExtension(a.getAttribute("href") || "") && normalize(a.textContent),
    );
    // one file, possibly cut into several <a> pieces by the editor ("20" + "24/2025 o'quv yili...")
    if (!fileAnchors.length) return;
    const rawTitle = normalize(fileAnchors.map((a) => a.textContent).join(""));
    let href = fileAnchors[0].getAttribute("href") || "";
    if (fileAnchors.some((a) => a.getAttribute("href") !== href)) {
      // pieces pointing at different files: "11." + "2" + "-ilova" where the tail was pasted with the link of annex 1.
      // The label's own number says which file it is.
      const byNumber = hrefForNumberedLabel(fileAnchors, rawTitle);
      if (!byNumber) return;
      href = byNumber;
    }
    if (!rawTitle || !isLoneLinkLine(normalize(block.textContent), rawTitle)) return;
    const title = tidyTitle(rawTitle);
    block.replaceWith(buildCard(doc, href, title, fileExtension(href) || "file", openLabel, downloadLabel));
    listItem?.classList.add("cms-li-cards");
    changed = true;
  });

  // A title link left loose inside a <div> that also holds other blocks (<div><span><a>Title</a></span><div>..</div></div>):
  // lift the link's own inline wrapper out as a card, but only when nothing but blocks sits beside it.
  const INLINE = new Set(["SPAN", "STRONG", "B", "EM", "I", "U", "FONT"]);
  const isBlockish = (node: Node) =>
    node.nodeType === Node.ELEMENT_NODE && !INLINE.has((node as Element).tagName) && (node as Element).tagName !== "A";
  Array.from(doc.body.querySelectorAll("a[href]")).forEach((anchor) => {
    const href = anchor.getAttribute("href") || "";
    const extension = fileExtension(href);
    if (!extension || !anchor.isConnected || anchor.classList.contains("cms-download-btn")) return;
    if (anchor.closest("table, ul, ol, blockquote, p, li, h1, h2, h3, h4, h5, h6, [data-file-card]")) return;
    if (anchor.querySelector("img, iframe, video")) return;
    const title = normalize(anchor.textContent);
    if (!title) return;
    let wrapper: Element = anchor;
    while (
      wrapper.parentElement &&
      INLINE.has(wrapper.parentElement.tagName) &&
      normalize(wrapper.parentElement.textContent) === title
    ) {
      wrapper = wrapper.parentElement;
    }
    const parent = wrapper.parentElement;
    if (!parent) return;
    const loneInline = Array.from(parent.childNodes).every(
      (node) => node === wrapper || isBlockish(node) || (node.nodeType === Node.TEXT_NODE && !node.textContent?.trim()),
    );
    if (!loneInline) return;
    wrapper.replaceWith(buildCard(doc, href, tidyTitle(title), extension, openLabel, downloadLabel));
    changed = true;
  });
  // A paragraph of text that ends with the file link on a line of its own ("explanation<br><a>Fakultetning
  // nizomi (yuklab olish)</a>"): the link line moves out of the paragraph into a card right below it. The
  // <br> may sit inside the editor's font <span>s, so the part after it is taken as a range, not as siblings.
  Array.from(doc.body.querySelectorAll("p")).forEach((p) => {
    if (!p.isConnected || p.closest("table, ul, ol, blockquote, [data-file-card]")) return;
    if (p.querySelector("img, iframe, video")) return;
    const lastBr = Array.from(p.querySelectorAll("br")).pop();
    if (!lastBr) return;
    const tailRange = doc.createRange();
    tailRange.setStartAfter(lastBr);
    tailRange.setEnd(p, p.childNodes.length);
    const tail = tailRange.cloneContents();
    const tailAnchors = Array.from(tail.querySelectorAll("a[href]")).filter(
      (a) => fileExtension(a.getAttribute("href") || "") && normalize(a.textContent),
    );
    const href = tailAnchors[0]?.getAttribute("href") || "";
    if (!tailAnchors.length || tailAnchors.some((a) => a.getAttribute("href") !== href)) return;
    const rawTitle = normalize(tailAnchors.map((a) => a.textContent).join(""));
    if (!rawTitle || !isLoneLinkLine(normalize(tail.textContent), rawTitle)) return;
    // there must be real text above the link line, and no different file link in the paragraph
    const aboveRange = doc.createRange();
    aboveRange.setStart(p, 0);
    aboveRange.setEndBefore(lastBr);
    if (!normalize(aboveRange.cloneContents().textContent)) return;
    const otherFile = Array.from(p.querySelectorAll("a[href]")).some(
      (a) => fileExtension(a.getAttribute("href") || "") && normalize(a.textContent) && a.getAttribute("href") !== href,
    );
    if (otherFile) return;
    const card = buildCard(doc, href, tidyTitle(rawTitle), fileExtension(href) || "file", openLabel, downloadLabel);
    tailRange.deleteContents();
    lastBr.remove();
    p.after(card);
    changed = true;
  });

  return changed ? doc.body.innerHTML : html;
}
