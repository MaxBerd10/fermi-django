import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getAdmissionResults, getAdmissionResultsPage } from "@/api/admissionResults";
import type { ResultCategory, ResultsPageInfo } from "@/types/content";
import PageHeader from "@/components/shared/PageHeader";
import { LoadingState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { Reveal } from "@/components/Animation";

export default function AdmissionResultsPage() {
  const { t } = useTranslation();
  const [categories, setCategories] = useState<ResultCategory[]>([]);
  const [page, setPage] = useState<ResultsPageInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getAdmissionResults(), getAdmissionResultsPage()])
      .then(([cats, pageInfo]) => {
        setCategories(cats);
        setPage(pageInfo);
      })
      .finally(() => setLoading(false));
  }, []);

  const title = page?.heading || t("admissionResults.fallbackTitle");
  usePageMeta(title);

  const fileCount = categories.reduce((sum, c) => sum + c.files.length, 0);

  return (
    <div>
      <PageHeader title={title} description={page?.intro} />

      <section className="section-pad bg-transparent pb-16 md:pb-20">
        <div className="section-container">
          {loading ? (
            <LoadingState />
          ) : (
            <>
              {page?.announcement && (
                <Reveal>
                  <div className="relative overflow-hidden rounded-2xl bg-primary-800 text-white px-5 py-6 sm:px-7 sm:py-7 mb-8">
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                      <div className="max-w-2xl">
                        <div className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-white/80 mb-3">
                          <i className="ri-shield-check-line" /> {t("admissionResults.noticeLabel")}
                        </div>
                        <p className="text-sm sm:text-base leading-relaxed whitespace-pre-line text-white/90">
                          {page.announcement}
                        </p>
                      </div>
                      {fileCount > 0 && (
                        <div className="shrink-0 inline-flex items-center gap-2 rounded-xl bg-white/10 px-3.5 py-2.5 text-sm font-semibold">
                          <i className="ri-file-pdf-2-line text-lg" />
                          {t("admissionResults.fileCount", { count: fileCount })}
                        </div>
                      )}
                    </div>
                  </div>
                </Reveal>
              )}

              {categories.length === 0 ? (
                <Reveal>
                  <p className="text-foreground-500">{t("admissionResults.empty")}</p>
                </Reveal>
              ) : (
                <>
                  <p className="text-sm text-foreground-500 mb-5">{t("admissionResults.personalUseNotice")}</p>
                  <div className="space-y-6">
                    {categories.map((c, ci) => (
                      <Reveal key={c.id} delay={ci * 80}>
                        <div>
                          <h2 className="font-heading text-xl md:text-2xl font-bold text-foreground-950 mb-3">
                            {c.title}
                          </h2>
                          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 items-stretch">
                            {c.files.map((f, fi) => (
                              <Reveal key={f.id} delay={ci * 80 + fi * 50} className="h-full">
                                <a
                                  href={f.file}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="group flex h-full items-center gap-3 p-3.5 page-card hover:border-primary-300 hover:shadow-lg transition-all duration-300 cursor-pointer"
                                >
                                  <div className="w-10 h-10 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center flex-shrink-0 group-hover:bg-primary-500 group-hover:text-background-50 transition-colors duration-300">
                                    <i className="ri-file-pdf-2-line w-5 h-5 flex items-center justify-center text-lg" />
                                  </div>
                                  <span className="text-sm font-medium text-foreground-800 group-hover:text-primary-700 transition-colors">
                                    {f.title}
                                  </span>
                                </a>
                              </Reveal>
                            ))}
                          </div>
                        </div>
                      </Reveal>
                    ))}
                  </div>
                </>
              )}

              <div className="mt-10">
                <Link
                  to="/qabul"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-primary-700 hover:text-primary-800 transition-colors"
                >
                  <i className="ri-arrow-left-line" /> {t("admissionResults.backToAdmission")}
                </Link>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
