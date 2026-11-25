import { Fragment } from "react";
import { splitLinks } from "@/lib/textLinks";

/**
 * Plain block text with its links made clickable: `[label](https://address)` shows the label, a bare URL or e-mail address shows itself. Paragraph/list blocks
 * store plain text (the editor's link marks are not kept), so an editor who writes "Batafsil: https://fjsti.uz/..." gets a working link on the site without
 * any special markup -- and so does every legacy post that already has one.
 */
export default function LinkifiedText({ text }: { text: string }) {
  if (!text || !/(https?:\/\/|@)/.test(text)) return <>{text}</>;
  return (
    <>
      {splitLinks(text).map((piece, i) =>
        piece.href ? (
          <a key={i} href={piece.href} {...(piece.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}>
            {piece.text}
          </a>
        ) : (
          <Fragment key={i}>{piece.text}</Fragment>
        ),
      )}
    </>
  );
}
