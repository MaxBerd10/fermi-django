import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import PageHeader from "@/components/shared/PageHeader";
import { usePageMeta } from "@/hooks/usePageMeta";
import { getImentorKeyStats, getImentorCaseScenarios } from "@/api/imentor";
import type { ImentorSubjectStat, ImentorCaseScenario } from "@/types/imentor";

type Stage = "picking" | "loading" | "list";

const SUBJECT_ICONS = ["ri-file-list-3-line", "ri-first-aid-kit-line", "ri-heart-pulse-line", "ri-mental-health-line", "ri-syringe-line", "ri-hospital-line"];

export default function KeyslarPage() {
  const { t } = useTranslation();
  usePageMeta(t("nav.keyslar"));

  const [stage, setStage] = useState<Stage>("picking");
  const [subjects, setSubjects] = useState<ImentorSubjectStat[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [subject, setSubject] = useState<ImentorSubjectStat | null>(null);
  const [cases, setCases] = useState<ImentorCaseScenario[]>([]);
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState<"cases" | "alpha">("cases");

  const filteredSubjects = subjects
    ?.filter((s) => {
      const q = query.trim().toLowerCase();
      if (!q) return true;
      return s.subject_name.toLowerCase().includes(q) || (s.department_name || "").toLowerCase().includes(q);
    })
    .sort((a, b) =>
      sortBy === "alpha" ? a.subject_name.localeCompare(b.subject_name) : (b.case_count || 0) - (a.case_count || 0),
    );

  const totalCases = subjects?.reduce((sum, s) => sum + (s.case_count || 0), 0) ?? 0;

  useEffect(() => {
    let cancelled = false;
    getImentorKeyStats()
      .then((data) => {
        if (!cancelled) setSubjects(data);
      })
      .catch(() => {
        if (!cancelled) setError(t("test.loadError"));
      });
    return () => {
      cancelled = true;
    };
  }, [t]);

  function openSubject(s: ImentorSubjectStat) {
    setSubject(s);
    setStage("loading");
    setError(null);
    getImentorCaseScenarios({ subjectCode: s.subject_code, count: 50 })
      .then((data) => {
        if (data.results.length === 0) {
          setError(t("keyslar.noContent"));
          setStage("picking");
          return;
        }
        setCases(data.results);
        setOpenIndex(null);
        setStage("list");
      })
      .catch(() => {
        setError(t("test.loadError"));
        setStage("picking");
      });
  }

  function backToSubjects() {
    setStage("picking");
    setSubject(null);
    setCases([]);
    setError(null);
  }

  const banner = (
    <div className="bg-primary-950 text-white p-4 md:p-5 rounded-2xl relative overflow-hidden flex flex-wrap items-center justify-between gap-4 w-full">
      <div className="relative z-10 min-w-0">
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10 text-secondary-300 text-[11px] font-bold uppercase tracking-[0.1em] mb-2.5">
          <i className="ri-hexagon-line" />
          {t("keyslar.bannerEyebrow")}
        </span>
        <h2 className="font-heading text-lg md:text-xl font-bold text-white leading-snug">{t("keyslar.bannerTitle")}</h2>
        <p className="mt-1 text-xs md:text-sm text-white/70">{t("keyslar.pickSubjectHint")}</p>
      </div>
      <div className="relative z-10 flex items-center gap-2 flex-shrink-0 flex-wrap">
        {subjects && subjects.length > 0 && (
          <div className="bg-white/10 rounded-xl px-3 py-2 min-w-[84px]">
            <p className="font-heading text-lg font-bold text-white leading-none">{subjects.length}</p>
            <p className="text-[11px] text-white/60 mt-1">{t("keyslar.bannerSubjectsLabel")}</p>
          </div>
        )}
        {totalCases > 0 && (
          <div className="bg-white/10 rounded-xl px-3 py-2 min-w-[84px]">
            <p className="font-heading text-lg font-bold text-white leading-none">{totalCases}</p>
            <p className="text-[11px] text-white/60 mt-1">{t("keyslar.bannerCasesLabel")}</p>
          </div>
        )}
        <div className="bg-white/10 rounded-xl px-3 py-2 min-w-[84px]">
          <p className="font-heading text-lg font-bold text-white leading-none">
            <i className="ri-check-line" />
          </p>
          <p className="text-[11px] text-white/60 mt-1">{t("keyslar.bannerAnswerLabel")}</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="text-foreground-950">
      <PageHeader title={t("nav.keyslar")} compact aside={banner} />

      <div className="section-container section-pad">
        <div className="page-card p-5 md:p-6">
          {stage === "picking" && (
            <>
              {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

              {subjects === null && !error && (
                <div className="flex items-center gap-2 text-foreground-500 text-sm">
                  <i className="ri-loader-4-line animate-spin" />
                  {t("test.loading")}
                </div>
              )}

              {subjects && subjects.length === 0 && <p className="text-sm text-foreground-500">{t("keyslar.noContent")}</p>}

              {subjects && subjects.length > 0 && (
                <>
                  <div className="flex flex-wrap items-center gap-2.5 mb-3">
                    <div className="relative flex-1 min-w-[220px]">
                      <i className="ri-search-line absolute left-3.5 top-1/2 -translate-y-1/2 text-foreground-400" />
                      <input
                        type="search"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder={t("keyslar.searchPlaceholder")}
                        className="w-full h-10 pl-9 pr-3 rounded-xl border border-[#e5e5e5] bg-white text-sm focus:outline-none focus:border-primary-500"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => setSortBy("cases")}
                      className={`h-10 px-3.5 rounded-xl border text-sm font-medium cursor-pointer transition-colors whitespace-nowrap ${
                        sortBy === "cases"
                          ? "bg-primary-950 border-primary-950 text-white"
                          : "border-[#e5e5e5] text-foreground-600 hover:border-primary-300"
                      }`}
                    >
                      <i className="ri-bar-chart-2-line mr-1" />
                      {t("keyslar.sortByCases")}
                    </button>
                    <button
                      type="button"
                      onClick={() => setSortBy("alpha")}
                      className={`h-10 px-3.5 rounded-xl border text-sm font-medium cursor-pointer transition-colors whitespace-nowrap ${
                        sortBy === "alpha"
                          ? "bg-primary-950 border-primary-950 text-white"
                          : "border-[#e5e5e5] text-foreground-600 hover:border-primary-300"
                      }`}
                    >
                      <i className="ri-sort-asc mr-1" />
                      {t("keyslar.sortByAlpha")}
                    </button>
                  </div>

                  <p className="text-xs text-foreground-500 mb-3">
                    {t("keyslar.resultsCount", { count: filteredSubjects?.length ?? 0, total: subjects.length })}
                  </p>

                  {filteredSubjects && filteredSubjects.length === 0 && (
                    <p className="text-sm text-foreground-500">{t("keyslar.noSearchResults")}</p>
                  )}

                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                    {filteredSubjects?.map((s, i) => (
                    <button
                      key={s.subject_code}
                      type="button"
                      onClick={() => openSubject(s)}
                      className="group text-left page-card p-4 hover:-translate-y-0.5 hover:shadow-md hover:border-primary-200 transition-all cursor-pointer"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-11 h-11 shrink-0 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center group-hover:bg-primary-600 group-hover:text-white transition-colors">
                          <i className={`${SUBJECT_ICONS[i % SUBJECT_ICONS.length]} text-lg`} />
                        </div>
                        <div className="min-w-0">
                          <div className="font-heading font-semibold text-foreground-900 mb-0.5 leading-snug">{s.subject_name}</div>
                          {s.department_name && <div className="text-xs text-foreground-500 line-clamp-1">{s.department_name}</div>}
                        </div>
                      </div>
                      <div className="flex items-center justify-between mt-3">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary-50 text-primary-700 text-[11px] font-bold">
                          <i className="ri-folder-line" />
                          {t("keyslar.casesCount", { count: s.case_count || 0 })}
                        </span>
                        <i className="ri-arrow-right-line text-foreground-300 group-hover:text-primary-600 group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </button>
                  ))}
                  </div>
                </>
              )}
            </>
          )}

          {stage === "loading" && (
            <div className="flex items-center justify-center gap-2 text-foreground-500 text-sm py-16">
              <i className="ri-loader-4-line animate-spin" />
              {t("test.loading")}
            </div>
          )}

          {stage === "list" && subject && (
            <div className="max-w-3xl mx-auto">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="font-heading font-bold text-foreground-900">{subject.subject_name}</div>
                  <div className="text-xs text-foreground-500">{t("keyslar.casesCount", { count: cases.length })}</div>
                </div>
                <button type="button" onClick={backToSubjects} className="text-xs text-foreground-400 hover:text-primary-700 cursor-pointer whitespace-nowrap">
                  <i className="ri-arrow-left-line mr-0.5" />
                  {t("keyslar.backToSubjects")}
                </button>
              </div>

              <div className="space-y-3">
                {cases.map((c, i) => {
                  const isOpen = openIndex === i;
                  return (
                    <div key={i} className="page-card p-4">
                      <div className="flex items-start gap-3 mb-3">
                        <span className="w-7 h-7 shrink-0 rounded-full bg-primary-50 text-primary-700 flex items-center justify-center text-xs font-bold">
                          {i + 1}
                        </span>
                        <p className="flex-1 text-sm text-foreground-800 leading-relaxed whitespace-pre-line">{c.scenario}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setOpenIndex(isOpen ? null : i)}
                        className="ml-10 text-xs font-semibold text-primary-700 hover:text-primary-900 cursor-pointer inline-flex items-center gap-1"
                      >
                        <i className={`ri-arrow-down-s-line transition-transform ${isOpen ? "rotate-180" : ""}`} />
                        {isOpen ? t("keyslar.hideAnswer") : t("keyslar.viewAnswer")}
                      </button>
                      {isOpen && (
                        <div className="ml-10 mt-3 page-card !bg-primary-50/60 p-3.5 text-sm text-foreground-700 whitespace-pre-line">
                          <span className="font-semibold text-foreground-900">{t("keyslar.answerLabel")}: </span>
                          {c.answer}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
