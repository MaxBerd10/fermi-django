export type TextPiece = { text: string; href?: string; external?: boolean };

/**
 * `[label](https://address)` or `[label](/path)` inside the site (a link that shows its label), a bare `https://address` and an e-mail address, in this order of preference.
 * Block text is plain text (no markup), so this is how an editor -- or a content script -- makes words a link. An address ends at whitespace;
 * the punctuation after it is not part of it. A labelled address may hold one level of parentheses (a file name such as `a(1).pdf`).
 */
const LINK_RE =
  /\[([^\]\n]+)\]\(((?:https?:\/\/|\/(?!\/))(?:[^\s()]|\([^\s()]*\))+)\)|(https?:\/\/[^\s<>"]*[^\s<>".,;:!?)\]»”’'])|([\w.+-]+@[\w-]+\.[\w.-]*[A-Za-z])/g;

export function splitLinks(text: string): TextPiece[] {
  const pieces: TextPiece[] = [];
  let last = 0;
  for (const match of text.matchAll(LINK_RE)) {
    const start = match.index ?? 0;
    if (start > last) pieces.push({ text: text.slice(last, start) });
    if (match[1] !== undefined) pieces.push({ text: match[1], href: match[2], external: !match[2].startsWith("/") });
    else if (match[3] !== undefined) pieces.push({ text: match[3], href: match[3], external: true });
    else pieces.push({ text: match[4], href: `mailto:${match[4]}`, external: false });
    last = start + match[0].length;
  }
  if (last < text.length || pieces.length === 0) pieces.push({ text: text.slice(last) });
  return pieces;
}
