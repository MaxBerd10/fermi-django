import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getFaculty } from "@/api/faculty";
import type { FacultyDetail } from "@/types/content";
import { ApiError } from "@/types/api";
import NotFound from "@/pages/NotFound";
import { isNotFound } from "@/lib/loadErrors";
import { Reveal } from "@/components/Animation";
import InnerPageLayout from "@/components/shared/InnerPageLayout";
import MenuSectionNav from "@/components/shared/MenuSectionNav";
import AcademicPageHero from "@/components/shared/AcademicPageHero";
import FacultyPageContent from "@/components/shared/FacultyPageContent";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { useRememberedContentHeight } from "@/hooks/useRememberedContentHeight";
import { stripHtml } from "@/lib/html";
import { FACULTY_MENU_ID, getFacultyPageConfig } from "@/lib/facultySection";

export default function FacultyPage() {
  const { t } = useTranslation();
  const { menuId, slug } = useParams<{ menuId: string; slug: string }>();
  const [faculty, setFaculty] = useState<FacultyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const { contentRef, remembered } = useRememberedContentHeight(`faculty:${slug}`, loading);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    setNotFound(false);
    getFaculty(slug, menuId ? Number(menuId) : undefined)
      .then(setFaculty)
      .catch((e) => {
        setNotFound(isNotFound(e));
        setError(isNotFound(e) ? null : e instanceof ApiError ? e.message : t("common.genericError"));
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, menuId]);

  usePageMeta(faculty?.title, faculty ? stripHtml(faculty.content).slice(0, 160) : null);

  // See departments/page.tsx's identical comment -- cold-start default
  // picked from real measured faculty pages, not the old too-short 80vh.
  if (loading) return <LoadingState minHeight="min-h-[80vh]" minHeightPx={remembered ?? 4200} />;
  if (notFound) return <NotFound />;
  if (error || !faculty) return <ErrorState message={error ?? undefined} />;

  const config = getFacultyPageConfig(slug ?? "");

  return (
    <InnerPageLayout
      className="faculty-layout"
      title={faculty.title}
      header={
        <AcademicPageHero title={faculty.title} logoUrl={faculty.img} theme={config.theme}
          breadcrumb={t("nav.section.fakultetlar")} description={t(config.introKey)} stats={config.stats} />
      }
      contentRef={contentRef}
      sidebar={<MenuSectionNav menuId={FACULTY_MENU_ID} currentSlug={slug} />}
    >
      <Reveal>
        <FacultyPageContent faculty={faculty} slug={slug ?? ""} />
      </Reveal>
    </InnerPageLayout>
  );
}
