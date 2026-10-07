import { useEffect, useState } from "react";
import { API_PAGE_SIZE } from "@/lib/pagination";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { listGallery } from "@/api/gallery";
import type { GalleryImage } from "@/types/content";
import { optimizedImageUrl } from "@/lib/imageProxy";
import { Reveal } from "@/components/Animation";
import PageHeader from "@/components/shared/PageHeader";
import NewsSectionLayout from "@/components/shared/NewsSectionLayout";
import NewsPagination from "@/components/shared/NewsPagination";
import { LoadingState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { NEWS_SECTION_MENU_ID } from "@/lib/newsSection";

export default function GaleryaPage() {
  const { t } = useTranslation();
  usePageMeta(t("gallery.eyebrow"));
  const [searchParams] = useSearchParams();
  // Three menu entries (Fotogalereya, a press-events one under Xorijiy-talabalar, Green university-2026) all open
  // this one gallery. The menu link says which section it was clicked in; show that section's list beside the
  // photos. Opened directly (or from the news section itself) it keeps the news list.
  const clickedSection = (useLocation().state as { menuSection?: number } | null)?.menuSection;
  const menuSectionId =
    typeof clickedSection === "number" && clickedSection !== NEWS_SECTION_MENU_ID ? clickedSection : undefined;
  const page = Number(searchParams.get("page") || "1");
  const [items, setItems] = useState<GalleryImage[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listGallery(page)
      .then((res) => {
        setItems(res.data);
        setTotal(res.meta?.total ?? res.data.length);
      })
      .finally(() => setLoading(false));
  }, [page]);

  const pageSize = API_PAGE_SIZE;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="text-foreground-950">
      <PageHeader title={t("gallery.eyebrow")} breadcrumb={t("news.title")} compact />

      <NewsSectionLayout intro={t("gallery.intro")} menuSectionId={menuSectionId}>
        {loading ? (
          <LoadingState />
        ) : (
          <>
            <Reveal>
              <div className="news-gallery-grid">
                {items.map((img) => (
                  <Link
                    key={img.id}
                    to={`/full-gallery/${img.id}`}
                    className="news-gallery-item group"
                  >
                    <img
                      src={optimizedImageUrl(img.img, 480)}
                      alt={img.title || t("gallery.altText")}
                      loading="lazy"
                    />
                    <div className="news-gallery-item__overlay">
                      <i className="ri-zoom-in-line opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden />
                    </div>
                  </Link>
                ))}
              </div>
            </Reveal>

            <Reveal delay={200}>
              <NewsPagination page={page} totalPages={totalPages} />
            </Reveal>
          </>
        )}
      </NewsSectionLayout>
    </div>
  );
}
