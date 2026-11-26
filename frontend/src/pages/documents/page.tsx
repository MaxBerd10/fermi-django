import { useEffect, useState } from "react";
import "@/styles/menu-section-content.css";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getDocuments } from "@/api/documents";
import type { DocumentDetail } from "@/types/content";
import { ApiError } from "@/types/api";
import InnerPageLayout from "@/components/shared/InnerPageLayout";
import MenuSectionNav from "@/components/shared/MenuSectionNav";
import { useMenu } from "@/context/MenuContext";
import { isStructureMenuSection, resolveMenuSection } from "@/lib/menuSection";
import LeaderRichContent from "@/components/shared/LeaderRichContent";
import { LoadingState, ErrorState } from "@/components/shared/LoadingState";
import { usePageMeta } from "@/hooks/usePageMeta";
import { Reveal } from "@/components/Animation";

export default function DocumentsPage() {
  const { t } = useTranslation();
  const { menuId, slug } = useParams<{ menuId: string; slug: string }>();
  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<number | null>();
  const { menu } = useMenu();
  const section = resolveMenuSection(menu, menuId ? Number(menuId) : undefined, slug);
  const referenceSection = section && isStructureMenuSection(menu, section.sectionId) ? section : null;

  useEffect(() => {
    if (!slug) return;
    let current = true;
    setLoading(true);
    setError(null);
    setOpenId(undefined);
    getDocuments(slug, menuId ? Number(menuId) : undefined)
      .then((data) => { if (current) setDoc(data); })
      .catch((e) => {
        if (current) setError(e instanceof ApiError && e.status !== 404 ? e.message : t("common.genericError"));
      })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [slug, menuId, t]);

  usePageMeta(doc?.title);

  if (loading) return <LoadingState />;
  if (error || !doc) return <ErrorState message={error ?? undefined} />;
  const expandedId = openId === undefined && referenceSection && doc.items.length === 1
    ? doc.items[0].id : openId;

  return (
    <InnerPageLayout
      className={referenceSection ? "structure-documents" : undefined}
      title={doc.title || t("documents.fallbackTitle")}
      breadcrumb={referenceSection?.title}
      sidebar={referenceSection && <MenuSectionNav menuId={referenceSection.sectionId} currentSlug={slug} />}
    >
      {doc.items.length === 0 && (
        <Reveal>
          <p className="text-foreground-500">{t("documents.empty")}</p>
        </Reveal>
      )}

      <div className="documents-list">
        {doc.items.map((item, i) => (
          <Reveal key={item.id} delay={i * 50}>
            <div className={`document-card ${expandedId === item.id ? "document-card--open" : ""}`}>
              <button
                type="button"
                onClick={() => setOpenId(expandedId === item.id ? null : item.id)}
                className="document-card__toggle"
                aria-expanded={expandedId === item.id}
              >
                <span className="document-card__title">{item.title}</span>
                <i
                  className={`ri-arrow-down-s-line text-xl text-slate-400 transition-transform ${expandedId === item.id ? "rotate-180" : ""}`}
                  aria-hidden
                />
              </button>
              {expandedId === item.id && (
                <div className="document-card__body cms-article cms-article--menu-section">
                  <LeaderRichContent html={item.content} />
                </div>
              )}
            </div>
          </Reveal>
        ))}
      </div>
    </InnerPageLayout>
  );
}
