import { useEffect, useState } from "react";
import { API_PAGE_SIZE } from "@/lib/pagination";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { listNews } from "@/api/news";
import { listTelegramNews } from "@/api/telegram";
import type { NewsArticle } from "@/types/content";
import { mergeNewsByDate } from "@/lib/telegramNews";
import { localizeTelegramCards } from "@/lib/uzTranslate";
import PageHeader from "@/components/shared/PageHeader";
import NewsSectionLayout from "@/components/shared/NewsSectionLayout";
import NewsCard from "@/components/shared/NewsCard";
import NewsPagination from "@/components/shared/NewsPagination";
import { ErrorState, LoadingState } from "@/components/shared/LoadingState";
import { useRememberedContentHeight } from "@/hooks/useRememberedContentHeight";
import { usePageMeta } from "@/hooks/usePageMeta";
import { Reveal } from "@/components/Animation";
import { NEWS_DEFAULT_MENU_ID } from "@/lib/newsSection";

// measured on the live site: the real content height of a first visit (desktop 1350 px / phone 390 px)
const TELEGRAM_WAIT_MS = 2000;
const FIRST_DESKTOP = 5000;
const FIRST_PHONE = 8800;

export default function NewsPage() {
  const { t, i18n } = useTranslation();
  usePageMeta(t("news.title"));
  const [searchParams] = useSearchParams();
  const page = Number(searchParams.get("page") || "1");
  const [items, setItems] = useState<NewsArticle[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  // The list is far taller than the spinner: without a placeholder of its own size the footer jumped when the cards
  // arrived (CLS 0.17 on a desktop). A repeat visit uses the height measured last time.
  const { contentRef, remembered } = useRememberedContentHeight(`news-list:${page}`, loading);
  const firstVisitHeight = typeof window !== "undefined" && window.innerWidth >= 1024 ? FIRST_DESKTOP : FIRST_PHONE;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setFailed(false);
    let retryTimer: number | undefined;
    // Telegram posts are merged into page 1 by date. Merged AFTER the first paint they slid in among the cards and
    // pushed the whole grid down (CLS 0.26 on a desktop), so page 1 waits for them (and their translation) for up to
    // TELEGRAM_WAIT_MS; only a slower feed is merged later, as before.
    const telegramReady: Promise<NewsArticle[] | null> =
      page === 1
        ? listTelegramNews()
            .then((posts) => localizeTelegramCards(posts, i18n.language).catch(() => posts))
            .catch(() => null)
        : Promise.resolve(null);
    const early: Promise<NewsArticle[] | null> = Promise.race([
      telegramReady,
      new Promise<null>((resolve) => window.setTimeout(() => resolve(null), TELEGRAM_WAIT_MS)),
    ]);
    Promise.all([listNews(page), early])
      .then(([res, telegramEarly]) => {
        if (cancelled) return;
        setItems(telegramEarly ? mergeNewsByDate(telegramEarly, res.data) : res.data);
        setTotal(res.meta?.total ?? res.data.length);
        setLoading(false);
        if (page !== 1) return;
        const applyTelegram = (localized: NewsArticle[] | null) => {
          if (cancelled || !localized) return;
          setItems(mergeNewsByDate(localized, res.data));
          // the pager counts the server's pages only: Telegram posts are merged into page 1, not added to it
          setTotal(res.meta?.total ?? res.data.length);
        };
        if (telegramEarly) return;
        telegramReady.then(applyTelegram);
        retryTimer = window.setTimeout(() => {
          listTelegramNews()
            .then((posts) => localizeTelegramCards(posts, i18n.language).catch(() => posts))
            .then(applyTelegram)
            .catch(() => {});
        }, 6000);
      })
      .catch(() => {
        if (!cancelled) {
          setFailed(true);
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
      window.clearTimeout(retryTimer);
    };
  }, [page, i18n.language]);

  const pageSize = API_PAGE_SIZE;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="text-foreground-950">
      <PageHeader
        title={t("yangiliklar.heading")}
        breadcrumb={t("news.title")}
        description={t("yangiliklar.description")}
        compact
      />

      <NewsSectionLayout>
        <div ref={contentRef} style={loading ? { minHeight: `${remembered ?? firstVisitHeight}px` } : undefined}>
        {loading ? (
          <LoadingState />
        ) : failed ? (
          <ErrorState message={t("common.genericError")} />
        ) : items.length === 0 ? (
          <p className="news-empty">{t("news.empty")}</p>
        ) : (
          <>
            <Reveal>
              <div className="news-grid news-grid--institute">
                {items.map((item, i) => (
                  <NewsCard key={item.id} article={item} menuId={NEWS_DEFAULT_MENU_ID} index={i} />
                ))}
              </div>
            </Reveal>

            <Reveal delay={200}>
              <NewsPagination page={page} totalPages={totalPages} />
            </Reveal>
          </>
        )}
        </div>
      </NewsSectionLayout>
    </div>
  );
}
