import { Link, useLocation } from "react-router-dom";
import { useLeaderSectionNav } from "@/hooks/useLeaderSectionNav";
import { isLeaderNavItemActive } from "@/lib/leaderSection";
import { normalizeMenuHref, normalizeYearLabels } from "@/lib/siteConstants";
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

export default function LeaderSectionNav({ currentSlug }: { currentSlug?: string }) {
  const { pathname } = useLocation();
  const { title, items } = useLeaderSectionNav();

  if (items.length === 0) return null;

  return (
    <nav
      className="cms-sidebar leader-sidebar sticky top-24 max-h-[calc(100vh-7rem)] overflow-y-auto"
      aria-label={title}
    >
      <div className="cms-sidebar__head">{normalizeYearLabels(title)}</div>
      <ul>
        {items.map((item) => {
          const href = normalizeMenuHref(item.href);
          const active = isLeaderNavItemActive(item, pathname, currentSlug);
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
