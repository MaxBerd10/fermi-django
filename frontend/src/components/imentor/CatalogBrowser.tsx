import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import Paginator from "@/components/shared/Paginator";
import { usePagination } from "@/hooks/usePagination";
import { COURSES, PROGRAMS, buildCatalog, programInfo, type CatalogEntry } from "@/lib/imentorCatalog";
import type { ImentorSubjectStat } from "@/types/imentor";

const SUBJECTS_PER_PAGE = 12;
const SUBJECT_ICONS = ["ri-file-list-3-line", "ri-first-aid-kit-line", "ri-heart-pulse-line", "ri-mental-health-line", "ri-syringe-line", "ri-hospital-line"];

type Lang = "uz" | "ru" | "en";
type SortBy = "count" | "alpha";

interface Props {
  subjects: ImentorSubjectStat[];
  /** how much content a subject has (questions / cases): shown on its card and used to sort */
  countOf: (subject: ImentorSubjectStat) => number;
  countLabel: (count: number) => string;
  sortByCountLabel: string;
  searchPlaceholder: string;
  noResultsLabel: string;
  onPick: (subject: ImentorSubjectStat) => void;
}

/**
 * Programme -> year -> subject picker shared by the test and the case pages. The programme and the year are read
 * from the subject names (see lib/imentorCatalog.ts); the choice lives in the address (?f=&k=&q=), so the browser's
 * back button steps out of a level and a link opens the same view.
 */
export default function CatalogBrowser({ subjects, countOf, countLabel, sortByCountLabel, searchPlaceholder, noResultsLabel, onPick }: Props) {
  const { t, i18n } = useTranslation();
  const rawLang = (i18n.language || "uz").slice(0, 2);
  const lang: Lang = rawLang === "ru" || rawLang === "en" ? rawLang : "uz";
  const [params, setParams] = useSearchParams();
  const topRef = useRef<HTMLDivElement>(null);

  const programKey = params.get("f") || "";
  const courseParam = params.get("k") || "";
  const query = params.get("q") || "";
  const sortBy: SortBy = params.get("s") === "alpha" ? "alpha" : "count";

  // The text box keeps its own state (the address updates a moment later), otherwise fast typing loses letters.
  const [text, setText] = useState(query);
  const lastWritten = useRef(query);
  useEffect(() => {
    if (query !== lastWritten.current) {
      // the address changed by itself (back button, a link): follow it
      lastWritten.current = query;
      setText(query);
    }
  }, [query]);
  useEffect(() => {
    if (text === lastWritten.current) return;
    const timer = window.setTimeout(() => {
      lastWritten.current = text;
      const next = new URLSearchParams(window.location.search);
      if (text) next.set("q", text);
      else next.delete("q");
      setParams(next, { replace: true });
    }, 250);
    return () => window.clearTimeout(timer);
  }, [text, setParams]);

  const catalog = useMemo(() => buildCatalog(subjects.filter((s) => s.subject_code && s.subject_name)), [subjects]);

  function update(changes: Record<string, string | null>, options?: { replace?: boolean }) {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    setParams(next, { replace: options?.replace ?? false });
  }

  const byProgram = useMemo(() => {
    const map = new Map<string, CatalogEntry<ImentorSubjectStat>[]>();
    for (const entry of catalog) {
      const list = map.get(entry.parsed.program) ?? [];
      list.push(entry);
      map.set(entry.parsed.program, list);
    }
    return map;
  }, [catalog]);

  const sorter = (a: CatalogEntry<ImentorSubjectStat>, b: CatalogEntry<ImentorSubjectStat>) =>
    sortBy === "alpha" ? a.parsed.title.localeCompare(b.parsed.title) : countOf(b.item) - countOf(a.item);

  const searching = query.trim().length > 0;
  const programEntries = useMemo(() => (programKey ? byProgram.get(programKey) ?? [] : []), [byProgram, programKey]);

  const courseCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const entry of programEntries) {
      const key = entry.parsed.course === null ? "none" : String(entry.parsed.course);
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
    return counts;
  }, [programEntries]);

  const visible = useMemo(() => {
    let list: CatalogEntry<ImentorSubjectStat>[];
    if (searching) {
      const q = query.trim().toLowerCase();
      list = catalog.filter(
        ({ item, parsed }) =>
          item.subject_name.toLowerCase().includes(q) ||
          parsed.title.toLowerCase().includes(q) ||
          (item.department_name || "").toLowerCase().includes(q),
      );
    } else if (programKey) {
      list = programEntries.filter((entry) => {
        if (!courseParam) return true;
        return courseParam === "none" ? entry.parsed.course === null : String(entry.parsed.course) === courseParam;
      });
    } else {
      list = [];
    }
    return [...list].sort(sorter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalog, searching, query, programKey, courseParam, programEntries, sortBy]);

  const paging = usePagination(visible, SUBJECTS_PER_PAGE, `${query}|${programKey}|${courseParam}|${sortBy}`, topRef);
  const showSubjects = searching || programKey !== "";

  const inputClass =
    "h-12 w-full rounded-xl border border-[#e4e7f0] bg-[#fafbfe] pl-11 pr-4 text-sm text-foreground-900 outline-none transition-colors placeholder:text-foreground-400 focus:border-[#0a1158] focus:bg-white focus:ring-2 focus:ring-[#dfe5ff]";
  const sortButton = (value: SortBy, label: string, icon: string) => (
    <button
      type="button"
      onClick={() => update({ s: value === "count" ? null : value }, { replace: true })}
      className={`h-10 rounded-lg px-3 text-xs font-semibold transition-colors ${
        sortBy === value ? "bg-[#0a1158] text-white shadow-sm" : "text-foreground-500 hover:text-[#0a1158]"
      }`}
    >
      <i className={`${icon} mr-1.5`} />
      {label}
    </button>
  );

  const courseChip = (key: string, label: string, count: number) => {
    const active = (courseParam || "") === key;
    return (
      <button
        key={key || "all"}
        type="button"
        onClick={() => update({ k: key || null })}
        aria-pressed={active}
        className={`inline-flex h-10 items-center gap-2 rounded-full border px-4 text-sm font-semibold transition-colors cursor-pointer ${
          active ? "border-[#0a1158] bg-[#0a1158] text-white" : "border-[#dfe3f0] bg-white text-foreground-700 hover:border-[#0a1158] hover:text-[#0a1158]"
        }`}
      >
        {label}
        <span className={`rounded-full px-2 py-0.5 text-[11px] ${active ? "bg-white/20" : "bg-[#eef2ff] text-[#0a1158]"}`}>{count}</span>
      </button>
    );
  };

  return (
    <>
      <section className="rounded-[1.35rem] border border-[#e5e8f1] bg-white p-3 shadow-[0_8px_28px_rgba(20,32,86,0.05)] sm:p-4">
        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="relative block flex-1">
            <i className="ri-search-line absolute left-4 top-1/2 -translate-y-1/2 text-lg text-[#64709c]" aria-hidden />
            <input
              type="search"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={searchPlaceholder}
              className={inputClass}
            />
          </label>
          {showSubjects && (
            <div className="flex rounded-xl border border-[#e4e7f0] bg-[#fafbfe] p-1 sm:w-auto">
              {sortButton("count", sortByCountLabel, "ri-bar-chart-grouped-line")}
              {sortButton("alpha", t("test.sortByAlpha"), "ri-sort-alphabet-asc")}
            </div>
          )}
        </div>
      </section>

      <div ref={topRef} className="scroll-mt-24" />

      {!showSubjects && (
        <div className="mt-6">
          <h2 className="font-heading text-lg font-bold text-foreground-900">{t("catalog.pickFaculty")}</h2>
          <p className="mt-1 mb-4 text-sm text-foreground-500">{t("catalog.pickFacultyHint")}</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {PROGRAMS.filter((program) => byProgram.has(program.key)).map((program) => {
              const entries = byProgram.get(program.key) ?? [];
              const total = entries.reduce((sum, entry) => sum + countOf(entry.item), 0);
              return (
                <button
                  key={program.key}
                  type="button"
                  onClick={() => update({ f: program.key, k: null })}
                  className="group flex items-center gap-4 rounded-2xl border border-[#e4e7f0] bg-white p-4 text-left shadow-[0_6px_18px_rgba(20,32,86,0.04)] transition-all hover:-translate-y-0.5 hover:border-[#b8c5f4] hover:shadow-[0_14px_28px_rgba(20,32,86,0.10)] focus:outline-none focus:ring-2 focus:ring-secondary-400 focus:ring-offset-2 cursor-pointer"
                >
                  <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[#e8edff] text-2xl text-[#0a1158] transition-colors group-hover:bg-[#0a1158] group-hover:text-white">
                    <i className={program.icon} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block font-heading text-[15px] font-bold leading-snug text-foreground-900">{program.name[lang]}</span>
                    <span className="mt-1 block text-xs text-foreground-500">
                      {t("catalog.subjectsCount", { count: entries.length })} · {countLabel(total)}
                    </span>
                    {program.key === "other" && <span className="mt-1 block text-[11px] text-foreground-400">{t("catalog.otherNote")}</span>}
                  </span>
                  <i className="ri-arrow-right-line text-foreground-400 transition-transform group-hover:translate-x-0.5 group-hover:text-[#0a1158]" />
                </button>
              );
            })}
          </div>
        </div>
      )}

      {showSubjects && (
        <div className="mt-6">
          {searching ? (
            <h2 className="font-heading text-lg font-bold text-foreground-900">{t("catalog.searchResults")}</h2>
          ) : (
            <>
              <button
                type="button"
                onClick={() => update({ f: null, k: null })}
                className="mb-3 inline-flex items-center gap-1 text-sm font-medium text-foreground-500 hover:text-[#0a1158] cursor-pointer"
              >
                <i className="ri-arrow-left-line" />
                {t("catalog.backToFaculties")}
              </button>
              <h2 className="font-heading text-lg font-bold text-foreground-900">{programInfo(programKey).name[lang]}</h2>
              <p className="mt-1 mb-3 text-sm text-foreground-500">{t("catalog.pickCourse")}</p>
              <div className="mb-5 flex flex-wrap gap-2">
                {courseChip("", t("catalog.allCourses"), programEntries.length)}
                {COURSES.filter((course) => courseCounts.has(String(course))).map((course) =>
                  courseChip(String(course), t("catalog.courseN", { n: course }), courseCounts.get(String(course)) ?? 0),
                )}
                {courseCounts.has("none") && courseChip("none", t("catalog.noCourse"), courseCounts.get("none") ?? 0)}
              </div>
            </>
          )}

          {visible.length === 0 && <p className="text-sm text-foreground-500">{searching ? noResultsLabel : t("catalog.emptyCourse")}</p>}

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {paging.pageItems.map(({ item, parsed }, i) => (
              <button
                key={item.subject_code}
                type="button"
                onClick={() => onPick(item)}
                className="group relative flex min-h-44 flex-col overflow-hidden rounded-2xl border border-[#e4e7f0] bg-white p-4 text-left shadow-[0_6px_18px_rgba(20,32,86,0.04)] transition-all hover:-translate-y-0.5 hover:border-[#b8c5f4] hover:shadow-[0_14px_28px_rgba(20,32,86,0.10)] focus:outline-none focus:ring-2 focus:ring-secondary-400 focus:ring-offset-2 cursor-pointer"
              >
                <div className="absolute right-0 top-0 h-20 w-20 rounded-bl-[4rem] bg-[#f6f8ff] transition-colors group-hover:bg-[#edf1ff]" aria-hidden />
                <div className="relative flex items-start gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#e8edff] text-[#0a1158] transition-colors group-hover:bg-[#0a1158] group-hover:text-white">
                    <i className={`${SUBJECT_ICONS[(paging.offset + i) % SUBJECT_ICONS.length]} text-lg`} />
                  </div>
                  <div className="min-w-0">
                    <div className="font-heading text-[15px] font-bold leading-snug text-foreground-900 line-clamp-3">{parsed.title}</div>
                    {item.department_name && <div className="mt-1 text-xs text-foreground-500 line-clamp-1">{item.department_name}</div>}
                  </div>
                </div>
                <div className="relative mt-3 flex flex-wrap gap-1.5">
                  {searching && parsed.program !== "other" && (
                    <span className="rounded-full bg-[#f1f3f9] px-2 py-0.5 text-[10.5px] font-semibold text-foreground-600">{programInfo(parsed.program).name[lang]}</span>
                  )}
                  {parsed.course !== null && (
                    <span className="rounded-full bg-[#f1f3f9] px-2 py-0.5 text-[10.5px] font-semibold text-foreground-600">{t("catalog.courseN", { n: parsed.course })}</span>
                  )}
                  {parsed.semester !== null && <span className="rounded-full bg-[#f1f3f9] px-2 py-0.5 text-[10.5px] font-semibold text-foreground-600">{parsed.semester}-sem</span>}
                  {parsed.track && <span className="rounded-full bg-[#f1f3f9] px-2 py-0.5 text-[10.5px] font-semibold text-foreground-600">{parsed.track}</span>}
                  {parsed.intake && <span className="rounded-full bg-[#f1f3f9] px-2 py-0.5 text-[10.5px] font-semibold text-foreground-600">{parsed.intake}</span>}
                </div>
                <div className="relative mt-auto flex items-end justify-between gap-3 pt-4">
                  <span className="inline-flex items-center gap-1 rounded-full bg-[#eef2ff] px-2.5 py-1 text-[11px] font-bold text-[#0a1158]">
                    <i className="ri-question-line" />
                    {countLabel(countOf(item))}
                  </span>
                  <span className="flex h-8 w-8 items-center justify-center rounded-full border border-[#e1e5ef] text-foreground-400 transition-all group-hover:border-[#0a1158] group-hover:bg-[#0a1158] group-hover:text-white group-hover:translate-x-0.5">
                    <i className="ri-arrow-right-line" />
                  </span>
                </div>
              </button>
            ))}
          </div>
          <div className="mt-6">
            <Paginator page={paging.page} totalPages={paging.totalPages} onChange={paging.go} />
          </div>
        </div>
      )}
    </>
  );
}
