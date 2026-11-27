import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import RichContent from "@/components/shared/RichContent";
import { convertFileLinkParagraphs } from "@/lib/fileLinkCards";
import { normalizeUzbekApostrophes } from "@/lib/normalizeCmsText";

/**
 * A raw_html block (what is left of it: embedded videos and maps), with any "file on its own line" link turned into a
 * document card first.
 */
export default function RawHtmlBlock({ html, className }: {
  html: string;
  className: string;
}) {
  const { t, i18n } = useTranslation();
  const isUzbek = (i18n.resolvedLanguage || i18n.language || "uz").startsWith("uz");
  const openLabel = t("document.open");
  const downloadLabel = t("document.download");
  const withCards = useMemo(
    () => convertFileLinkParagraphs(html, openLabel, isUzbek ? normalizeUzbekApostrophes : undefined, downloadLabel),
    [html, openLabel, downloadLabel, isUzbek],
  );
  return <RichContent html={withCards} className={className} />;
}
