import { useEffect, useMemo, useState } from "react";
import InstituteHistoryArticle from "@/components/shared/InstituteHistoryArticle";
import ArticleBody from "@/components/shared/ArticleBody";
import { useLocation, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getPage } from "@/api/pages";
import type { Page } from "@/types/content";
import { ApiError } from "@/types/api";
import NotFound from "@/pages/NotFound";
import { isNotFound } from "@/lib/loadErrors";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import InnerPageLayout from "@/components/shared/InnerPageLayout";
import MenuSectionNav from "@/components/shared/MenuSectionNav";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { useRememberedContentHeight } from "@/hooks/useRememberedContentHeight";
import { Reveal } from "@/components/Animation";
import { useMenu } from "@/context/MenuContext";
import { findMenuTitleBySlug, resolveMenuSection } from "@/lib/menuSection";
import { MenuSectionOriginContext } from "@/lib/menuSectionOrigin";
import { normalizeMenuHref, normalizePageSlug, normalizeYearLabels } from "@/lib/siteConstants";

/**
 * Generic renderer for every static/informational page pulled from the old
 * site (bylaws, council/journal archives, admission info, building
 * descriptions, ...) — one template, driven entirely by real ContentBlock
 * data (see BlockRenderer) plus the app's own menu tree for title/sidebar.
 * No per-slug special-casing.
 */
export default function BlogPage() {
  const { t } = useTranslation();
  const { menuId, slug } = useParams<{ menuId: string; slug: string }>();
  const [page, setPage] = useState<Page | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const { contentRef, remembered } = useRememberedContentHeight(`blog:${slug}`, loading);

  const resolvedMenuId = menuId ? Number(menuId) : undefined;
  const { menu: menuTree } = useMenu();
  const menuSection = useMemo(
    () => resolveMenuSection(menuTree, resolvedMenuId, slug),
    [menuTree, resolvedMenuId, slug],
  );
  // A page reached through a link inside another section's page (Faoliyat > Doktorantura links to the
  // specialty pages of Abiturient > Doktorantura) keeps THAT section's list beside it, as long as the page is
  // not itself one of that section's entries -- the list does not jump away from where the visitor was.
  const clickedSectionId = (useLocation().state as { menuSection?: number } | null)?.menuSection;
  const originSection = useMemo(
    () =>
      typeof clickedSectionId === "number" && clickedSectionId !== menuSection?.sectionId
        ? resolveMenuSection(menuTree, clickedSectionId)
        : null,
    [menuTree, clickedSectionId, menuSection?.sectionId],
  );
  const sidebarSection =
    originSection && slug && !originSection.links.some((link) => link.href.endsWith(`/${slug}`)) ? originSection : menuSection;
  const rawTitle = (slug && findMenuTitleBySlug(menuTree, slug)) || menuSection?.title;
  // Same year-rename Navbar.tsx already applies to this exact label when rendering
  // the nav link itself — without it, a page reached via a "-2026" URL would show
  // its own stale "-2025" title even though the link the visitor clicked said 2026.
  const title = (rawTitle && normalizeYearLabels(rawTitle)) || t("footer.institutHaqida");

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setNotFound(false);
    getPage(normalizePageSlug(slug), resolvedMenuId)
      .then((data) => {
        if (!cancelled) setPage(data);
      })
      .catch((e) => {
        if (!cancelled) {
          setNotFound(isNotFound(e));
          setError(isNotFound(e) ? null : e instanceof ApiError ? e.message : t("common.genericError"));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, menuId, t]);

  usePageMeta(title);

  // See departments/page.tsx's identical comment -- this generic CMS-page
  // template covers ~235 pages of widely varying length; the cold-start
  // default is a conservative median from real measured pages, not 80vh.
  if (loading) return <LoadingState minHeight="min-h-[80vh]" minHeightPx={remembered ?? 2600} />;
  if (notFound) return <NotFound />;
  if (error || !page) return <ErrorState message={error ?? undefined} />;

  // Every page of a menu section keeps the section list beside it, "Institut haqida" included -- without it
  // a visitor reading the section page by page loses the list and has to go back to the menu each time.
  const isHistoryPage = slug === "institut-tarixi";
  const sortedBlocks = page.blocks.slice().sort((a, b) => a.order - b.order);
  // Plenty of these ~235 pages have no heading block anywhere in their body
  // (the real site's own content for them is just plain/bold paragraphs) --
  // without a real h2, PageHeader's h1 is followed straight by the footer's
  // h3, an invalid skipped heading level. A visually-hidden h2 keeps the
  // outline valid without changing anything a sighted visitor sees.
  const isMissionPage = slug === "institut-missiyasi-va-kelajak-tasavvuri";
  const isInstituteAboutPage = slug === "institut-xaqida";
  const hasBodyHeading = sortedBlocks.some((b) => b.block_type === "heading");

  return (
    <InnerPageLayout
      title={title}
      breadcrumb={sidebarSection ? t(sidebarSection.breadcrumbKey) : t("footer.institutHaqida")}
      contentRef={contentRef}
      sidebar={sidebarSection && <MenuSectionNav menuId={sidebarSection.sectionId} currentSlug={slug} />}
    >
      {!hasBodyHeading && <h2 className="sr-only">{title}</h2>}
      <Reveal>
        {isHistoryPage && sortedBlocks.length > 0 ? (
          <InstituteHistoryArticle blocks={sortedBlocks} />
        ) : sortedBlocks.length > 0 ? (
          <article className={`page-card px-5 py-4 md:px-7 md:py-5 lg:px-8 lg:py-6 cms-article cms-article--rich space-y-4${isMissionPage ? " institute-mission" : ""} article-body`}
          >
            <MenuSectionOriginContext.Provider value={sidebarSection?.sectionId}>
              {!isInstituteAboutPage ? <ArticleBody blocks={sortedBlocks} /> : sortedBlocks.map((block) =>
                isInstituteAboutPage && block.block_type === "raw_html" && block.data.slug === slug ? (
                  <div key={block.id} className="grid items-center gap-5 md:grid-cols-2 lg:gap-8">
                    <div className="min-w-0">
                      <h2>{t("institut.fullName")}</h2>
                      <p>{t("institut.aboutParagraph1")}</p>
                      <p>{t("institut.aboutParagraph2")}</p>
                    </div>
                    <BlockRenderer block={block} />
                  </div>
                ) : (
                  <BlockRenderer
                    key={block.id}
                    block={block}
                    documentTitle={isInstituteAboutPage ? t("institut.ecaqaDocument") : undefined}
                  />
                ),
              )}
            </MenuSectionOriginContext.Provider>
          </article>
        ) : (
          <div className="page-card px-5 py-8 text-center">
            <i className="ri-file-list-3-line text-3xl text-slate-300" aria-hidden />
            <p className="mt-3 text-sm text-slate-500">{t("department.emptyContent")}</p>
          </div>
        )}
      </Reveal>
    </InnerPageLayout>
  );
}
