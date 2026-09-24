import { useEffect, useState } from "react";
import { useParams, useSearchParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getNewsArticle } from "@/api/news";
import type { NewsArticle } from "@/types/content";
import { ApiError } from "@/types/api";
import PageHeader from "@/components/shared/PageHeader";
import RichContent from "@/components/shared/RichContent";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import NewsSectionLayout from "@/components/shared/NewsSectionLayout";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { useRememberedContentHeight } from "@/hooks/useRememberedContentHeight";
import { stripHtml } from "@/lib/html";
import { getNewsArticleImage } from "@/lib/newsImages";
import { optimizedImageUrl } from "@/lib/imageProxy";
import { formatLongDate } from "@/lib/date";
import { Reveal } from "@/components/Animation";
import AiSummaryBlock from "@/components/ai/AiSummaryBlock";
import { NEWS_DEFAULT_MENU_ID } from "@/lib/newsSection";
import { localizeTelegramArticle } from "@/lib/uzTranslate";
import { isTelegramNewsSlug } from "@/lib/telegramNews";

export default function DetailPage() {
  const { t, i18n } = useTranslation();
  const { slug } = useParams<{ slug: string }>();
  const [searchParams] = useSearchParams();
  const menuIdParam = searchParams.get("menuId");
  const menuId = menuIdParam ? Number(menuIdParam) : NEWS_DEFAULT_MENU_ID;
  const [article, setArticle] = useState<NewsArticle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { contentRef, remembered } = useRememberedContentHeight(`detail:${slug}`, loading);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    getNewsArticle(slug, menuId)
      .then((data) => {
        setArticle(data);
        setLoading(false);
        const lang = i18n.language;
        if (isTelegramNewsSlug(slug) && lang.slice(0, 2) !== "uz") {
          localizeTelegramArticle(data, lang)
            .then((localized) => {
              setArticle(localized);
            })
            .catch(() => {});
        }
      })
      .catch((e) => setError(e instanceof ApiError && e.status !== 404 ? e.message : t("detail.loadError")))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, menuId, i18n.language]);

  usePageMeta(article?.title, article ? stripHtml(article.content).slice(0, 160) : null);

  if (loading) return <LoadingState minHeight="min-h-[80vh]" minHeightPx={remembered ?? 2200} />;
  if (error || !article) return <ErrorState message={error ?? undefined} />;

  const categorySlug = article.category?.slug;
  const heroImage = getNewsArticleImage(article);
  const hasBodyHeading = article.blocks
    ? article.blocks.some((b) => b.block_type === "heading")
    : /<h[1-6][ >]/i.test(article.content);

  return (
    <div className="text-foreground-950" ref={contentRef}>
      <PageHeader title={article.title} breadcrumb={t("detail.breadcrumb")} compact />

      <NewsSectionLayout currentSlug={categorySlug}>
        <Reveal>
          <article className="news-article">
            <div className="news-article__content">
              <div className="news-article__meta">
                {article.category && (
                  <span className="news-article__chip">
                    {article.category.slug === "telegram" ? t("news.telegram") : article.category.title}
                  </span>
                )}
                <span className="news-article__meta-item">
                  <i className="ri-calendar-line" aria-hidden />
                  {formatLongDate(article.date, i18n.language)}
                </span>
                {article.seen > 0 && (
                  <span className="news-article__meta-item">
                    <i className="ri-eye-line" aria-hidden />
                    {article.seen} {t("news.viewsSuffix")}
                  </span>
                )}
              </div>

              {heroImage && (
                <div className={`news-article__hero${categorySlug === "telegram" ? " news-article__hero--contain" : ""}`}>
                  <img src={optimizedImageUrl(heroImage, 1200)} alt={article.title} />
                  {article.isVideo && (
                    <span className="news-article__video-badge" aria-hidden>
                      <i className="ri-play-fill" />
                    </span>
                  )}
                </div>
              )}

              {article.isVideo && article.telegramUrl && (
                // Telegram's own web preview can't play video either (it marks it
                // "not_supported" and only ever gives us a poster frame) — the only way
                // to actually watch it is inside Telegram itself.
                <a
                  href={article.telegramUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="news-article__watch-video mb-5"
                >
                  <i className="ri-play-circle-fill" aria-hidden />
                  {t("news.watchOnTelegram")}
                </a>
              )}

              <AiSummaryBlock title={article.title} content={article.content} className="mb-5" />

              {/* See blog/page.tsx's identical comment: without a real h2 in
                  the body, PageHeader's h1 is followed straight by the
                  footer's h3. A Django-backed article has real ContentBlocks
                  (checked directly below); a Telegram-sourced one only has
                  raw HTML, checked the same way blog/page.tsx does for its
                  own raw-HTML pages. */}
              {!hasBodyHeading && <h2 className="sr-only">{article.title}</h2>}

              {/* Django-backed articles carry real ContentBlocks (see
                  NewsArticle.blocks's own doc comment) -- rendering those
                  through blocksToPlainText+RichContent instead, as this used
                  to, silently dropped every non-text block (images, in
                  particular) from the page, since that helper only ever
                  joins heading/paragraph/list text. A Telegram-sourced
                  article has no `blocks` at all (that feed is real HTML with
                  no Page/ContentBlock backing), so it keeps using
                  RichContent on article.content exactly as before. */}
              {article.blocks && article.blocks.length > 0 ? (
                <div className="cms-article cms-article--rich cms-article--news space-y-4">
                  {article.blocks.map((block) => (
                    <BlockRenderer key={block.id} block={block} />
                  ))}
                </div>
              ) : (
                <RichContent
                  html={article.content}
                  className="cms-article cms-article--rich cms-article--news"
                />
              )}

              {article.file && (
                <a
                  href={article.file}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="news-article__download"
                >
                  <i className="ri-file-download-line" aria-hidden />
                  {t("common.downloadFile")}
                </a>
              )}

              {article.telegramUrl && !article.isVideo && (
                <a
                  href={article.telegramUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="news-article__download"
                >
                  <i className="ri-telegram-fill" aria-hidden />
                  {t("news.openInTelegram")}
                </a>
              )}
            </div>
          </article>
        </Reveal>

        {categorySlug && categorySlug !== "telegram" && (
          <Reveal delay={120}>
            <Link
              to={`/news/${menuId}/${categorySlug}`}
              className="news-back-link"
            >
              <i className="ri-arrow-left-line" aria-hidden />
              {article.category?.title ?? t("news.title")}
            </Link>
          </Reveal>
        )}
      </NewsSectionLayout>
    </div>
  );
}
