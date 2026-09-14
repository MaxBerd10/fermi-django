import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useNewsSectionNav } from "@/hooks/useNewsSectionNav";
import { isNewsNavItemActive, normalizeNewsHref } from "@/lib/newsSection";
import { normalizeYearLabels } from "@/lib/siteConstants";
// .cms-sidebar__link--active (this component's active-link style) lives in
// these files alongside RichContent's own CMS-article styling -- imported
// here too since this nav can render on a page without RichContent also
// mounting. See RichContent.tsx's own copy of this comment.
import "@/styles/buildings-content.css";
import "@/styles/conference-content.css";
import "@/styles/newspaper-content.css";
import "@/styles/regulatory-content.css";
import "@/styles/science-activity-content.css";
import "@/styles/news-content.css";
import "@/styles/leader-content.css";
import "@/styles/faculty-content.css";
import "@/styles/department-content.css";
import "@/styles/menu-section-content.css";

export default function NewsSectionNav({
  currentSlug,
  showAllNews = true,
}: {
  currentSlug?: string;
  showAllNews?: boolean;
}) {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const { title, items } = useNewsSectionNav();

  const allNewsActive = pathname === "/yangiliklar";

  return (
    <nav className="cms-sidebar news-sidebar sticky top-24 max-h-[calc(100vh-7rem)] overflow-y-auto" aria-label={title}>
      <div className="cms-sidebar__head">{normalizeYearLabels(title)}</div>
      <ul>
        {showAllNews && (
          <li>
            <Link
              to="/yangiliklar"
              className={`cms-sidebar__link ${allNewsActive ? "cms-sidebar__link--active" : ""}`}
            >
              {t("news.viewAll")}
            </Link>
          </li>
        )}
        {items.map((item) => {
          const href = normalizeNewsHref(item.href);
          const active = isNewsNavItemActive(href, pathname, currentSlug);
          return (
            <li key={item.id}>
              <Link to={href} className={`cms-sidebar__link ${active ? "cms-sidebar__link--active" : ""}`}>
                {normalizeYearLabels(item.title)}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
