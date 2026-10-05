import { Fragment } from "react";

// A URL ends at whitespace; trailing sentence punctuation / closing brackets are not part of it.
const LINK_RE = /(https?:\/\/[^\s<>"]*[^\s<>".,;:!?)\]»”’']|[\w.+-]+@[\w-]+\.[\w.-]*[A-Za-z])/g;

/**
 * Plain block text with its URLs and e-mail addresses made clickable. Paragraph/list blocks store plain text
 * (the editor's link marks are not kept), so an editor who writes "Batafsil: https://fjsti.uz/..." gets a
 * working link on the site without any special markup -- and so does every legacy post that already has one.
 */
export default function LinkifiedText({ text }: { text: string }) {
  if (!text || !/(https?:\/\/|@)/.test(text)) return <>{text}</>;
  const parts = text.split(LINK_RE);
  return (
    <>
      {parts.map((part, i) => {
        if (i % 2 === 0) return <Fragment key={i}>{part}</Fragment>;
        const isEmail = !part.startsWith("http");
        return (
          <a key={i} href={isEmail ? `mailto:${part}` : part} {...(isEmail ? {} : { target: "_blank", rel: "noopener noreferrer" })}>
            {part}
          </a>
        );
      })}
    </>
  );
}
