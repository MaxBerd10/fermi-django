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

const FILE_PATH_RE = /\.(pdf|docx?|xlsx?|pptx?|zip|rar)$/i;

function fileExtension(href: string): string | null {
  const path = href.split(/[?#]/)[0];
  const match = FILE_PATH_RE.exec(path);
  return match ? match[1].toLowerCase() : null;
}

function normalize(text: string | null): string {
  return (text ?? "").replace(/[\s ​]+/g, " ").trim();
}

function buildCard(doc: Document, href: string, title: string, extension: string, openLabel: string): HTMLElement {
  const el = (tag: string, className: string) => {
    const node = doc.createElement(tag);
    node.className = className;
    return node;
  };
  const card = el("div", CARD_CLASS);

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
    if (fileAnchors.length !== 1) return;
    const anchor = fileAnchors[0];
    const title = normalize(anchor.textContent);
    const href = anchor.getAttribute("href") || "";
    if (!title || normalize(block.textContent).length > title.length * 1.15 + 3) return;
    block.replaceWith(buildCard(doc, href, title, fileExtension(href) || "file", openLabel));
    changed = true;
  });

  return changed ? doc.body.innerHTML : html;
}
