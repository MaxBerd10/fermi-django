import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import PageHeader from "@/components/shared/PageHeader";
import CatalogBrowser from "@/components/imentor/CatalogBrowser";
import TopicExplorer from "@/components/imentor/TopicExplorer";
import { subjectInfo } from "@/lib/imentorCatalog";
import { usePageMeta } from "@/hooks/usePageMeta";
import { imentorLanguage, languageCount, subjectsInLanguage, type ImentorLanguage } from "@/lib/imentorLanguage";
import { getImentorKeyStats } from "@/api/imentor";
import type { ImentorSubjectStat } from "@/types/imentor";

type Stage = "picking" | "list";

/** a key document holds several clinical cases; `questions_total` counts the cases, `case_count` the documents */
const caseItems = (s: ImentorSubjectStat, lang: ImentorLanguage) => languageCount(s, lang) ?? (s.questions_total || s.case_count || 0);

export default function KeyslarPage() {
  const { t, i18n } = useTranslation();
  usePageMeta(t("nav.keyslar"));
  // the subjects and cases come in the visitor's language (iMentor reports what exists in each language)
  const lang = imentorLanguage(i18n.language);

  const [stage, setStage] = useState<Stage>("picking");
  const [subjects, setSubjects] = useState<ImentorSubjectStat[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [subject, setSubject] = useState<ImentorSubjectStat | null>(null);

  const visibleSubjects = useMemo(() => (subjects ? subjectsInLanguage(subjects, lang) : null), [subjects, lang]);
  const totalCases = visibleSubjects?.reduce((sum, s) => sum + caseItems(s, lang), 0) ?? 0;

  useEffect(() => {
    let cancelled = false;
    getImentorKeyStats(lang)
      .then((data) => {
        if (cancelled) return;
        setSubjects(data);
        // the open subject comes again in the new language (its name and department change with the language)
        setSubject((current) => (current ? data.find((s) => s.subject_code === current.subject_code) ?? current : current));
      })
      .catch(() => {
        if (!cancelled) setError(t("test.loadError"));
      });
    return () => {
      cancelled = true;
    };
  }, [t, lang]);

  function openSubject(s: ImentorSubjectStat) {
    setSubject(s);
    setError(null);
    setStage("list");
  }

  function backToSubjects() {
    setStage("picking");
    setSubject(null);
    setError(null);
  }

  const banner = (
    <div className="relative flex min-h-36 items-center overflow-hidden rounded-[1.35rem] bg-[#0a1158] px-6 py-5 text-white shadow-[0_14px_30px_rgba(10,17,88,0.18)] sm:px-7 sm:py-6 lg:px-10 xl:px-12">
      <div className="absolute -right-8 -top-12 h-32 w-32 rounded-full border border-white/10" aria-hidden />
      <div className="relative grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-5">
        <div className="max-w-3xl">
          <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-secondary-300">
            <i className="ri-stethoscope-line text-sm" />
            {t("keyslar.bannerEyebrow")}
          </span>
          <p className="mt-1.5 font-heading text-[clamp(1.55rem,2.15vw,2.25rem)] font-bold leading-tight">{t("keyslar.bannerTitle")}</p>
          <p className="mt-2 text-sm leading-relaxed text-white/75">{t("keyslar.pickSubjectHint")}</p>
        </div>
        <div className="hidden shrink-0 grid-cols-3 gap-2 lg:grid">
          {/* always shown, so the cards do not appear one after another while the catalog loads */}
          <div className="min-w-24 rounded-2xl border border-white/15 bg-white/10 px-3 py-3 text-center">
            <i className="ri-file-text-line text-lg text-secondary-300" />
            <strong className={`mt-1 block text-xl leading-none ${subjects === null && !error ? "animate-pulse text-white/50" : ""}`}>{visibleSubjects ? visibleSubjects.length : "…"}</strong>
            <span className="mt-1 block text-[10px] text-white/70">{t("keyslar.bannerSubjectsLabel")}</span>
          </div>
          <div className="min-w-24 rounded-2xl border border-white/15 bg-white/10 px-3 py-3 text-center">
            <i className="ri-heart-pulse-line text-lg text-secondary-300" />
            <strong className={`mt-1 block text-xl leading-none ${subjects === null && !error ? "animate-pulse text-white/50" : ""}`}>{visibleSubjects ? totalCases : "…"}</strong>
            <span className="mt-1 block text-[10px] text-white/70">{t("keyslar.bannerCasesLabel")}</span>
          </div>
          <div className="min-w-24 rounded-2xl border border-white/15 bg-white/10 px-3 py-3 text-center">
            <i className="ri-file-search-line text-lg text-secondary-300" />
            <strong className="mt-1 block text-xl leading-none">✓</strong>
            <span className="mt-1 block text-[10px] text-white/70">{t("keyslar.bannerAnswerLabel")}</span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="text-foreground-950">
      <PageHeader title={t("nav.keyslar")} compact aside={banner} />

      <div className="section-container section-pad !pt-2 md:!pt-3">
        {stage === "picking" && (
          <div className="max-w-none mx-auto overflow-hidden">
            {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

            {subjects === null && !error && (
              // tall enough that the footer is below the first screen while the catalog loads, so it does not jump down
              <div className="flex min-h-screen items-start gap-2 pt-2 text-foreground-500 text-sm">
                <i className="ri-loader-4-line animate-spin" />
                {t("test.loading")}
              </div>
            )}

            {subjects && subjects.length === 0 && <p className="text-sm text-foreground-500">{t("keyslar.noContent")}</p>}
            {subjects && subjects.length > 0 && visibleSubjects?.length === 0 && <p className="text-sm text-foreground-500">{t("imentor.noContentInLanguage")}</p>}

            {visibleSubjects && visibleSubjects.length > 0 && (
              <p className="mb-3 flex items-start gap-2 text-sm text-foreground-500">
                <i className="ri-translate-2 mt-0.5 shrink-0" aria-hidden />
                {t("imentor.languageHint")}
              </p>
            )}

            {visibleSubjects && visibleSubjects.length > 0 && (
              <CatalogBrowser
                subjects={visibleSubjects}
                countOf={(s) => caseItems(s, lang)}
                countLabel={(count) => t("keyslar.casesCount", { count })}
                sortByCountLabel={t("keyslar.sortByCases")}
                searchPlaceholder={t("keyslar.searchPlaceholder")}
                noResultsLabel={t("keyslar.noSearchResults")}
                onPick={openSubject}
              />
            )}
          </div>
        )}

        {stage === "list" && subject && (
          <div className="page-card p-5 md:p-6">
            <TopicExplorer
              kind="keys"
              subjectCode={subject.subject_code}
              aside={
                <div>
                  <button type="button" onClick={backToSubjects} className="mb-4 inline-flex items-center gap-1 text-sm font-medium text-foreground-500 hover:text-[#0a1158] cursor-pointer">
                    <i className="ri-arrow-left-line" />
                    {t("keyslar.backToSubjects")}
                  </button>
                  <h2 className="font-heading text-2xl font-bold leading-tight text-foreground-900">{subjectInfo(subject, lang).title}</h2>
                  <p className="mt-2 text-sm text-foreground-500">
                    {subjectInfo(subject, lang).department ? `${subjectInfo(subject, lang).department} · ` : ""}
                    {t("keyslar.casesCount", { count: caseItems(subject, lang) })}
                  </p>
                </div>
              }
            />
          </div>
        )}
      </div>
    </div>
  );
}
