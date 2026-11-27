import { useTranslation } from "react-i18next";
import DocumentCard from "./DocumentCard";
import {
  CARD_ACTIONS_CLASS,
  CARD_CLASS,
  CARD_ICON_CLASS,
  CARD_MAIN_CLASS,
  CARD_META_CLASS,
  CARD_TITLE_CLASS,
  PRIMARY_BUTTON_CLASS,
} from "./documentCardClasses";
import type { LoneFileLink } from "@/lib/loneFileLink";

/** The file name in an address ("%D0%A3%D0%9F-27.pdf" -> "УП-27.pdf"), for the card's type label. */
function fileNameOf(href: string, extension: string): string {
  const last = href.split(/[?#]/)[0].split("/").pop() || "";
  try {
    return decodeURIComponent(last) || `file.${extension}`;
  } catch {
    return last || `file.${extension}`;
  }
}

/**
 * A block that is one file link, shown as the site's file card. A file (pdf, docx, ...) is a DocumentCard (its size is not known from the text, so none is shown);
 * a link to a national legal portal (lex.uz, dd.gov.uz) is the same card with the portal's name as its type and one "open" button, since there is nothing to download.
 */
export default function FileLinkCard({ link }: { link: LoneFileLink }) {
  const { t } = useTranslation();
  if (/^(?:lex\.uz|dd\.gov\.uz)$/i.test(link.extension)) {
    return (
      <div className={CARD_CLASS} data-file-card="">
        <div className={CARD_MAIN_CLASS}>
          <span className={CARD_ICON_CLASS} aria-hidden="true">
            <i className="ri-government-line" />
          </span>
          <span className="min-w-0">
            <span className={CARD_TITLE_CLASS}>{link.title}</span>
            <span className={CARD_META_CLASS}>{link.extension.toUpperCase()}</span>
          </span>
        </div>
        <div className={CARD_ACTIONS_CLASS}>
          <a href={link.href} target="_blank" rel="noopener noreferrer" className={PRIMARY_BUTTON_CLASS}>
            <i className="ri-external-link-line" aria-hidden="true" />
            {t("document.open")}
          </a>
        </div>
      </div>
    );
  }
  return <DocumentCard url={link.href} title={link.title} filename={fileNameOf(link.href, link.extension)} fileSize={0} />;
}
