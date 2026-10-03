import { useTranslation } from "react-i18next";
import {
  CARD_ACTIONS_CLASS,
  CARD_CLASS,
  CARD_ICON_CLASS,
  CARD_MAIN_CLASS,
  CARD_META_CLASS,
  CARD_TITLE_CLASS,
  fileIconClass,
  PRIMARY_BUTTON_CLASS,
  SECONDARY_BUTTON_CLASS,
} from "./documentCardClasses";

interface DocumentCardProps {
  url: string;
  title: string;
  filename: string;
  fileSize: number;
}

/**
 * "Hxteu8Tx-Sbornik_konferensii_ab12CdE.pdf" -> "Sbornik konferensii": drops the extension and the
 * random upload prefix/suffix, and turns underscores into spaces -- the fallback title for a
 * document that has neither a caption nor a title of its own.
 */
export function humanizeFilename(filename: string): string {
  const base = filename.replace(/\.[A-Za-z0-9]{2,5}$/, "");
  const cleaned = base
    .replace(/^[A-Za-z0-9]{8}-/, "")
    .replace(/_[A-Za-z0-9]{7}(?=\.|$)/, "")
    .replace(/[_\s]+/g, " ")
    .trim();
  return cleaned || filename;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * A downloadable file shown as a card -- name, type and size, plus "open in the browser" and
 * "download" -- instead of one bare button. Deliberately no embedded viewer: a 9 MB PDF in an
 * <iframe> loads in full on page open (slow, hurts the Lighthouse score) and phones only show its
 * first page anyway. The buttons carry `cms-download-btn` so the article link styling skips them.
 */
export default function DocumentCard({ url, title, filename, fileSize }: DocumentCardProps) {
  const { t } = useTranslation();
  const extension = (filename.split(".").pop() || "file").toUpperCase();
  const meta = [extension, fileSize > 0 ? formatFileSize(fileSize) : ""].filter(Boolean).join(" · ");

  return (
    <div className={CARD_CLASS}>
      <div className={CARD_MAIN_CLASS}>
        <span className={CARD_ICON_CLASS} aria-hidden="true">
          <i className={fileIconClass(extension)} />
        </span>
        <span className="min-w-0">
          <span className={CARD_TITLE_CLASS}>{title}</span>
          <span className={CARD_META_CLASS}>{meta}</span>
        </span>
      </div>
      <div className={CARD_ACTIONS_CLASS}>
        <a href={url} target="_blank" rel="noopener noreferrer" className={PRIMARY_BUTTON_CLASS}>
          <i className="ri-external-link-line" aria-hidden="true" />
          {t("document.open")}
        </a>
        <a href={url} download target="_blank" rel="noopener noreferrer" className={SECONDARY_BUTTON_CLASS}>
          <i className="ri-download-2-line" aria-hidden="true" />
          {t("document.download")}
        </a>
      </div>
    </div>
  );
}
