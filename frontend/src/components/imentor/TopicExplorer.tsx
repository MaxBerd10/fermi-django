import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import Paginator from "@/components/shared/Paginator";
import { usePagination } from "@/hooks/usePagination";
import { getImentorKey, getImentorSubjectDocuments, getImentorTest } from "@/api/imentor";
import { imentorLanguage } from "@/lib/imentorLanguage";
import type { ImentorCaseItem, ImentorDocument, ImentorDocumentKind, ImentorKeyDetail, ImentorTestDetail, ImentorTestQuestionContent } from "@/types/imentor";

const OPTION_LETTERS = ["A", "B", "C", "D", "E", "F"];
const PER_PAGE = 10;
const PARALLEL_FETCHES = 3;

type Detail = ImentorTestDetail | ImentorKeyDetail;

interface TopicGroup {
  key: string;
  code: string;
  title: string;
  documents: ImentorDocument[];
  items: number;
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

/** One entry per topic of the syllabus (a subject normally has a single syllabus; with several, each topic keeps its own). */
function groupByTopic(documents: ImentorDocument[]): TopicGroup[] {
  const topics = new Map<string, TopicGroup>();
  for (const document of documents) {
    const key = `${document.syllabus_id ?? ""}|${document.variant_label ?? ""}|${document.topic_code || document.topic}`;
    const topic = topics.get(key) ?? { key, code: document.topic_code, title: document.topic, documents: [], items: 0 };
    topic.documents.push(document);
    topic.items += document.question_count || 0;
    topics.set(key, topic);
  }
  return [...topics.values()].sort((a, b) => compareTopicCode(a.code, b.code) || a.key.localeCompare(b.key));
}

/** The case texts come as light markdown ("### Bemor" headings, **bold**): show the headings as headings, not as symbols. */
function CaseText({ text }: { text: string }) {
  return (
    <>
      {text.split("\n").map((line, index) => {
        const heading = /^#{1,6}\s+(.*)$/.exec(line);
        const clean = (heading ? heading[1] : line).replace(/\*\*(.+?)\*\*/g, "$1");
        if (heading) return <strong key={index} className="mt-2 block text-foreground-900 first:mt-0">{clean}</strong>;
        return <span key={index} className="block">{clean || " "}</span>;
      })}
    </>
  );
}

/**
 * The site does not decide what is a translation or who made it: iMentor says so. A row gets the badge only when iMentor
 * marks the document `translated_by: "ai"` (its translator); a translation a teacher made or reviewed carries no badge.
 */
function isAiTranslated(document: ImentorDocument) {
  return document.translated_by === "ai";
}

/** iMentor says the document exists in this language but was written in another one: it is shown as a translation. */
function isShownAsTranslation(document: ImentorDocument, language: string) {
  return !!document.primary_language && document.primary_language !== language;
}

function AiBadge() {
  const { t } = useTranslation();
  return (
    <span title={t("imentor.aiNote")} className="mr-2 inline-flex items-center gap-1 rounded-md bg-amber-50 px-1.5 py-0.5 align-middle text-[10px] font-semibold text-amber-800">
      <i className="ri-translate-2" aria-hidden />
      {t("imentor.aiTranslated")}
    </span>
  );
}

function TopicTag({ code }: { code: string }) {
  if (!code) return null;
  return <span className="mr-2 inline-flex rounded-md bg-[#e8edff] px-1.5 py-0.5 align-middle text-[10px] font-bold uppercase text-[#0a1158]">{code}</span>;
}

function QuestionRow({
  number,
  code,
  translated,
  question,
  correct,
  open,
  onToggle,
}: {
  number: number;
  code: string;
  translated: boolean;
  question: ImentorTestQuestionContent;
  correct: number | undefined;
  open: boolean;
  onToggle: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="overflow-hidden rounded-xl border border-[#e4e7f0] bg-white">
      <button type="button" onClick={onToggle} aria-expanded={open} className="flex w-full items-center gap-3 p-3.5 text-left cursor-pointer">
        <span className="flex h-7 min-w-7 shrink-0 items-center justify-center rounded-full bg-primary-50 px-1 text-xs font-bold text-primary-700">{number}</span>
        <span className="flex-1 text-sm font-medium text-foreground-800 line-clamp-2">
          {translated && <AiBadge />}
          <TopicTag code={code} />
          {question.question}
        </span>
        <i className={`ri-arrow-down-s-line shrink-0 text-foreground-400 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="px-3.5 pb-3.5">
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
}

function CaseRow({ number, code, translated, item, open, onToggle }: { number: number; code: string; translated: boolean; item: ImentorCaseItem; open: boolean; onToggle: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="rounded-xl border border-[#e4e7f0] bg-white p-4">
      <div className="mb-3 flex items-start gap-3">
        <span className="flex h-7 min-w-7 shrink-0 items-center justify-center rounded-full bg-primary-50 px-1 text-xs font-bold text-primary-700">{number}</span>
        <div className="flex-1 text-sm leading-relaxed text-foreground-800">
          {translated && <AiBadge />}
          <TopicTag code={code} />
          <CaseText text={item.scenario} />
        </div>
      </div>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="ml-10 inline-flex items-center gap-1 text-xs font-semibold text-primary-700 hover:text-primary-900 cursor-pointer"
      >
        <i className={`ri-arrow-down-s-line transition-transform ${open ? "rotate-180" : ""}`} />
        {open ? t("keyslar.hideAnswer") : t("keyslar.viewAnswer")}
      </button>
      {open && (
        <div className="page-card !bg-primary-50/60 ml-10 mt-3 p-3.5 text-sm text-foreground-700">
          <span className="mb-1 block font-semibold text-foreground-900">{t("keyslar.answerLabel")}</span>
          <CaseText text={item.answer} />
        </div>
      )}
    </div>
  );
}

function RowPlaceholder({ number, failed, onRetry }: { number: number; failed: boolean; onRetry: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center gap-3 rounded-xl border border-[#e4e7f0] bg-white p-3.5 text-sm text-foreground-400">
      <span className="flex h-7 min-w-7 shrink-0 items-center justify-center rounded-full bg-[#f1f3f9] px-1 text-xs font-bold text-foreground-400">{number}</span>
      {failed ? (
        <button type="button" onClick={onRetry} className="text-red-600 hover:underline cursor-pointer">
          {t("test.loadError")}
        </button>
      ) : (
        <>
          <i className="ri-loader-4-line animate-spin" />
          {t("test.loading")}
        </>
      )}
    </div>
  );
}

interface Props {
  kind: ImentorDocumentKind;
  subjectCode: string;
  /** top of the side panel: the subject's name and its main action */
  aside?: ReactNode;
}

/**
 * Every question (or clinical case) of a subject, in the order its teachers wrote them, ten to a page. A subject
 * with 500 questions shows all 500; the topic list only narrows the view. The questions live in many small
 * documents on iMentor's side, so only the documents the current page needs are fetched.
 * On a wide screen the side panel (subject, action, topics) stays in view while the questions scroll.
 */
export default function TopicExplorer({ kind, subjectCode, aside }: Props) {
  const { t, i18n } = useTranslation();
  // the questions / cases come in the visitor's language (iMentor returns only what exists in it); switching the site
  // language fetches the list and the documents again
  const lang = imentorLanguage(i18n.language);
  const isTests = kind === "tests";

  const [documents, setDocuments] = useState<ImentorDocument[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [topicKey, setTopicKey] = useState("");
  const [details, setDetails] = useState<Record<number, Detail | "error">>({});
  const [openRows, setOpenRows] = useState<Record<string, boolean>>({});
  const listTopRef = useRef<HTMLDivElement>(null);
  const requested = useRef(new Set<number>());

  useEffect(() => {
    let cancelled = false;
    setDocuments(null);
    setFailed(false);
    setTopicKey("");
    setDetails({});
    setOpenRows({});
    requested.current = new Set();
    getImentorSubjectDocuments(kind, subjectCode, lang)
      .then((data) => !cancelled && setDocuments(data))
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [kind, subjectCode, lang]);

  const topics = useMemo(() => (documents ? groupByTopic(documents) : []), [documents]);
  const totalItems = topics.reduce((sum, topic) => sum + topic.items, 0);

  /** the flat list of everything in view: one entry per question / case, pointing at its document */
  const items = useMemo(() => {
    const chosen = topicKey ? topics.filter((topic) => topic.key === topicKey) : topics;
    const list: Array<{ document: ImentorDocument; index: number; code: string }> = [];
    for (const topic of chosen) {
      for (const document of topic.documents) {
        for (let index = 0; index < (document.question_count || 0); index += 1) list.push({ document, index, code: topic.code });
      }
    }
    return list;
  }, [topics, topicKey]);

  const paging = usePagination(items, PER_PAGE, `${subjectCode}|${topicKey}|${lang}`, listTopRef);

  const fetchDocument = useCallback(
    (document: ImentorDocument) => {
      requested.current.add(document.id);
      const load = isTests ? getImentorTest(document.id, lang) : getImentorKey(document.id, lang);
      return load
        .then((detail) => setDetails((current) => ({ ...current, [document.id]: detail })))
        .catch(() => {
          requested.current.delete(document.id);
          setDetails((current) => ({ ...current, [document.id]: "error" }));
        });
    },
    [isTests, lang],
  );

  // fetch the documents the visible page needs (a few at a time: iMentor's server is small)
  useEffect(() => {
    const needed: ImentorDocument[] = [];
    for (const { document } of paging.pageItems) {
      if (!requested.current.has(document.id) && !needed.some((d) => d.id === document.id)) needed.push(document);
    }
    if (needed.length === 0) return;
    let cancelled = false;
    (async () => {
      for (let start = 0; start < needed.length && !cancelled; start += PARALLEL_FETCHES) {
        await Promise.all(needed.slice(start, start + PARALLEL_FETCHES).map(fetchDocument));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [paging.pageItems, fetchDocument]);

  const hasTranslations = !!documents?.some((document) => isShownAsTranslation(document, lang));
  const countLabel = (count: number) => (isTests ? t("test.questionsCount", { count }) : t("keyslar.casesCount", { count }));
  const ready = documents !== null && documents.length > 0;

  const topicFilter = ready && (
    <div className="mt-5">
      <span className="mb-2.5 block text-sm font-bold uppercase tracking-wide text-foreground-500">{t("test.syllabusTitle")}</span>

      {/* phones: a compact picker */}
      <select
        value={topicKey}
        onChange={(event) => setTopicKey(event.target.value)}
        aria-label={t("test.syllabusTitle")}
        className="h-11 w-full rounded-xl border border-[#e4e7f0] bg-white px-3 text-sm text-foreground-900 outline-none focus:border-[#0a1158] focus:ring-2 focus:ring-[#dfe5ff] lg:hidden"
      >
        <option value="">
          {t("test.allTopics")} · {totalItems}
        </option>
        {topics.map((topic) => (
          <option key={topic.key} value={topic.key}>
            {topic.code ? `${topic.code.toUpperCase()} — ` : ""}
            {topic.title.length > 90 ? `${topic.title.slice(0, 90)}…` : topic.title} · {topic.items}
          </option>
        ))}
      </select>

      {/* wide screens: the whole syllabus as a list that stays beside the questions */}
      <div className="hidden max-h-[46vh] space-y-1 overflow-y-auto pr-1 lg:block">
        {[{ key: "", code: "", title: t("test.allTopics"), items: totalItems }, ...topics].map((topic) => {
          const active = topicKey === topic.key;
          return (
            <button
              key={topic.key || "all"}
              type="button"
              onClick={() => setTopicKey(topic.key)}
              aria-pressed={active}
              className={`flex w-full items-start gap-3 rounded-xl px-3.5 py-2.5 text-left text-[15px] leading-snug transition-colors cursor-pointer ${
                active ? "bg-[#0a1158] text-white" : "text-foreground-700 hover:bg-[#f1f3f9]"
              }`}
            >
              {topic.code ? (
                <span className={`mt-px inline-flex min-w-8 shrink-0 justify-center rounded-md px-1.5 py-0.5 text-xs font-bold uppercase ${active ? "bg-white/20" : "bg-[#e8edff] text-[#0a1158]"}`}>
                  {topic.code}
                </span>
              ) : (
                <i className="ri-stack-line mt-px shrink-0" aria-hidden />
              )}
              <span className="min-w-0 flex-1 line-clamp-3">{topic.title}</span>
              <span className={`shrink-0 text-xs font-semibold ${active ? "text-white/80" : "text-foreground-400"}`}>{topic.items}</span>
            </button>
          );
        })}
      </div>
    </div>
  );

  let main: ReactNode;
  if (failed) {
    main = <p className="text-sm text-red-600">{t("test.loadError")}</p>;
  } else if (!documents) {
    main = (
      <div className="flex min-h-[60vh] items-start gap-2 pt-2 text-sm text-foreground-500">
        <i className="ri-loader-4-line animate-spin" />
        {t("test.loading")}
      </div>
    );
  } else if (documents.length === 0) {
    main = <p className="text-sm text-foreground-500">{t("test.noTopics")}</p>;
  } else {
    main = (
      <>
        <div className="mb-3 text-sm font-medium text-foreground-500">
          {topicKey ? topics.find((topic) => topic.key === topicKey)?.title : t("test.allTopics")} · {countLabel(items.length)}
        </div>
        {hasTranslations && (
          <p className="mb-3 flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-snug text-amber-900">
            <i className="ri-translate-2 mt-0.5 shrink-0" aria-hidden />
            {t("imentor.aiNote")}
          </p>
        )}
        <div ref={listTopRef} className="scroll-mt-24 space-y-2">
          {paging.pageItems.map(({ document, index, code }, pageIndex) => {
            const number = paging.offset + pageIndex + 1;
            const rowKey = `${document.id}:${index}`;
            const detail = details[document.id];
            const toggle = () => setOpenRows((current) => ({ ...current, [rowKey]: !current[rowKey] }));
            if (!detail || detail === "error") {
              return (
                <RowPlaceholder
                  key={rowKey}
                  number={number}
                  failed={detail === "error"}
                  onRetry={() => {
                    setDetails((current) => {
                      const next = { ...current };
                      delete next[document.id];
                      return next;
                    });
                    void fetchDocument(document);
                  }}
                />
              );
            }
            if (isTests) {
              const test = detail as ImentorTestDetail;
              const source = test.payload.questions;
              // asked with ?language=, iMentor puts that language straight into `questions` (and names it in `language`);
              // a translation stored beside the original is only the fallback for an answer that did not come that way
              const translated = test.language === lang ? undefined : test.payload.translations?.[lang]?.questions;
              const question = (translated && translated.length === source.length ? translated : source)[index];
              if (!question) return null;
              return (
                <QuestionRow
                  key={rowKey}
                  number={number}
                  code={topicKeyCode(topicKey, code)}
                  translated={isAiTranslated(document)}
                  question={question}
                  correct={source[index]?.correctOptionIndex ?? question.correctOptionIndex}
                  open={!!openRows[rowKey]}
                  onToggle={toggle}
                />
              );
            }
            const keyDetail = detail as ImentorKeyDetail;
            const translatedCases = keyDetail.language === lang ? undefined : keyDetail.payload.translations?.[lang]?.questions;
            const cases = translatedCases && translatedCases.length === keyDetail.payload.questions.length ? translatedCases : keyDetail.payload.questions;
            const item = cases[index];
            if (!item) return null;
            return <CaseRow key={rowKey} number={number} code={topicKeyCode(topicKey, code)} translated={isAiTranslated(document)} item={item} open={!!openRows[rowKey]} onToggle={toggle} />;
          })}
        </div>
        <div className="mt-5">
          <Paginator page={paging.page} totalPages={paging.totalPages} onChange={paging.go} />
        </div>
      </>
    );
  }

  return (
    <div className="lg:grid lg:grid-cols-[minmax(0,24rem)_minmax(0,1fr)] lg:items-start lg:gap-10">
      <aside className="mb-6 lg:sticky lg:top-24 lg:mb-0 lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto">
        {aside}
        {topicFilter}
      </aside>
      <div className="min-w-0">{main}</div>
    </div>
  );
}

/** the topic code tag is only useful when the list mixes several topics */
function topicKeyCode(topicKey: string, code: string) {
  return topicKey ? "" : code;
}
