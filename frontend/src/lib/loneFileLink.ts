import { fileExtension } from "@/lib/fileLinkCards";
import { repairLegacyHref } from "@/lib/legacyLinks";
import { splitLinks } from "@/lib/textLinks";

export interface LoneFileLink {
  /** what the line says (the link's label), shown as the card's title */
  title: string;
  href: string;
  /** "pdf", "docx", ... or the portal name ("lex.uz", "dd.gov.uz") */
  extension: string;
}

/**
 * A block text that is nothing but ONE link to a file ("[Order No. 236](https://fermi.uz/media/x.pdf)") or to a national legal portal
 * (lex.uz): the site shows it as the same card a document block gets (icon, name, type, open / download), not as a text link with a badge.
 * Punctuation after the link ("." ";") is allowed; a link inside running text, two links, or an address that is not a file is not a lone file link.
 */
export function loneFileLink(text: string): LoneFileLink | null {
  if (!text || !/\]\(/.test(text)) return null;
  const pieces = splitLinks(text.trim()).filter((piece) => piece.text.trim() !== "");
  const links = pieces.filter((piece) => piece.href);
  if (links.length !== 1 || pieces.some((piece) => !piece.href && !/^[\s.;:,]*$/.test(piece.text))) return null;
  const [link] = links;
  const href = repairLegacyHref(link.href as string) ?? (link.href as string);
  const extension = fileExtension(href);
  if (!extension) return null;
  const title = link.text.trim();
  return title ? { title, href, extension } : null;
}
