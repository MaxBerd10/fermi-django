import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { DepartmentDetail, Leader } from "@/types/content";
import DepartmentHero from "@/components/shared/DepartmentHero";
import DepartmentHeadCard from "@/components/shared/DepartmentHeadCard";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import { getDepartmentTheme } from "@/lib/departmentSection";

export default function DepartmentPageContent({
  department,
  slug,
  head,
  isFallback,
}: {
  department: DepartmentDetail;
  slug: string;
  head: Leader | null;
  isFallback?: boolean;
}) {
  const { t } = useTranslation();
  const theme = getDepartmentTheme(slug);
  const [headOpen, setHeadOpen] = useState(false);

  const hasContent = department.blocks.length > 0;

  return (
    <div className={`department-page department-page--${theme}`}>
      <DepartmentHero
        title={department.title}
        logoUrl={department.img}
        theme={theme}
        isFallback={isFallback}
      />

      {head && (
        <section className="department-page__head" aria-labelledby="department-head-heading">
          <h2 id="department-head-heading" className="department-page__section-title">
            {t("department.headTitle")}
          </h2>
          <DepartmentHeadCard
            leader={head}
            open={headOpen}
            onToggle={() => setHeadOpen((v) => !v)}
          />
        </section>
      )}

      {hasContent ? (
        <section className="department-page__about" aria-labelledby="department-about-heading">
          <h2 id="department-about-heading" className="department-page__section-title">
            {t("department.aboutTitle")}
          </h2>
          <div className="department-page__article cms-article cms-article--rich cms-article--menu-section cms-article--kafedra space-y-4">
            {department.blocks
              .slice()
              .sort((a, b) => a.order - b.order)
              .map((block) => (
                <BlockRenderer key={block.id} block={block} />
              ))}
          </div>
        </section>
      ) : (
        !head && (
          <div className="department-page__empty page-card p-6 text-center">
            <i className="ri-file-list-3-line text-3xl text-slate-300" aria-hidden />
            <p className="mt-3 text-sm text-slate-500">{t("department.emptyContent")}</p>
          </div>
        )
      )}
    </div>
  );
}
