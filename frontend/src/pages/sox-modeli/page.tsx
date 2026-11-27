import { useTranslation } from "react-i18next";
import InnerPageLayout from "@/components/shared/InnerPageLayout";
import MenuSectionNav from "@/components/shared/MenuSectionNav";
import { useMenu } from "@/context/MenuContext";
import { resolveMenuSection } from "@/lib/menuSection";
import DocumentCard from "@/blocks/DocumentCard";
import { usePageMeta } from "@/hooks/usePageMeta";

/*
 * "Soʻx modeli" — the institute's 2026 report on the Soʻx district: a short introduction and the report itself as the
 * site's usual file card (open in the browser / download). The texts are site texts (Sayt matnlari, key prefix "sox") in three
 * languages; the report file itself is Uzbek. The figures are the report's own.
 */

const PDF_URL = "/files/Sox-modeli-hisobot-2026.pdf";
const PDF_BYTES = 2275197;

const RESULTS = ["sox.result1", "sox.result2", "sox.result3", "sox.result4", "sox.result5"];

export default function SoxModeliPage() {
  const { t } = useTranslation();
  const { menu } = useMenu();
  const section = resolveMenuSection(menu, undefined, "sox-modeli");

  usePageMeta(t("sox.title"), t("sox.metaDescription"));

  return (
    <InnerPageLayout
      title={t("sox.title")}
      breadcrumb={section?.title ?? t("journal.breadcrumb")}
      sidebar={section && <MenuSectionNav menuId={section.sectionId} currentSlug="sox-modeli" />}
    >
      <article className="page-card cms-article cms-article--rich institute-reference">
        <img
          src="/images/sox/sox-modeli-banner.webp"
          alt={t("sox.bannerAlt")}
          width={1411}
          height={430}
          className="block h-auto w-full rounded-xl"
        />
        <div className="mt-6 space-y-4">
          <p>{t("sox.leadFull")}</p>
          <p>{t("sox.about")}</p>
          <div>
            <p className="font-semibold text-[#0a1158]">{t("sox.resultsTitle")}</p>
            <ul className="mt-2 list-disc space-y-1.5 pl-5">
              {RESULTS.map((key) => (
                <li key={key}>{t(key)}</li>
              ))}
            </ul>
          </div>
          <p>{t("sox.fileNote")}</p>
        </div>

        <DocumentCard url={PDF_URL} title={t("sox.docTitle")} filename="Sox-modeli-hisobot-2026.pdf" fileSize={PDF_BYTES} />
      </article>
    </InnerPageLayout>
  );
}
