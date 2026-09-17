import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getPage } from "@/api/pages";
import type { Page } from "@/types/content";
import { ApiError } from "@/types/api";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import PageHeader from "@/components/shared/PageHeader";
import { Reveal } from "@/components/Animation";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { normalizeYearLabels } from "@/lib/siteConstants";

// Page has no title field of its own (see PageSerializer -- just
// {id, slug, blocks}), and this route carries no menuId to resolve a
// breadcrumb label from the menu tree the way /blog/:menuId/:slug does.
// Humanizing the slug is the only title source available here.
function titleFromSlug(slug: string): string {
  return slug
    .split("-")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export default function AboutPage() {
  const { t } = useTranslation();
  const { slug } = useParams<{ slug: string }>();
  const [page, setPage] = useState<Page | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    getPage(slug)
      .then(setPage)
      .catch((e) => setError(e instanceof ApiError && e.status !== 404 ? e.message : t("common.genericError")))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  const displayTitle = normalizeYearLabels(slug ? titleFromSlug(slug) : "");

  usePageMeta(displayTitle);

  if (loading) return <LoadingState />;
  if (error || !page) return <ErrorState message={error ?? undefined} />;

  return (
    <div className="text-foreground-950">
      <PageHeader title={displayTitle} breadcrumb={t("footer.institutHaqida")} />
      <section className="section-pad bg-transparent">
        <div className="section-container max-w-4xl">
          <Reveal>
            <article className="page-card p-5 md:p-7 lg:p-8 cms-article space-y-4">
              {page.blocks
                .slice()
                .sort((a, b) => a.order - b.order)
                .map((block) => (
                  <BlockRenderer key={block.id} block={block} />
                ))}
            </article>
          </Reveal>
        </div>
      </section>
    </div>
  );
}
