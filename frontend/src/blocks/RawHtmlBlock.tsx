import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import RichContent from "@/components/shared/RichContent";
import { convertFileLinkParagraphs } from "@/lib/fileLinkCards";
import { normalizeUzbekApostrophes } from "@/lib/normalizeCmsText";
import { PdfViewer } from "./RoadmapPdfFrame";

/**
 * A raw_html block (what is left of it: embedded videos and maps), with any "file on its own line" link turned into a
 * document card first.
 */
export default function RawHtmlBlock({ html, className, pdfTitle }: {
  html: string;
  className: string;
  pdfTitle?: string;
}) {
  const { t, i18n } = useTranslation();
  const isUzbek = (i18n.resolvedLanguage || i18n.language || "uz").startsWith("uz");
  const openLabel = t("document.open");
  const downloadLabel = t("document.download");
  const withCards = useMemo(
    () => convertFileLinkParagraphs(html, openLabel, isUzbek ? normalizeUzbekApostrophes : undefined, downloadLabel),
    [html, openLabel, downloadLabel, isUzbek],
  );
  const pdfUrl = useMemo(() => {
    if (!pdfTitle || typeof DOMParser === "undefined") return null;
    const document = new DOMParser().parseFromString(withCards, "text/html");
    const cards = document.querySelectorAll("[data-file-card]");
    if (cards.length !== 1) return null;
    const href = cards[0].querySelector("a[href]")?.getAttribute("href");
    if (!href) return null;
    try {
      const url = new URL(href, window.location.origin);
      return /^https?:$/.test(url.protocol) && /\.pdf$/i.test(url.pathname) ? url.href : null;
    } catch {
      return null;
    }
  }, [pdfTitle, withCards]);
  if (pdfUrl && pdfTitle) {
    return (
      <div className="space-y-4">
        <PdfViewer key={pdfUrl} src={pdfUrl} title={pdfTitle} />
        <RichContent html={withCards} className={className} />
      </div>
    );
  }
  return <RichContent html={withCards} className={className} />;
}
