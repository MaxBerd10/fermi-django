import { useId, useState, type ReactNode, type Ref } from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import PageHeader from "./PageHeader";

interface ContentProps {
  children: ReactNode;
  sidebar?: ReactNode;
  className?: string;
}

export function InnerPageContent({ children, sidebar, className }: ContentProps) {
  const { t } = useTranslation();
  const sidebarId = useId();
  const { pathname } = useLocation();
  const [openPath, setOpenPath] = useState<string | null>(null);
  const menuOpen = openPath === pathname;

  return (
    <section className={`inner-page-content ${className ?? ""}`}>
      <div className="section-container inner-page-grid" data-sidebar={sidebar ? "" : undefined}>
        {sidebar && (
          <button
            type="button"
            className="inner-page-menu"
            aria-expanded={menuOpen}
            aria-controls={sidebarId}
            onClick={() => setOpenPath(menuOpen ? null : pathname)}
          >
            {t("innerPage.sectionPages")}
            <i className={menuOpen ? "ri-arrow-up-s-line" : "ri-arrow-down-s-line"} aria-hidden="true" />
          </button>
        )}
        {sidebar && (
          <aside id={sidebarId} className="inner-page-sidebar" data-open={menuOpen}>
            {sidebar}
          </aside>
        )}
        <div className="inner-page-body">{children}</div>
      </div>
    </section>
  );
}

export default function InnerPageLayout({
  title,
  breadcrumb,
  description,
  contentRef,
  header,
  className,
  children,
  sidebar,
}: ContentProps & {
  title: string;
  header?: ReactNode;
  breadcrumb?: string;
  description?: string;
  contentRef?: Ref<HTMLDivElement>;
}) {
  return (
    <div className={`text-foreground-950 ${className ?? ""}`} ref={contentRef}>
      {header ?? <PageHeader title={title} breadcrumb={breadcrumb} description={description} compact />}
      <InnerPageContent sidebar={sidebar}>{children}</InnerPageContent>
    </div>
  );
}
