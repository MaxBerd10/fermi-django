import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getPage } from "@/api/pages";
import type { Page } from "@/types/content";
import type { MenuNode } from "@/types/menu";
import { ApiError } from "@/types/api";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import PageHeader from "@/components/shared/PageHeader";
import MenuSectionNav from "@/components/shared/MenuSectionNav";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { Reveal } from "@/components/Animation";
import { useMenu } from "@/context/MenuContext";
import { resolveMenuSection } from "@/lib/menuSection";
import { normalizeMenuHref, normalizePageSlug, normalizeYearLabels } from "@/lib/siteConstants";

// The page's own title isn't part of the Page/ContentBlock API (see
// apps/content/serializers.py::PageSerializer) — every one of these ~235
// pages is reached from a real nav entry, and that entry's own label is
// already a real, localized title, so this looks it up there instead of
// duplicating the same string into the CMS content. Matches on `href`, not
// `urlValue` — api/menu.ts always leaves urlValue blank (see its own
// comment: Navbar never branched on it, so it was never worth deriving)
// and only `href` (Django's `url` field, already a full "/blog/:menuId/:slug"
// path) actually carries the real slug. normalizeMenuHref() first, same as
// every other renderer of this href (Navbar.tsx, menuSection.ts, ...) — the
// raw href off the menu tree can still say a stale year (e.g. "...-2025")
// that this function's own "-2026" URL slug won't literally match otherwise.
function findTitleBySlug(nodes: MenuNode[], slug: string): string | null {
  for (const node of nodes) {
    if (normalizeMenuHref(node.href)?.endsWith(`/${slug}`)) return node.title.trim();
    const found = findTitleBySlug(node.children ?? [], slug);
    if (found) return found;
  }
  return null;
}

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

  const resolvedMenuId = menuId ? Number(menuId) : undefined;
  const { menu: menuTree } = useMenu();
  const menuSection = useMemo(
    () => resolveMenuSection(menuTree, resolvedMenuId, slug),
    [menuTree, resolvedMenuId, slug],
  );
  const rawTitle = (slug && findTitleBySlug(menuTree, slug)) || menuSection?.title;
  // Same year-rename Navbar.tsx already applies to this exact label when rendering
  // the nav link itself — without it, a page reached via a "-2026" URL would show
  // its own stale "-2025" title even though the link the visitor clicked said 2026.
  const title = (rawTitle && normalizeYearLabels(rawTitle)) || t("footer.institutHaqida");

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    getPage(normalizePageSlug(slug), resolvedMenuId)
      .then((data) => {
        if (!cancelled) setPage(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof ApiError ? e.message : t("common.genericError"));
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

  if (loading) return <LoadingState />;
  if (error || !page) return <ErrorState message={error ?? undefined} />;

  const hasSidebar = Boolean(menuSection);
  const sortedBlocks = page.blocks.slice().sort((a, b) => a.order - b.order);

  return (
    <div className="text-foreground-950">
      <PageHeader
        title={title}
        breadcrumb={menuSection ? t(menuSection.breadcrumbKey) : t("footer.institutHaqida")}
        compact
      />

      <section className="section-pad !pt-3 md:!pt-4 bg-transparent pb-16 md:pb-20">
        <div
          className={`section-container grid gap-5 lg:gap-6 items-start ${hasSidebar ? "lg:grid-cols-12" : ""}`}
        >
          <div className={hasSidebar ? "lg:col-span-8 min-w-0" : "min-w-0"}>
            <Reveal>
              {sortedBlocks.length > 0 ? (
                <article className="page-card px-5 py-4 md:px-7 md:py-5 lg:px-8 lg:py-6 cms-article cms-article--rich space-y-4">
                  {sortedBlocks.map((block) => (
                    <BlockRenderer key={block.id} block={block} />
                  ))}
                </article>
              ) : (
                <div className="page-card px-5 py-8 text-center">
                  <i className="ri-file-list-3-line text-3xl text-slate-300" aria-hidden />
                  <p className="mt-3 text-sm text-slate-500">{t("department.emptyContent")}</p>
                </div>
              )}
            </Reveal>
          </div>

          {hasSidebar && resolvedMenuId && (
            <aside className="lg:col-span-4 min-w-0">
              <Reveal delay={100}>
                <MenuSectionNav menuId={resolvedMenuId} currentSlug={slug} />
              </Reveal>
            </aside>
          )}
        </div>
      </section>
    </div>
  );
}
