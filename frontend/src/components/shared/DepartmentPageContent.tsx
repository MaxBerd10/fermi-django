import ArticleBody from "./ArticleBody";
import { useState } from "react";
import "@/styles/department-content.css";
import { useTranslation } from "react-i18next";
import type { DepartmentDetail, Leader } from "@/types/content";
import LeaderProfileCard from "@/components/shared/LeaderProfileCard";
import DepartmentArticle from "./DepartmentArticle";

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
  const [headOpen, setHeadOpen] = useState(false);

  const hasContent = department.blocks.length > 0;
  // "Institut tarixi" is stored as a department record but is a page of the "Institut haqida" section: it
  // gets no "Kafedralar" banner and no "Kafedra haqida" heading.
  const isHistory = slug === "institut-tarixi";

  const ordered = [...department.blocks].sort((a, b) => a.order - b.order);
  const article = isHistory ? (
    <article className="page-card px-5 py-4 md:px-7 md:py-5 lg:px-8 lg:py-6 cms-article cms-article--rich space-y-4 article-body">
      <ArticleBody blocks={ordered} />
    </article>
  ) : (
    <div className="academic-page__article department-page__article cms-article cms-article--rich cms-article--menu-section cms-article--kafedra space-y-4">
      <DepartmentArticle key={department.id} blocks={ordered} />
    </div>
  );

  return (
    <div className="academic-page">
      {isFallback && !isHistory && (
        <p className="academic-intro__note">
          <i className="ri-information-line" aria-hidden="true" /> {t("department.fallbackNote")}
        </p>
      )}

      {head && (
        <section className="department-page__head" aria-labelledby="department-head-heading">
          <h2 id="department-head-heading" className="academic-page__title">
            {t("department.headTitle")}
          </h2>
          <LeaderProfileCard
            key={`${head.id}:${head.photo ?? ""}`}
            roleLabel={t("department.headTitle")}
            leader={head}
            open={headOpen}
            onToggle={() => setHeadOpen((v) => !v)}
          />
        </section>
      )}

      {hasContent ? (
        <section className="department-page__about" aria-labelledby="department-about-heading">
          {isHistory ? (
            <h2 id="department-about-heading" className="sr-only">
              {department.title}
            </h2>
          ) : (
            <h2 id="department-about-heading" className="academic-page__title">
              {t("department.aboutTitle")}
            </h2>
          )}
          {article}
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
