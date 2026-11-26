import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getDepartment, listDepartments } from "@/api/departments";
import type { DepartmentDetail, Leader } from "@/types/content";
import { ApiError } from "@/types/api";
import NotFound from "@/pages/NotFound";
import { isNotFound } from "@/lib/loadErrors";
import { Reveal } from "@/components/Animation";
import InnerPageLayout from "@/components/shared/InnerPageLayout";
import MenuSectionNav from "@/components/shared/MenuSectionNav";
import DepartmentPageContent from "@/components/shared/DepartmentPageContent";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { useRememberedContentHeight } from "@/hooks/useRememberedContentHeight";
import { stripHtml } from "@/lib/html";
import { normalizeYearLabels } from "@/lib/siteConstants";
import { DEPARTMENT_MENU_ID } from "@/lib/departmentSection";
import { useMenu } from "@/context/MenuContext";
import { INSTITUTE_ABOUT_MENU_ID, resolveMenuSection } from "@/lib/menuSection";

export default function DepartmentPage() {
  const { t } = useTranslation();
  const { menuId, slug } = useParams<{ menuId: string; slug: string }>();
  const [dept, setDept] = useState<DepartmentDetail | null>(null);
  const [head, setHead] = useState<Leader | null>(null);
  const [isFallback, setIsFallback] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const { contentRef, remembered } = useRememberedContentHeight(`department:${slug}`, loading);

  const resolvedMenuId = menuId ? Number(menuId) : undefined;
  const { menu: menuTree } = useMenu();

  useEffect(() => {
    if (!slug) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setNotFound(false);
    setIsFallback(false);
    setHead(null);

    async function load() {
      try {
        const detail = await getDepartment(slug!, resolvedMenuId);
        if (cancelled) return;
        setDept(detail);
        const headLeader = detail.leaders?.find((l) => l.isHead) ?? detail.leaders?.[0];
        if (headLeader) {
          setHead(headLeader);
        }
        return;
      } catch (e) {
        if (cancelled) return;
        const listResult = await listDepartments().catch(() => []);
        const meta = listResult.find((item) => item.slug === slug);
        if (!meta) {
          if (!cancelled) {
            setNotFound(isNotFound(e));
            setError(isNotFound(e) ? null : e instanceof ApiError ? e.message : t("common.genericError"));
          }
          return;
        }

        if (cancelled) return;

        setDept({
          id: 0,
          title: meta.title,
          img: meta.img,
          slug: meta.slug,
          content: "",
          blocks: [],
          menu: null,
          leaders: [],
        });
        setIsFallback(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, menuId, t]);

  usePageMeta(dept?.title, dept ? stripHtml(dept.content).slice(0, 160) : null);

  // Department "about" articles routinely run several thousand pixels tall
  // (staff card + full CMS body) -- a first-ever cold load has no remembered
  // height yet, so this cold-start default is picked from real measured
  // department pages (~1,000-11,000px) rather than the old 80vh, which was
  // an order of magnitude short and shoved the footer down by that whole gap.
  if (loading) return <LoadingState minHeight="min-h-[80vh]" minHeightPx={remembered ?? 3600} />;
  if (notFound) return <NotFound />;
  if (error || !dept) return <ErrorState message={error ?? undefined} />;

  // A department record opened from the "Institut haqida" menu ("Institut tarixi") is a page of that section, not a kafedra:
  // its list is the section's, and it gets no kafedra banner.
  const inInstituteSection = resolvedMenuId === INSTITUTE_ABOUT_MENU_ID
    || resolveMenuSection(menuTree, resolvedMenuId, slug)?.sectionId === INSTITUTE_ABOUT_MENU_ID;
  const sidebarMenuId = inInstituteSection ? INSTITUTE_ABOUT_MENU_ID : DEPARTMENT_MENU_ID;
  const displayTitle = normalizeYearLabels(dept.title.trim());

  return (
    <InnerPageLayout
      className={inInstituteSection ? undefined : "academic-layout"}
      title={displayTitle}
      breadcrumb={inInstituteSection ? t("footer.institutHaqida") : t("nav.section.kafedralar")}
      contentRef={contentRef}
      sidebar={<MenuSectionNav menuId={sidebarMenuId} currentSlug={slug} />}
    >
      <Reveal>
        <DepartmentPageContent
          key={dept.slug}
          department={dept}
          inInstituteSection={inInstituteSection}
          head={head}
          isFallback={isFallback}
        />
      </Reveal>
    </InnerPageLayout>
  );
}
