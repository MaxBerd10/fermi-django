import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import RichContent from "@/components/shared/RichContent";
import { convertFileLinkParagraphs } from "@/lib/fileLinkCards";

/** A raw_html block, with any "file on its own line" link turned into a document card first. */
export default function RawHtmlBlock({ html, slug, className }: { html: string; slug?: string; className: string }) {
  const { t } = useTranslation();
  const openLabel = t("document.open");
  const withCards = useMemo(() => convertFileLinkParagraphs(html, openLabel), [html, openLabel]);
  return <RichContent html={withCards} className={className} slug={slug} />;
}
