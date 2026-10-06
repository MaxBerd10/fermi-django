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

function buildCard(doc: Document, href: string, title: string, extension: string, openLabel: string): HTMLElement {
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
  titleEl.textContent = title;
  const meta = el("span", CARD_META_CLASS);
  meta.textContent = extension.toUpperCase();
  text.append(titleEl, meta);
  main.append(icon, text);

  const actions = el("div", CARD_ACTIONS_CLASS);
  const link = el("a", PRIMARY_BUTTON_CLASS) as HTMLAnchorElement;
  link.href = href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  const linkIcon = el("i", "ri-external-link-line");
  linkIcon.setAttribute("aria-hidden", "true");
  link.append(linkIcon, doc.createTextNode(openLabel));
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
export function convertFileLinkParagraphs(html: string, openLabel: string): string {
  if (!html || typeof DOMParser === "undefined" || !/\.(pdf|docx?|xlsx?|pptx?|zip|rar)/i.test(html)) return html;
  const doc = new DOMParser().parseFromString(html, "text/html");
  let changed = false;

  doc.body.querySelectorAll("p, div, h1, h2, h3, h4, h5, h6").forEach((block) => {
    if (!block.isConnected) return; // already swallowed by an outer element that was turned into a card
    if (block.closest("table, ul, ol, blockquote")) return;
    if (block.querySelector("img, iframe, video")) return;
    const fileAnchors = Array.from(block.querySelectorAll("a[href]")).filter((a) =>
      fileExtension(a.getAttribute("href") || ""),
    );
    // one file, possibly cut into several <a> pieces by the editor ("20" + "24/2025 o'quv yili...")
    const href = fileAnchors[0]?.getAttribute("href") || "";
    if (!fileAnchors.length || fileAnchors.some((a) => a.getAttribute("href") !== href)) return;
    const title = normalize(fileAnchors.map((a) => a.textContent).join(""));
    if (!title || !isLoneLinkLine(normalize(block.textContent), title)) return;
    block.replaceWith(buildCard(doc, href, title, fileExtension(href) || "file", openLabel));
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
    wrapper.replaceWith(buildCard(doc, href, title, extension, openLabel));
    changed = true;
  });
  return changed ? doc.body.innerHTML : html;
}
