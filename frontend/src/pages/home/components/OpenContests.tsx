import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getNewsCategory } from "@/api/news";
import type { NewsArticle } from "@/types/content";
import { Reveal } from "@/components/Animation";
import { formatShortDate } from "@/lib/date";
import { getNewsArticleImage } from "@/lib/newsImages";
import { optimizedImageUrl } from "@/lib/imageProxy";

/**
 * "Ochiq tanlovlar": a home-page shelf for the announcements in the "Tanlovlar" news category, so a contest
 * call does not sink down the news feed as newer posts arrive. Nothing to maintain by hand: a post filed in
 * that category shows up here, and it leaves the shelf after SHOW_DAYS (or when it is unpublished / moved to
 * another category in the admin panel). With no recent contest the whole section renders nothing.
 */
const SHOW_DAYS = 60;
const MAX_CARDS = 3;
const CONTESTS_PATH = "/news/0/tanlovlar";

export default function OpenContests() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<NewsArticle[]>([]);

  useEffect(() => {
    let cancelled = false;
    getNewsCategory("tanlovlar")
      .then((res) => {
        if (cancelled) return;
        const oldest = Date.now() - SHOW_DAYS * 24 * 60 * 60 * 1000;
        setItems(res.data.items.filter((post) => new Date(post.date).getTime() >= oldest).slice(0, MAX_CARDS));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [i18n.language]);

  if (items.length === 0) return null;

  return (
    <section id="tanlovlar" className="py-5 md:py-6 bg-transparent">
      <div className="section-container">
        <Reveal>
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-2 mb-4">
            <div>
              <p className="inline-flex items-center gap-2 text-[11px] font-semibold tracking-[0.1em] uppercase text-[#0a1158] mb-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#ffd600]" aria-hidden />
                {t("contests.eyebrow")}
              </p>
              <h2 className="font-heading text-xl md:text-2xl font-bold text-[#0a0a0a] tracking-tight leading-tight">
                {t("contests.heading")}
              </h2>
            </div>
            <Link
              to={CONTESTS_PATH}
              className="inline-flex items-center gap-1.5 self-start md:self-auto h-9 px-3.5 rounded-full bg-white border border-[#e5e5e5] text-sm font-semibold text-[#0a1158] hover:border-[#ffd600] transition-colors cursor-pointer"
            >
              {t("contests.viewAll")}
              <i className="ri-arrow-right-line" />
            </Link>
          </div>
        </Reveal>

        <div className="grid gap-3 md:gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((post, i) => {
            const image = getNewsArticleImage(post);
            return (
              <Reveal key={post.id} delay={i * 40}>
                <Link
                  to={`/detail/${post.slug}`}
                  className="group flex h-full gap-3.5 p-3 rounded-[1.35rem] bg-white/95 border border-[#e5e5e5]/80 shadow-sm hover:shadow-md hover:border-[#ffd600] transition-all cursor-pointer"
                >
                  <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl overflow-hidden bg-[#e5e5e5] shrink-0">
                    {image ? (
                      <img
                        src={optimizedImageUrl(image, 240)}
                        alt={post.title}
                        width={112}
                        height={112}
                        className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-500"
                        loading="lazy"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-[#555555]">
                        <i className="ri-award-line text-3xl" />
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex flex-col">
                    <span className="text-[11px] font-semibold text-[#555555] uppercase tracking-wide">
                      {formatShortDate(post.date, i18n.language)}
                    </span>
                    <h3 className="mt-1 font-heading text-[15px] font-bold text-[#0a0a0a] leading-snug line-clamp-3 group-hover:text-[#0a1158] transition-colors">
                      {post.title}
                    </h3>
                    <span className="mt-auto pt-2 inline-flex items-center gap-1 text-sm font-bold text-[#0a1158]">
                      {t("contests.apply")}
                      <i className="ri-arrow-right-line" />
                    </span>
                  </div>
                </Link>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
