import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { getImentorKey, getImentorSubjectDocuments, getImentorTest } from "@/api/imentor";
import type { ImentorDocument, ImentorDocumentKind, ImentorKeyDetail, ImentorTestDetail, ImentorTestQuestionContent } from "@/types/imentor";

const OPTION_LETTERS = ["A", "B", "C", "D", "E", "F"];

interface TopicGroup {
  key: string;
  code: string;
  title: string;
  documents: ImentorDocument[];
  items: number;
}

interface SyllabusGroup {
  key: string;
  syllabusId: number | null;
  topics: TopicGroup[];
}

/** "a2" before "a10": letters first, then the number */
function compareTopicCode(a: string, b: string) {
  const split = (code: string) => {
    const match = /^([a-zA-Z]*)(\d*)/.exec(code) ?? [];
    return [match[1] ?? "", Number(match[2] || 0)] as const;
  };
  const [aLetters, aNumber] = split(a);
  const [bLetters, bNumber] = split(b);
  return aLetters.localeCompare(bLetters) || aNumber - bNumber || a.localeCompare(b);
}

function groupDocuments(documents: ImentorDocument[]): SyllabusGroup[] {
  const syllabi = new Map<string, Map<string, TopicGroup>>();
  const syllabusIds = new Map<string, number | null>();
  for (const document of documents) {
    const syllabusKey = `${document.syllabus_id ?? ""}|${document.variant_label ?? ""}`;
    syllabusIds.set(syllabusKey, document.syllabus_id);
    const topics = syllabi.get(syllabusKey) ?? new Map<string, TopicGroup>();
    const topicKey = document.topic_code || document.topic;
    const topic = topics.get(topicKey) ?? { key: topicKey, code: document.topic_code, title: document.topic, documents: [], items: 0 };
    topic.documents.push(document);
    topic.items += document.question_count || 0;
    topics.set(topicKey, topic);
    syllabi.set(syllabusKey, topics);
  }
  return [...syllabi.entries()].map(([key, topics]) => ({
    key,
    syllabusId: syllabusIds.get(key) ?? null,
    topics: [...topics.values()].sort((a, b) => compareTopicCode(a.code, b.code)),
  }));
}

/** The case texts come as light markdown ("### Bemor" headings, **bold**): show the headings as headings, not as symbols. */
function CaseText({ text }: { text: string }) {
  return (
    <>
      {text.split("\n").map((line, index) => {
        const heading = /^#{1,6}\s+(.*)$/.exec(line);
        const clean = (heading ? heading[1] : line).replace(/\*\*(.+?)\*\*/g, "$1");
        if (heading) return <strong key={index} className="mt-2 block text-foreground-900 first:mt-0">{clean}</strong>;
        return <span key={index} className="block">{clean || "\u00a0"}</span>;
      })}
    </>
  );
}

function Loading({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 py-4 text-sm text-foreground-500">
      <i className="ri-loader-4-line animate-spin" />
      {label}
    </div>
  );
}

function TestDocumentView({ id, lang }: { id: number; lang: string }) {
  const { t } = useTranslation();
  const [detail, setDetail] = useState<ImentorTestDetail | null>(null);
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    getImentorTest(id)
      .then((data) => !cancelled && setDetail(data))
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (failed) return <p className="py-3 text-sm text-red-600">{t("test.loadError")}</p>;
  if (!detail) return <Loading label={t("test.loading")} />;

  const translated = detail.payload.translations?.[lang]?.questions;
  const questions: ImentorTestQuestionContent[] = translated && translated.length === detail.payload.questions.length ? translated : detail.payload.questions;

  return (
    <div className="space-y-2 py-2">
      {questions.map((question, index) => {
        const correct = detail.payload.questions[index]?.correctOptionIndex ?? question.correctOptionIndex;
        const isOpen = open === index;
        return (
          <div key={index} className="overflow-hidden rounded-xl border border-[#e4e7f0] bg-white">
            <button type="button" onClick={() => setOpen(isOpen ? null : index)} className="flex w-full items-center gap-3 p-3 text-left cursor-pointer">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-50 text-xs font-bold text-primary-700">{index + 1}</span>
              <span className="flex-1 text-sm font-medium text-foreground-800 line-clamp-2">{question.question}</span>
              <i className={`ri-arrow-down-s-line shrink-0 text-foreground-400 transition-transform ${isOpen ? "rotate-180" : ""}`} />
            </button>
            {isOpen && (
              <div className="px-3 pb-3">
                <p className="mb-2.5 text-sm font-semibold leading-snug text-foreground-900">{question.question}</p>
                <div className="space-y-1.5">
                  {question.options.map((option, optionIndex) => {
                    const isCorrect = optionIndex === correct;
                    return (
                      <div
                        key={optionIndex}
                        className={`flex items-center gap-2.5 rounded-lg border px-3 py-2 text-sm ${
                          isCorrect ? "border-green-500 bg-green-50 font-medium text-foreground-900" : "border-[#e5e5e5] text-foreground-600"
                        }`}
                      >
                        <span
                          className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                            isCorrect ? "bg-green-500 text-white" : "bg-[#eee] text-foreground-500"
                          }`}
                        >
                          {isCorrect ? <i className="ri-check-line" /> : OPTION_LETTERS[optionIndex]}
                        </span>
                        {option}
                      </div>
                    );
                  })}
                </div>
                {question.explanation && (
                  <div className="mt-2.5 text-xs text-foreground-500">
                    <span className="font-semibold text-foreground-700">{t("test.explanation")}: </span>
                    {question.explanation}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function KeyDocumentView({ id }: { id: number }) {
  const { t } = useTranslation();
  const [detail, setDetail] = useState<ImentorKeyDetail | null>(null);
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    getImentorKey(id)
      .then((data) => !cancelled && setDetail(data))
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (failed) return <p className="py-3 text-sm text-red-600">{t("test.loadError")}</p>;
  if (!detail) return <Loading label={t("test.loading")} />;

  return (
    <div className="space-y-3 py-2">
      {detail.payload.questions.map((item, index) => {
        const isOpen = open === index;
        return (
          <div key={index} className="rounded-xl border border-[#e4e7f0] bg-white p-4">
            <div className="mb-3 flex items-start gap-3">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-50 text-xs font-bold text-primary-700">{index + 1}</span>
              <div className="flex-1 text-sm leading-relaxed text-foreground-800"><CaseText text={item.scenario} /></div>
            </div>
            <button
              type="button"
              onClick={() => setOpen(isOpen ? null : index)}
              className="ml-10 inline-flex items-center gap-1 text-xs font-semibold text-primary-700 hover:text-primary-900 cursor-pointer"
            >
              <i className={`ri-arrow-down-s-line transition-transform ${isOpen ? "rotate-180" : ""}`} />
              {isOpen ? t("keyslar.hideAnswer") : t("keyslar.viewAnswer")}
            </button>
            {isOpen && (
              <div className="page-card !bg-primary-50/60 ml-10 mt-3 p-3.5 text-sm text-foreground-700">
                <span className="mb-1 block font-semibold text-foreground-900">{t("keyslar.answerLabel")}</span>
                <CaseText text={item.answer} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

interface Props {
  kind: ImentorDocumentKind;
  subjectCode: string;
  /** shown above a topic's documents, e.g. a "try yourself on this topic" button */
  topicActions?: (topic: { code: string; title: string; items: number }) => ReactNode;
}

/**
 * The whole content of a subject, the way its teachers wrote it: syllabus -> topics -> tests (or case sets) ->
 * questions. Nothing is sampled, so a subject with 500 questions shows all 500.
 */
export default function TopicExplorer({ kind, subjectCode, topicActions }: Props) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "uz").slice(0, 2);
  const [documents, setDocuments] = useState<ImentorDocument[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [openTopic, setOpenTopic] = useState<string | null>(null);
  const [openDocument, setOpenDocument] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDocuments(null);
    setFailed(false);
    setOpenTopic(null);
    setOpenDocument(null);
    getImentorSubjectDocuments(kind, subjectCode)
      .then((data) => !cancelled && setDocuments(data))
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [kind, subjectCode]);

  const syllabi = useMemo(() => (documents ? groupDocuments(documents) : []), [documents]);
  const topicCount = syllabi.reduce((sum, syllabus) => sum + syllabus.topics.length, 0);
  const isTests = kind === "tests";

  if (failed) return <p className="text-sm text-red-600">{t("test.loadError")}</p>;
  if (!documents) return <Loading label={t("test.loading")} />;
  if (documents.length === 0) return <p className="text-sm text-foreground-500">{t("test.noTopics")}</p>;

  return (
    <div>
      <div className="mb-1 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-heading text-lg font-bold text-foreground-900">{t("test.syllabusTitle")}</h2>
        <span className="text-xs font-medium text-foreground-500">{t("test.topicsCount", { count: topicCount })}</span>
      </div>
      <p className="mb-4 text-sm text-foreground-500">{t(isTests ? "test.syllabusHint" : "keyslar.syllabusHint")}</p>

      <div className="space-y-5">
        {syllabi.map((syllabus) => (
          <div key={syllabus.key}>
            {syllabi.length > 1 && syllabus.syllabusId !== null && (
              <div className="mb-2 text-xs font-bold uppercase tracking-wide text-foreground-400">{t("test.syllabusN", { id: syllabus.syllabusId })}</div>
            )}
            <div className="space-y-2">
              {syllabus.topics.map((topic) => {
                const topicId = `${syllabus.key}|${topic.key}`;
                const isOpen = openTopic === topicId;
                return (
                  <div key={topicId} className="overflow-hidden rounded-2xl border border-[#e4e7f0] bg-white shadow-[0_4px_14px_rgba(20,32,86,0.03)]">
                    <button
                      type="button"
                      onClick={() => {
                        setOpenTopic(isOpen ? null : topicId);
                        setOpenDocument(null);
                      }}
                      aria-expanded={isOpen}
                      className="flex w-full items-center gap-3 p-4 text-left cursor-pointer hover:bg-[#fafbfe]"
                    >
                      {topic.code && (
                        <span className="flex h-9 min-w-9 shrink-0 items-center justify-center rounded-xl bg-[#e8edff] px-2 text-xs font-bold uppercase text-[#0a1158]">{topic.code}</span>
                      )}
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm font-semibold leading-snug text-foreground-900">{topic.title}</span>
                        <span className="mt-1 block text-xs text-foreground-500">
                          {isTests
                            ? `${t("test.topicTestsCount", { count: topic.documents.length })} · ${t("test.questionsCount", { count: topic.items })}`
                            : t("keyslar.topicCasesCount", { count: topic.items })}
                        </span>
                      </span>
                      <i className={`ri-arrow-down-s-line shrink-0 text-xl text-foreground-400 transition-transform ${isOpen ? "rotate-180" : ""}`} />
                    </button>

                    {isOpen && (
                      <div className="border-t border-[#eef0f6] bg-[#fafbfe] p-3 sm:p-4">
                        {topicActions && <div className="mb-3">{topicActions({ code: topic.code, title: topic.title, items: topic.items })}</div>}
                        <div className="space-y-2">
                          {topic.documents.map((document) => {
                            const documentOpen = openDocument === document.id;
                            return (
                              <div key={document.id} className="rounded-xl border border-[#e4e7f0] bg-white">
                                <button
                                  type="button"
                                  onClick={() => setOpenDocument(documentOpen ? null : document.id)}
                                  aria-expanded={documentOpen}
                                  className="flex w-full flex-wrap items-center gap-x-3 gap-y-1 p-3 text-left cursor-pointer"
                                >
                                  <span className="text-sm font-semibold text-foreground-900">{t(isTests ? "test.testNumber" : "keyslar.caseSetNumber", { id: document.id })}</span>
                                  <span className="rounded-full bg-[#eef2ff] px-2 py-0.5 text-[11px] font-bold text-[#0a1158]">
                                    {isTests ? t("test.questionsCount", { count: document.question_count }) : t("keyslar.casesCount", { count: document.question_count })}
                                  </span>
                                  {document.author_display_name && (
                                    <span className="min-w-0 flex-1 truncate text-xs text-foreground-500">{t("test.testAuthor", { name: document.author_display_name })}</span>
                                  )}
                                  <span className="ml-auto inline-flex items-center gap-1 text-xs font-semibold text-primary-700">
                                    {documentOpen ? t("test.hideQuestions") : t("test.showQuestions")}
                                    <i className={`ri-arrow-down-s-line transition-transform ${documentOpen ? "rotate-180" : ""}`} />
                                  </span>
                                </button>
                                {documentOpen && (
                                  <div className="border-t border-[#eef0f6] px-3 pb-2">
                                    {isTests ? <TestDocumentView id={document.id} lang={lang} /> : <KeyDocumentView id={document.id} />}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
