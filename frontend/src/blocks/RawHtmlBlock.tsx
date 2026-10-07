import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import RichContent from "@/components/shared/RichContent";
import { convertFileLinkParagraphs } from "@/lib/fileLinkCards";
import { rebuildsLayoutFromText } from "@/lib/enhanceCmsHtml";
import { normalizeUzbekApostrophes } from "@/lib/normalizeCmsText";

/**
 * A raw_html block, with any "file on its own line" link turned into a document card first -- except on the
 * pages whose layout is rebuilt from the text (journal archives, abstracts, council decisions): those read the
 * original markup, and cards would put "PDF" / "Brauzerda ochish" into their titles.
 */
export default function RawHtmlBlock({ html, slug, className }: { html: string; slug?: string; className: string }) {
  const { t, i18n } = useTranslation();
  const isUzbek = (i18n.resolvedLanguage || i18n.language || "uz").startsWith("uz");
  const openLabel = t("document.open");
  const withCards = useMemo(
    () => (rebuildsLayoutFromText(slug) ? html : convertFileLinkParagraphs(html, openLabel, isUzbek ? normalizeUzbekApostrophes : undefined)),
    [html, openLabel, slug, isUzbek],
  );
  return <RichContent html={withCards} className={className} slug={slug} />;
}
