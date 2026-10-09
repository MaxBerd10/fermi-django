import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getNewsCategory } from "@/api/news";
import type { NewsArticle } from "@/types/content";
import { formatShortDate } from "@/lib/date";
import { stripHtml } from "@/lib/html";
import { buildNewsDetailHref } from "@/lib/newsSection";
import { pad2, useAdmissionCountdown } from "@/hooks/useAdmissionCountdown";

const EVENTS_HREF = "/news/6/tadbirlar";
const EVENTS_SHOWN = 4;
const JOURNAL_HREF = "/blog/283/jurnal-xaqida";
const JOURNAL_SUBMIT_HREF = "/blog/283/maqola-namunasi";

export default function EventsJournal() {
  const { t, i18n } = useTranslation();
  const cd = useAdmissionCountdown();
  // The latest posts of the "Tadbirlar" (events) news category -- real events, each with its own page.
  // null = still loading, [] = none (or the request failed): the list is then left out.
  const [events, setEvents] = useState<NewsArticle[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    getNewsCategory("tadbirlar", 1)
      .then((res) => {
        if (cancelled) return;
        const latest = [...res.data.items].sort((x, y) => String(y.date).localeCompare(String(x.date))).slice(0, EVENTS_SHOWN);
        setEvents(latest);
      })
      .catch(() => !cancelled && setEvents([]));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="pt-5 pb-3 md:pt-6 md:pb-3 bg-transparent border-t border-[#e5e5e5]/60">
      <div className="section-container relative z-10">
        {events === null && (
          <div aria-hidden="true">
            <div className="mb-4 h-14" />
            <div className="border-t border-primary-200">
              {Array.from({ length: EVENTS_SHOWN }, (_, i) => (
                <div key={i} className="py-4 border-b border-primary-200 min-h-[7.5rem] sm:min-h-[8rem]">
                  <div className="h-5 w-1/2 rounded-md bg-[#e5e5e5] animate-pulse" />
                  <div className="mt-3 h-3.5 w-3/4 rounded-md bg-[#e5e5e5] animate-pulse" />
                </div>
              ))}
            </div>
          </div>
        )}

        {events && events.length > 0 && (
          <>
            <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-4">
              <div>
                <p className="section-eyebrow !mb-2">{t("events.eyebrow")}</p>
                <h2 className="font-heading text-xl md:text-2xl font-bold text-[#0a0a0a] tracking-tight max-w-2xl">
                  {t("events.heading")}
                </h2>
              </div>
              <Link to={EVENTS_HREF} className="uni-link cursor-pointer self-start sm:self-auto">
                {t("common.viewAll")}
                <i className="ri-arrow-right-line" />
              </Link>
            </div>

            <div className="border-t border-primary-200">
              {events.map((event) => {
                const [day, ...monthParts] = formatShortDate(event.date, i18n.language).split(" ");
                const excerpt = stripHtml(event.content || "").trim();
                return (
                  <Link
                    key={event.id}
                    to={buildNewsDetailHref(event.slug)}
                    className="group grid sm:grid-cols-[5rem_1fr] items-start gap-4 sm:gap-6 py-4 border-b border-primary-200 cursor-pointer min-h-[7.5rem] sm:min-h-[8rem]"
                  >
                    <div className="flex sm:flex-col items-baseline sm:items-start gap-2 sm:gap-0">
                      <span className="font-heading text-3xl md:text-4xl font-semibold text-primary-950 leading-none tabular-nums">
                        {day}
                      </span>
                      <span className="text-xs uppercase tracking-wider font-semibold text-foreground-500 sm:mt-1">
                        {monthParts.join(" ")}
                      </span>
                    </div>

                    <div className="min-w-0">
                      <p className="text-[0.7rem] font-semibold uppercase tracking-[0.12em] text-primary-600">
                        {event.category?.title || t("events.eyebrow")}
                      </p>
                      <h3 className="mt-1 font-heading text-base md:text-lg font-semibold text-foreground-950 leading-snug group-hover:text-primary-700 transition-colors line-clamp-2">
                        {event.title}
                      </h3>
                      {excerpt && (
                        <p className="mt-1.5 text-sm text-foreground-500 leading-relaxed line-clamp-2 max-w-3xl">{excerpt}</p>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          </>
        )}

        <div className="mt-5 bg-primary-950 text-white p-4 md:p-5 grid lg:grid-cols-2 gap-5 overflow-hidden relative rounded-2xl">
          <div className="relative z-10">
            <p className="text-[11px] font-semibold tracking-[0.14em] uppercase text-secondary-300 mb-2">
              {t("journal.scopusIndexed")}
            </p>
            <h3 className="font-heading text-lg md:text-xl font-semibold leading-tight text-white">
              Journal of Community &amp; Public Medicine
            </h3>
            <p className="mt-3 text-sm text-white/80 leading-relaxed line-clamp-3">{t("journal.description")}</p>
            <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2">
              <Link to={JOURNAL_HREF} className="uni-btn-gold cursor-pointer">
                {t("journal.viewPage")}
              </Link>
              <Link to={JOURNAL_SUBMIT_HREF} className="uni-link !text-white/85 hover:!text-white cursor-pointer">
                {t("journal.submitArticle")}
              </Link>
            </div>
          </div>
          <div className="relative z-10 lg:border-l lg:border-white/15 lg:pl-6">
            <p className="text-[11px] font-semibold tracking-[0.14em] uppercase text-secondary-300 mb-2">
              {t("admission.countdownTitle")}
            </p>
            <h3 className="text-base font-semibold text-white">{t("admission.deadline")}</h3>
            <div className="mt-4 grid grid-cols-4 gap-2">
              {(cd.expired
                ? [
                    { v: "00", l: t("admission.days") },
                    { v: "00", l: t("admission.hours") },
                    { v: "00", l: t("admission.minutes") },
                    { v: "00", l: t("admission.seconds") },
                  ]
                : [
                    { v: pad2(cd.days), l: t("admission.days") },
                    { v: pad2(cd.hours), l: t("admission.hours") },
                    { v: pad2(cd.minutes), l: t("admission.minutes") },
                    { v: pad2(cd.seconds), l: t("admission.seconds") },
                  ]
              ).map((item) => (
                <div key={item.l} className="border border-white/15 py-2.5 text-center">
                  <div className="text-lg font-heading font-semibold tabular-nums text-white">{item.v}</div>
                  <div className="text-[10px] uppercase tracking-wider text-white/60 mt-0.5">{item.l}</div>
                </div>
              ))}
            </div>
            <Link to="/qabul" className="uni-link mt-4 !text-secondary-300 cursor-pointer">
              {t("admission.applyNow")}
              <i className="ri-arrow-right-line" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
