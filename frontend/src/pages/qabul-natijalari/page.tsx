import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getAdmissionResults, getAdmissionResultsPage } from "@/api/admissionResults";
import type { ResultCategory, ResultsPageInfo } from "@/types/content";
import PageHeader from "@/components/shared/PageHeader";
import { LoadingState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { Reveal } from "@/components/Animation";

const CATEGORY_ICONS: Record<string, string> = {
  Farmatsiya: "ri-capsule-line",
  Stomatologiya: "ri-heart-pulse-line",
  Pediatriya: "ri-parent-line",
  "Davolash ishi": "ri-stethoscope-line",
  Davolash: "ri-hospital-line",
  "Tibbiy profilaktika ishi": "ri-shield-cross-line",
};
const DEFAULT_CATEGORY_ICON = "ri-file-list-3-line";

function fileBadge(title: string): { label: string; bg: string; color: string } {
  const lower = title.toLowerCase();
  if (lower.includes("o'zbek") || lower.includes("o‘zbek") || lower.includes("uzbek")) {
    return { label: "O'Z", bg: "#eaf7ef", color: "#23744c" };
  }
  if (lower.includes("rus")) {
    return { label: "RU", bg: "#f3efff", color: "#5b35a4" };
  }
  return { label: "PDF", bg: "#fff7de", color: "#8a6200" };
}

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
  // "2026/2027" pulled straight out of the admin-entered heading rather than
  // a hardcoded/translated string, so this doesn't need a code change (or go
  // stale) every new admission cycle.
  const yearBadge = title.match(/\d{4}\/\d{4}/)?.[0];

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
                  <div className="relative overflow-hidden rounded-2xl bg-[#0a1158] text-white px-5 py-6 sm:px-7 sm:py-7 mb-8">
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                      <div className="max-w-2xl">
                        <div className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-white/80 mb-3">
                          <i className="ri-shield-check-line text-[#ffd600]" /> {t("admissionResults.noticeLabel")}
                        </div>
                        <p className="text-sm sm:text-base leading-relaxed whitespace-pre-line text-white/90">
                          {page.announcement}
                        </p>
                      </div>
                      {fileCount > 0 && (
                        <div className="shrink-0 inline-flex items-center gap-2 rounded-xl bg-white/10 px-3.5 py-2.5 text-sm font-semibold">
                          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#ffd600] text-[#0a1158]">
                            <i className="ri-file-pdf-2-line text-lg" />
                          </span>
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
                  <Reveal>
                    <div className="mb-4 flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
                      <div>
                        {yearBadge && <span className="section-eyebrow">{yearBadge}</span>}
                        <h2 className="mt-1 font-heading text-xl font-bold tracking-tight text-foreground-950 sm:text-2xl">
                          {title}
                        </h2>
                      </div>
                      <p className="text-sm text-foreground-500">{t("admissionResults.personalUseNotice")}</p>
                    </div>
                  </Reveal>

                  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {categories.map((c, ci) => (
                      <Reveal key={c.id} delay={ci * 60} className="h-full">
                        <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-background-200 bg-background-50 shadow-[0_8px_24px_rgba(20,32,86,0.05)] transition-shadow hover:shadow-[0_14px_30px_rgba(20,32,86,0.10)]">
                          <div className="flex items-center gap-3 border-b border-background-100 bg-background-100/60 px-4 py-4">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-50 text-lg text-primary-700">
                              <i className={CATEGORY_ICONS[c.title] ?? DEFAULT_CATEGORY_ICON} />
                            </div>
                            <h3 className="font-heading text-base font-bold text-foreground-950">{c.title}</h3>
                          </div>
                          <div className="divide-y divide-background-100">
                            {c.files.map((f) => {
                              const badge = fileBadge(f.title);
                              return (
                                <div key={f.id} className="flex items-center gap-3 px-4 py-3">
                                  <span
                                    className="inline-flex min-w-9 justify-center rounded-md px-2 py-1 text-[10px] font-extrabold tracking-wide"
                                    style={{ backgroundColor: badge.bg, color: badge.color }}
                                  >
                                    {badge.label}
                                  </span>
                                  <span className="min-w-0 flex-1 text-sm font-medium text-foreground-800">{f.title}</span>
                                  <a
                                    href={f.file}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex h-9 shrink-0 items-center gap-1 rounded-lg bg-[#0a1158] px-3 text-xs font-semibold text-white transition-colors hover:bg-[#060a3d] focus:outline-none focus:ring-2 focus:ring-[#ffd600] focus:ring-offset-2"
                                  >
                                    <i className="ri-external-link-line" /> {t("admissionResults.openPdf")}
                                  </a>
                                </div>
                              );
                            })}
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
