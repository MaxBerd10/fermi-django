import { useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useMenu } from "@/context/MenuContext";
import {
  isMenuSectionLinkActive,
  resolveMenuSection,
  type MenuSectionLink,
} from "@/lib/menuSection";
import { normalizeYearLabels } from "@/lib/siteConstants";
// See NewsSectionNav.tsx's identical copy of this comment -- cms-content.css
// is the file that actually defines .cms-sidebar/__head/__link(--active),
// not just supplementary styling, and this nav also renders on pages
// without RichContent mounted alongside it (e.g. the Xorijiy-talabalar news
// fallback).
import "@/styles/cms-content.css";
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

export default function MenuSectionNav({
  menuId,
  currentSlug,
}: {
  menuId: number;
  currentSlug?: string;
}) {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const { menu } = useMenu();
  const [query, setQuery] = useState("");

  const section = useMemo(
    () => resolveMenuSection(menu, menuId, currentSlug),
    [menu, menuId, currentSlug],
  );

  const filteredLinks = useMemo(() => {
    if (!section) return [];
    const q = query.trim().toLowerCase();
    if (!q) return section.links;
    return section.links.filter((l) => l.title.toLowerCase().includes(q));
  }, [section, query]);

  if (!section) return null;

  const showSearch = section.links.length >= 12;

  return (
    <nav
      className={`cms-sidebar menu-sidebar menu-sidebar--${section.theme} sticky top-24 max-h-[calc(100vh-7rem)] overflow-hidden flex flex-col`}
      aria-label={section.title}
    >
      <div className="cms-sidebar__head">{normalizeYearLabels(section.title)}</div>

      {showSearch && (
        <div className="menu-sidebar__search-wrap">
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("nav.menuSearchPlaceholder")}
            className="menu-sidebar__search"
            aria-label={t("nav.menuSearchPlaceholder")}
          />
        </div>
      )}

      <ul className="menu-sidebar__list overflow-y-auto flex-1 min-h-0">
        {filteredLinks.map((link) => (
          <MenuLinkItem
            key={link.id}
            link={link}
            active={isMenuSectionLinkActive(link, pathname, currentSlug)}
            sectionId={section.sectionId}
          />
        ))}
        {filteredLinks.length === 0 && (
          <li className="menu-sidebar__empty">{t("leader.noSearchResults")}</li>
        )}
      </ul>
    </nav>
  );
}

function MenuLinkItem({ link, active, sectionId }: { link: MenuSectionLink; active: boolean; sectionId: number }) {
  return (
    <li>
      <Link
        to={link.href}
        state={{ menuSection: sectionId }}
        className={`cms-sidebar__link menu-sidebar__link ${active ? "cms-sidebar__link--active" : ""}`}
        style={{ paddingLeft: `calc(1.25rem + ${link.depth * 0.65}rem)` }}
      >
        {normalizeYearLabels(link.title)}
      </Link>
    </li>
  );
}
