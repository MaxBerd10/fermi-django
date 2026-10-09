import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import PageHeader from "@/components/shared/PageHeader";
import CatalogBrowser from "@/components/imentor/CatalogBrowser";
import TopicExplorer from "@/components/imentor/TopicExplorer";
import { parseSubjectName } from "@/lib/imentorCatalog";
import { usePageMeta } from "@/hooks/usePageMeta";
import { getImentorTestStats, getImentorSampleQuestions } from "@/api/imentor";
import { downloadTestResultPdf } from "@/lib/testResultPdf";
import type { ImentorSubjectStat, ImentorSampleQuestion, ImentorQuestionLang } from "@/types/imentor";

// iMentor answers a random-sample request with 10 to 30 questions
const QUIZ_QUESTION_COUNT = 20;
const OPTION_LETTERS = ["A", "B", "C", "D", "E", "F"];

function pickLang(q: ImentorSampleQuestion, lang: string): ImentorQuestionLang {
  return q.languages[lang] || q.languages[q.available_languages[0]] || Object.values(q.languages)[0];
}

type Stage = "picking" | "loading" | "study" | "quiz" | "result";

export default function TestPage() {
  const { t, i18n } = useTranslation();
  usePageMeta(t("nav.test"));
  const lang = i18n.language?.slice(0, 2) || "uz";

  const [stage, setStage] = useState<Stage>("picking");
  const [subjects, setSubjects] = useState<ImentorSubjectStat[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [subject, setSubject] = useState<ImentorSubjectStat | null>(null);
  const [quizQuestions, setQuizQuestions] = useState<ImentorSampleQuestion[]>([]);
  // set when the quiz was started from one topic of the syllabus instead of the whole subject
  const [quizTopic, setQuizTopic] = useState<{ code: string; title: string } | null>(null);

  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getImentorTestStats()
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
    setError(null);
    setStage("study");
  }

  function startQuiz(topic: { code: string; title: string } | null = null) {
    if (!subject) return;
    setStage("loading");
    setError(null);
    setPdfError(null);
    setQuizTopic(topic);
    getImentorSampleQuestions({ subjectCode: subject.subject_code, topicCode: topic?.code || undefined, count: QUIZ_QUESTION_COUNT })
      .then((data) => {
        if (data.questions.length === 0) {
          setError(t("test.noContent"));
          setStage("study");
          return;
        }
        setQuizQuestions(data.questions);
        setIndex(0);
        setSelected(null);
        setAnswers({});
        setStage("quiz");
      })
      .catch(() => {
        setError(t("test.loadError"));
        setStage("study");
      });
  }

  function selectOption(i: number) {
    if (selected !== null) return;
    setSelected(i);
    setAnswers((prev) => ({ ...prev, [index]: i }));
  }

  function nextQuestion() {
    if (index + 1 < quizQuestions.length) {
      setIndex(index + 1);
      setSelected(answers[index + 1] ?? null);
    } else {
      setStage("result");
    }
  }

  function retry() {
    startQuiz(quizTopic);
  }

  function backToSubjects() {
    setStage("picking");
    setSubject(null);
    setQuizQuestions([]);
    setQuizTopic(null);
    setError(null);
    setPdfError(null);
  }

  async function downloadPdf() {
    if (!subject || quizQuestions.length === 0) return;
    setIsDownloadingPdf(true);
    setPdfError(null);
    try {
      await downloadTestResultPdf({
        subjectName: subject.subject_name,
        score,
        total: quizQuestions.length,
        percent: scorePercent,
        locale: i18n.language || "uz",
        labels: {
          title: t("test.pdf.title"),
          subject: t("test.pdf.subject"),
          result: t("test.pdf.result"),
          correctAnswers: t("test.pdf.correctAnswers"),
          score: t("test.pdf.score"),
          yourAnswer: t("test.yourAnswer"),
          correctAnswer: t("test.correctAnswer"),
          explanation: t("test.explanation"),
          correct: t("test.pdf.correct"),
          incorrect: t("test.pdf.incorrect"),
          notAnswered: t("test.pdf.notAnswered"),
          page: t("test.pdf.page"),
        },
        questions: quizQuestions.map((q, questionIndex) => {
          const content = pickLang(q, lang);
          const selectedIndex = answers[questionIndex];
          return {
            number: questionIndex + 1,
            question: content.question,
            selectedOption: selectedIndex === undefined ? undefined : `${OPTION_LETTERS[selectedIndex]}. ${content.options[selectedIndex]}`,
            correctOption: `${OPTION_LETTERS[q.correctOptionIndex]}. ${content.options[q.correctOptionIndex]}`,
            explanation: content.explanation,
            isCorrect: selectedIndex === q.correctOptionIndex,
          };
        }),
      });
    } catch {
      setPdfError(t("test.pdf.error"));
    } finally {
      setIsDownloadingPdf(false);
    }
  }

  const score = quizQuestions.reduce((sum, q, i) => sum + (answers[i] === q.correctOptionIndex ? 1 : 0), 0);
  const scorePercent = quizQuestions.length > 0 ? Math.round((score / quizQuestions.length) * 100) : 0;

  const banner = (
    <div className="relative flex min-h-36 items-center overflow-hidden rounded-[1.35rem] bg-[#0a1158] px-6 py-5 text-white shadow-[0_14px_30px_rgba(10,17,88,0.18)] sm:px-7 sm:py-6 lg:px-10 xl:px-12">
      <div className="absolute -right-8 -top-12 h-32 w-32 rounded-full border border-white/10" aria-hidden />
      <div className="relative grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-5">
        <div className="max-w-3xl">
          <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-secondary-300">
            <i className="ri-brain-line text-sm" />
            {t("test.bannerEyebrow")}
          </span>
          <p className="mt-1.5 font-heading text-[clamp(1.55rem,2.15vw,2.25rem)] font-bold leading-tight">{t("test.bannerTitle")}</p>
          <p className="mt-2 text-sm leading-relaxed text-white/75">{t("test.pickSubjectHint")}</p>
        </div>
        <div className="hidden shrink-0 grid-cols-3 gap-2 lg:grid">
          {subjects && subjects.length > 0 && (
            <div className="min-w-24 rounded-2xl border border-white/15 bg-white/10 px-3 py-3 text-center">
              <i className="ri-file-list-3-line text-lg text-secondary-300" />
              <strong className="mt-1 block text-xl leading-none">{subjects.length}</strong>
              <span className="mt-1 block text-[10px] text-white/70">{t("test.bannerSubjectsLabel")}</span>
            </div>
          )}
          <div className="min-w-24 rounded-2xl border border-white/15 bg-white/10 px-3 py-3 text-center">
            <i className="ri-shuffle-line text-lg text-secondary-300" />
            <strong className="mt-1 block text-xl leading-none">{QUIZ_QUESTION_COUNT}</strong>
            <span className="mt-1 block text-[10px] text-white/70">{t("test.bannerQuestionsLabel")}</span>
          </div>
          <div className="min-w-24 rounded-2xl border border-white/15 bg-white/10 px-3 py-3 text-center">
            <i className="ri-file-pdf-2-line text-lg text-secondary-300" />
            <strong className="mt-1 block text-xl leading-none">PDF</strong>
            <span className="mt-1 block text-[10px] text-white/70">{t("test.bannerPdfLabel")}</span>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="text-foreground-950">
      <PageHeader title={t("nav.test")} compact aside={banner} />

      <div className="section-container section-pad !pt-2 md:!pt-3">
        {stage === "picking" && (
          <div className="max-w-none mx-auto overflow-hidden">
            {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

            {subjects === null && !error && (
              <div className="flex items-center gap-2 text-foreground-500 text-sm">
                <i className="ri-loader-4-line animate-spin" />
                {t("test.loading")}
              </div>
            )}

            {subjects && subjects.length === 0 && <p className="text-sm text-foreground-500">{t("test.noContent")}</p>}

            {subjects && subjects.length > 0 && (
              <CatalogBrowser
                subjects={subjects}
                countOf={(s) => s.questions_total}
                countLabel={(count) => t("test.questionsCount", { count })}
                sortByCountLabel={t("test.sortByQuestions")}
                searchPlaceholder={t("test.searchPlaceholder")}
                noResultsLabel={t("test.noSearchResults")}
                onPick={openSubject}
              />
            )}
          </div>
        )}

        {stage !== "picking" && (
        <div className="page-card p-5 md:p-6 overflow-hidden">
          {stage === "loading" && (
            <div className="flex items-center justify-center gap-2 text-foreground-500 text-sm py-16">
              <i className="ri-loader-4-line animate-spin" />
              {t("test.loading")}
            </div>
          )}

          {stage === "study" && subject && (
            <div className="max-w-3xl mx-auto">
              <div className="flex items-start justify-between gap-3 mb-4">
                <div>
                  <div className="font-heading font-bold text-foreground-900">{parseSubjectName(subject.subject_name).title}</div>
                  <div className="text-xs text-foreground-500">
                    {subject.department_name ? `${subject.department_name} · ` : ""}
                    {t("test.questionsCount", { count: subject.questions_total })}
                  </div>
                </div>
                <button type="button" onClick={backToSubjects} className="text-xs text-foreground-400 hover:text-primary-700 cursor-pointer whitespace-nowrap">
                  <i className="ri-arrow-left-line mr-0.5" />
                  {t("test.backToSubjects")}
                </button>
              </div>

              {error && <p className="text-sm text-red-600 mb-4" role="alert">{error}</p>}

              <button type="button" onClick={() => startQuiz(null)} className="uni-btn cursor-pointer w-full sm:w-auto mb-6">
                <i className="ri-pencil-ruler-2-line" />
                {t("test.quizWholeSubject", { count: QUIZ_QUESTION_COUNT })}
              </button>

              <TopicExplorer
                kind="tests"
                subjectCode={subject.subject_code}
                topicActions={(topic) =>
                  topic.code ? (
                    <button
                      type="button"
                      onClick={() => startQuiz({ code: topic.code, title: topic.title })}
                      className="inline-flex items-center gap-2 rounded-full border border-[#0a1158] px-4 py-2 text-xs font-semibold text-[#0a1158] transition-colors hover:bg-[#0a1158] hover:text-white cursor-pointer"
                    >
                      <i className="ri-pencil-ruler-2-line" />
                      {t("test.quizTopic")}
                    </button>
                  ) : null
                }
              />
            </div>
          )}

          {stage === "quiz" &&
            quizQuestions[index] &&
            (() => {
              const q = quizQuestions[index];
              const content = pickLang(q, lang);
              const isAnswered = selected !== null;
              return (
                <div className="max-w-3xl mx-auto">
                  <div className="h-1.5 w-full rounded-full bg-[#eee] overflow-hidden mb-4">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-primary-500 to-primary-700 transition-all duration-300"
                      style={{ width: `${((index + (isAnswered ? 1 : 0)) / quizQuestions.length) * 100}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between mb-4">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary-50 text-primary-700 text-xs font-bold">
                      <i className="ri-file-list-3-line" />
                      {t("test.questionOf", { current: index + 1, total: quizQuestions.length })}
                    </span>
                    <button
                      type="button"
                      onClick={() => setStage("study")}
                      className="text-xs text-foreground-400 hover:text-primary-700 cursor-pointer"
                    >
                      {t("test.backToStudy")}
                    </button>
                  </div>

                  <p className="font-heading text-base font-semibold text-foreground-900 mb-4 leading-snug">{content.question}</p>

                  <div className="space-y-2 mb-4">
                    {content.options.map((opt, i) => {
                      const isCorrect = i === q.correctOptionIndex;
                      const isSelected = i === selected;
                      let cls = "border-[#e5e5e5] hover:border-primary-200 hover:bg-primary-50/40";
                      let badgeCls = "bg-[#eee] text-foreground-500";
                      if (isAnswered && isCorrect) {
                        cls = "border-green-500 bg-green-50";
                        badgeCls = "bg-green-500 text-white";
                      } else if (isAnswered && isSelected && !isCorrect) {
                        cls = "border-red-500 bg-red-50";
                        badgeCls = "bg-red-500 text-white";
                      }
                      return (
                        <button
                          key={i}
                          type="button"
                          onClick={() => selectOption(i)}
                          disabled={isAnswered}
                          className={`w-full flex items-center gap-3 text-left px-3.5 py-2.5 rounded-xl border text-sm transition-colors ${cls} ${
                            isAnswered ? "cursor-default" : "cursor-pointer"
                          }`}
                        >
                          <span className={`w-6 h-6 shrink-0 rounded-full flex items-center justify-center text-[11px] font-bold transition-colors ${badgeCls}`}>
                            {isAnswered && isCorrect ? (
                              <i className="ri-check-line" />
                            ) : isAnswered && isSelected && !isCorrect ? (
                              <i className="ri-close-line" />
                            ) : (
                              OPTION_LETTERS[i]
                            )}
                          </span>
                          {opt}
                        </button>
                      );
                    })}
                  </div>

                  {isAnswered && content.explanation && (
                    <div className="page-card !bg-primary-50/60 p-3.5 mb-4 text-sm text-foreground-700">
                      <span className="font-semibold text-foreground-900">{t("test.explanation")}: </span>
                      {content.explanation}
                    </div>
                  )}

                  {isAnswered && (
                    <button type="button" onClick={nextQuestion} className="uni-btn cursor-pointer">
                      {index + 1 < quizQuestions.length ? t("test.next") : t("test.finish")}
                      <i className="ri-arrow-right-line" />
                    </button>
                  )}
                </div>
              );
            })()}

          {stage === "result" && (
            <div className="text-center py-6">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-white mb-4 shadow-lg shadow-primary-500/25">
                <i className="ri-medal-line text-3xl" />
              </div>
              <h2 className="font-heading text-lg font-bold text-foreground-900 mb-2">{t("test.resultTitle")}</h2>
              <p className="text-2xl font-bold text-primary-800 mb-1" aria-live="polite">
                {t("test.resultScore", { correct: score, total: quizQuestions.length })}
              </p>
              <p className="text-sm font-semibold text-foreground-600 mb-6">
                {t("test.resultPercent", { percent: scorePercent })}
              </p>
              {pdfError && <p className="text-sm text-red-600 mb-4" role="alert">{pdfError}</p>}
              <div className="flex flex-wrap items-center justify-center gap-3">
                <button type="button" onClick={downloadPdf} disabled={isDownloadingPdf} className="uni-btn cursor-pointer disabled:cursor-wait disabled:opacity-60">
                  <i className={isDownloadingPdf ? "ri-loader-4-line animate-spin" : "ri-file-download-line"} />
                  {isDownloadingPdf ? t("test.pdf.generating") : t("test.pdf.download")}
                </button>
                <button type="button" onClick={retry} className="uni-btn-ghost !text-primary-800 !border-primary-200 !bg-primary-50 hover:!bg-primary-100 cursor-pointer">
                  <i className="ri-refresh-line" />
                  {t("test.retry")}
                </button>
                <button type="button" onClick={() => setStage("study")} className="uni-btn-ghost !text-primary-800 !border-primary-200 !bg-primary-50 hover:!bg-primary-100 cursor-pointer">
                  {t("test.backToStudy")}
                </button>
                <button type="button" onClick={backToSubjects} className="uni-btn-ghost !text-primary-800 !border-primary-200 !bg-primary-50 hover:!bg-primary-100 cursor-pointer">
                  {t("test.backToSubjects")}
                </button>
              </div>
            </div>
          )}
        </div>
        )}
      </div>
    </div>
  );
}
