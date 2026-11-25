import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getLeaders } from "@/api/leaders";
import type { LeadersResponse } from "@/types/content";
import { ApiError } from "@/types/api";
import NotFound from "@/pages/NotFound";
import { isNotFound } from "@/lib/loadErrors";
import { Reveal } from "@/components/Animation";
import InnerPageLayout from "@/components/shared/InnerPageLayout";
import LeaderSectionNav from "@/components/shared/LeaderSectionNav";
import LeaderProfileCard from "@/components/shared/LeaderProfileCard";
import LeaderListToolbar from "@/components/shared/LeaderListToolbar";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { useRememberedContentHeight } from "@/hooks/useRememberedContentHeight";
import {
  getLeaderPageIntroKey,
  isLeaderFeaturedPage,
  isVacantLeader,
  LEGACY_LEADER_SECTION_MENU_ID,
  LEADER_SECTION_MENU_ID,
} from "@/lib/leaderSection";

export default function LeaderPage() {
  const { t, i18n } = useTranslation();
  const { menuId, slug } = useParams<{ menuId: string; slug: string }>();
  const [data, setData] = useState<LeadersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<number | null | undefined>();

  const resolvedMenuId = menuId ? Number(menuId) : undefined;
  const isLeaderSection =
    resolvedMenuId === LEADER_SECTION_MENU_ID || resolvedMenuId === LEGACY_LEADER_SECTION_MENU_ID;
  const isProrectorPage = slug === "prorektorlar";
  const isDepartmentPage = slug === "kafedra-mudirlari";
  const { contentRef, remembered } = useRememberedContentHeight(`leader:${slug}`, loading);
  // Cold-start default varies wildly by route: "kafedra-mudirlari" lists
  // every department head (~30 photo cards, several thousand px tall),
  // "prorektorlar" lists 5, a single rektor/prorektor bio is much shorter --
  // see departments/page.tsx's identical comment for why this matters.
  const coldStartMinHeight = isDepartmentPage ? 3200 : isProrectorPage ? 1800 : 900;

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    setNotFound(false);
    setQuery("");
    setOpenId(undefined);
    getLeaders(slug, resolvedMenuId)
      .then(setData)
      .catch((e) => {
        setNotFound(isNotFound(e));
        setError(isNotFound(e) ? null : e instanceof ApiError ? e.message : t("common.genericError"));
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug, menuId, i18n.language]);

  const leaders = useMemo(
    () => (data?.leaders ?? []).filter((l) => !isVacantLeader(l.name)),
    [data?.leaders],
  );

  const filteredLeaders = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return leaders;
    return leaders.filter(
      (l) =>
        l.name.toLowerCase().includes(q) ||
        l.position.toLowerCase().includes(q) ||
        l.email?.toLowerCase().includes(q),
    );
  }, [leaders, query]);

  const title = slug === "rektor" ? t("leadership.rectorLabel")
    : isProrectorPage ? t("leader.title.prorectors")
      : isDepartmentPage ? t("leader.title.departmentHeads")
        : data?.category.title;

  usePageMeta(title);

  if (loading) return <LoadingState minHeightPx={remembered ?? coldStartMinHeight} />;
  if (notFound) return <NotFound />;
  if (error || !data) return <ErrorState message={error ?? undefined} />;

  const introKey = getLeaderPageIntroKey(slug);
  const featured = isLeaderFeaturedPage(slug, leaders.length);
  const showToolbar = isProrectorPage || isDepartmentPage;

  const expandedId = openId === undefined && featured ? leaders[0]?.id : openId;

  return (
    <InnerPageLayout
      title={title ?? data.category.title}
      breadcrumb={isLeaderSection ? t("leader.breadcrumb") : title}
      contentRef={contentRef}
      sidebar={isLeaderSection && <LeaderSectionNav currentSlug={slug} />}
    >
      {introKey && (
        <Reveal>
          <p className="leader-section__intro">{t(introKey)}</p>
        </Reveal>
      )}

      {leaders.length === 0 && (
        <Reveal>
          <div className="page-card px-5 py-8 text-center">
            <p className="text-foreground-500">{t("leader.empty")}</p>
          </div>
        </Reveal>
      )}

      {showToolbar && leaders.length > 0 && (
        <LeaderListToolbar
          query={query}
          onQueryChange={setQuery}
          total={leaders.length}
          filtered={filteredLeaders.length}
          showSearch={isDepartmentPage || leaders.length > 4}
        />
      )}

      {leaders.length > 0 && filteredLeaders.length === 0 && (
        <p className="leader-empty-search">{t("leader.noSearchResults")}</p>
      )}

      <div className="leader-prorector-list">
        {filteredLeaders.map((leader) => (
          <LeaderProfileCard
            key={`${leader.id}:${leader.photo ?? ""}`}
            leader={leader}
            roleLabel={slug === "rektor" ? t("leadership.rectorLabel") : isDepartmentPage
              ? t("leader.role.departmentHead") : isProrectorPage ? t("leader.role.prorector") : undefined}
            rector={featured}
            open={expandedId === leader.id}
            onToggle={() => setOpenId(expandedId === leader.id ? null : leader.id)}
          />
        ))}
      </div>
    </InnerPageLayout>
  );
}
