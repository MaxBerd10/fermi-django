import { useEffect, useMemo, useState } from "react";
import ArticleBody from "@/components/shared/ArticleBody";
import StructureArticle from "@/components/shared/StructureArticle";
import RegulatoryDocument from "@/components/shared/RegulatoryDocument";
import { useLocation, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getPage } from "@/api/pages";
import type { Page } from "@/types/content";
import { ApiError } from "@/types/api";
import NotFound from "@/pages/NotFound";
import { isNotFound } from "@/lib/loadErrors";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import LinkifiedText from "@/blocks/LinkifiedText";
import InnerPageLayout from "@/components/shared/InnerPageLayout";
import MenuSectionNav from "@/components/shared/MenuSectionNav";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { useRememberedContentHeight } from "@/hooks/useRememberedContentHeight";
import { Reveal } from "@/components/Animation";
import { useMenu } from "@/context/MenuContext";
import { findMenuTitleBySlug, INSTITUTE_ABOUT_MENU_ID, isStructureMenuSection, resolveMenuSection } from "@/lib/menuSection";
import { NEWS_SECTION_MENU_ID } from "@/lib/newsSection";
import { MenuSectionOriginContext } from "@/lib/menuSectionOrigin";
import { normalizeTechnicalCollegeHeading } from "@/lib/technicalCollegeHeading";
import { normalizeMenuHref, normalizePageSlug, normalizeYearLabels } from "@/lib/siteConstants";

// Pages drawn as a regulatory document: a table of facts (Qabul raqami: ...) above the text of the decree.
const REGULATORY_PAGE_SLUGS = new Set([
  "talim-togrisia",
  "prezident-farmon-va-qarorlari",
  "taraqqiyot-strategiyasi",
  "davlat-dasturlari",
  "oliy-talimning-davlat-talim-standarti",
  "oliy-talim-yonalishlari-va-mutaxassisliklari-klassifikatori",
  "ozbeksiton-respublikasi-ssv-buyruqlari",
]);

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
  const isScientificSection = (menuSection?.sectionId ?? resolvedMenuId) === 1993;
  const sectionTitle = menuSection?.links.find((link) => link.href === `/blog/${menuId}/${slug}`)?.title;
  const rawTitle = isScientificSection && slug === "ilmiy-kengash"
    ? t("science.dissertationLinkCouncil")
    : sectionTitle || (slug && findMenuTitleBySlug(menuTree, slug)) || menuSection?.title;
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
  const isTechnicalCollege = menuSection?.theme === "texnikum" || /texnikum/i.test(slug ?? "");
  const sortedBlocks = page.blocks.slice().sort((a, b) => a.order - b.order).map((block) => {
    if (block.block_type !== "heading" && block.block_type !== "paragraph") return block;
    const text = block.data.text;
    // the headings of the technical-college pages were typed in capitals
    const displayText = isTechnicalCollege && block.block_type === "heading"
      ? normalizeTechnicalCollegeHeading(text) : text;
    return displayText === block.data.text ? block : { ...block, data: { ...block.data, text: displayText } };
  });
  const hasEditorialGroups = slug === "avtoreferatlar" || slug === "tahrir-hayati-kengashi";
  const editorialGroups = hasEditorialGroups && sortedBlocks.some((block) => block.block_type === "heading")
    ? sortedBlocks.reduce<Array<typeof sortedBlocks>>((groups, block) => {
      if (block.block_type === "document") return groups;
      if (!groups.length || block.block_type === "heading") groups.push([]);
      groups[groups.length - 1].push(block);
      return groups;
    }, []) : null;
  // avtoreferatlar: per defence four blocks -- the council line, the author (heading), the thesis title, the PDF card -- drawn as one card each
  const autoreferatCards = slug === "avtoreferatlar" && sortedBlocks.length > 0 && sortedBlocks.length % 4 === 0
    && sortedBlocks.every((block, index) => block.block_type === (["paragraph", "heading", "paragraph", "document"] as const)[index % 4])
    ? Array.from({ length: sortedBlocks.length / 4 }, (_, index) => sortedBlocks.slice(index * 4, index * 4 + 4)) : null;
  const isStructuredCouncil = slug === "institut-ilmiy-kengashi"
    && sortedBlocks[0]?.block_type === "paragraph"
    && sortedBlocks.every(({ block_type }) =>
      block_type === "paragraph" || block_type === "heading" || block_type === "list",
    );
  const isPublicationArchive = /^(?:jcpm-\d{4}|institut-gazetasi-(?:arxivi-)?\d{4})$/.test(slug ?? "");
  const isScientificRegulatoryPage = isScientificSection
    && /normativ|normative|regulat|норматив/iu.test(`${slug ?? ""} ${title}`);
  const isRegulatoryPage = isScientificRegulatoryPage || REGULATORY_PAGE_SLUGS.has(slug ?? "");
  const documentFacts: Array<{ id: number; label: string; value: string }> = [];
  if (isRegulatoryPage) {
    for (const block of sortedBlocks) {
      if (block.block_type !== "paragraph") break;
      const fact = /^([^:\n]{2,42}):\s*(\S[^\n]*)$/.exec(block.data.text.trim());
      if (!fact) break;
      documentFacts.push({ id: block.id, label: fact[1].trim(), value: fact[2] });
    }
  }
  const isRegulatoryIndex = slug === "prezident-farmon-va-qarorlari"
    || slug === "davlat-dasturlari" || slug === "ozbeksiton-respublikasi-ssv-buyruqlari";
  // Plenty of these ~235 pages have no heading block anywhere in their body
  // (the real site's own content for them is just plain/bold paragraphs) --
  // without a real h2, PageHeader's h1 is followed straight by the footer's
  // h3, an invalid skipped heading level. A visually-hidden h2 keeps the
  // outline valid without changing anything a sighted visitor sees.
  const hasBodyHeading = sortedBlocks.some((b) => b.block_type === "heading");
  const showGrantOverview = slug === "fjsti-grant-siyosati" && sortedBlocks[0]?.block_type === "paragraph";
  const isInstituteDocument = menuSection?.sectionId === INSTITUTE_ABOUT_MENU_ID
    && sortedBlocks.length > 0
    && sortedBlocks.every((block) => block.block_type === "document" || block.block_type === "image");
  const isInstituteReference = menuSection?.theme === "institut"
    && menuSection.sectionId !== INSTITUTE_ABOUT_MENU_ID
    && menuSection.sectionId !== NEWS_SECTION_MENU_ID;
  const hasReferenceIntro = isStructureMenuSection(menuTree, menuSection?.sectionId);
  const isReferencePage = isInstituteReference || hasReferenceIntro;
  const isTextPage = isReferencePage && sortedBlocks.every(({ block_type }) =>
    block_type === "heading" || block_type === "paragraph" || block_type === "list",
  );
  const documentBlocks = sortedBlocks.filter((block) =>
    block.block_type === "document" || block.block_type === "raw_html",
  );
  // a page with exactly one document (a PDF) opens it inline, in every section; the buttons (open, download) stand above it
  const inlinePdfBlockId = documentBlocks.length === 1 ? documentBlocks[0].id : undefined;
  const breadcrumb = sidebarSection
    ? (isReferencePage || sidebarSection.breadcrumbKey === "nav.section.default" ? normalizeYearLabels(sidebarSection.title) : t(sidebarSection.breadcrumbKey))
    : t("footer.institutHaqida");

  return (
    <InnerPageLayout
      title={title}
      breadcrumb={breadcrumb}
      contentRef={contentRef}
      sidebar={sidebarSection && <MenuSectionNav menuId={sidebarSection.sectionId} currentSlug={slug} />}
    >
      {!hasBodyHeading && !showGrantOverview && <h2 className="sr-only">{title}</h2>}
      <Reveal>
        {sortedBlocks.length > 0 ? (
          <article className={`page-card px-5 py-4 md:px-7 md:py-5 lg:px-8 lg:py-6 cms-article cms-article--rich space-y-4 article-body${isInstituteDocument ? " article-document" : ""}${isReferencePage ? " institute-reference" : ""}${hasReferenceIntro ? " reference-intro" : ""}${isTextPage ? " institute-reference--text" : ""}${slug === "ilmiy-kengash" ? " cms-article--council-decisions council-archive" : ""}${isPublicationArchive ? " publication-archive" : ""}${isRegulatoryPage ? " regulatory-archive" : ""}${isRegulatoryIndex ? " regulatory-archive--index" : ""}`}
          >
            <MenuSectionOriginContext.Provider value={sidebarSection?.sectionId}>
              {showGrantOverview && <h2>{t("science.grantOverview")}</h2>}
              {isStructuredCouncil ? (
                <div className="cms-article--council council-overview">
                  <div className="cms-council-intro"><BlockRenderer block={sortedBlocks[0]} /></div>
                  {sortedBlocks.slice(1).map((block) => {
                    const items = block.block_type === "list" ? block.data.items
                      : block.block_type === "paragraph"
                        ? block.data.text.split(";").map((item) => item.trim()).filter(Boolean)
                        : [];
                    if (block.block_type !== "list" && items.length < 2) {
                      return <BlockRenderer key={block.id} block={block} />;
                    }
                    return (
                      <ul key={block.id} className="cms-council-tasks">
                        {items.map((item, index) => <li key={index}><LinkifiedText text={item} /></li>)}
                      </ul>
                    );
                  })}
                </div>
              ) : autoreferatCards ? (
                <div className="autoreferat-grid">
                  {autoreferatCards.map((card) => (
                    <section key={card[0].id} className="autoreferat-card">
                      {card.map((block) => <BlockRenderer key={block.id} block={block} />)}
                    </section>
                  ))}
                </div>
              ) : editorialGroups ? (
                <>
                  <div className="council-abstracts">
                    {editorialGroups.map((blocks) => (
                      <section key={blocks[0].id} className="council-abstracts__entry">
                        <ArticleBody blocks={blocks} />
                      </section>
                    ))}
                  </div>
                  <ArticleBody blocks={sortedBlocks.filter((block) => block.block_type === "document")} />
                </>
              ) : isRegulatoryIndex ? (
                <div className="regulatory-index">
                  {sortedBlocks.map((block) => block.block_type === "heading" || block.block_type === "paragraph" ? (
                    <div key={block.id} className="regulatory-index__entry">
                      <LinkifiedText text={block.data.text} />
                    </div>
                  ) : (
                    <div key={block.id} className="regulatory-index__full">
                      <BlockRenderer block={block} showPdf={block.id === inlinePdfBlockId} documentTitle={title} />
                    </div>
                  ))}
                </div>
              ) : documentFacts.length >= 2 ? (
                <>
                  <dl className="cms-regulatory__metadata">
                    {documentFacts.map(({ id, label, value }) => (
                      <div key={id} className="cms-regulatory__meta-row">
                        <dt>{label}</dt>
                        <dd><LinkifiedText text={value} /></dd>
                      </div>
                    ))}
                  </dl>
                  <RegulatoryDocument blocks={sortedBlocks.slice(documentFacts.length)} inlinePdfBlockId={inlinePdfBlockId} title={title} />
                </>
              ) : isRegulatoryPage ? (
                <RegulatoryDocument blocks={sortedBlocks} inlinePdfBlockId={inlinePdfBlockId} title={title} />
              ) : <StructureArticle blocks={sortedBlocks} inlinePdfBlockId={inlinePdfBlockId} title={title} slug={slug} />}
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
