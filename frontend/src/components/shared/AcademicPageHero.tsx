import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import "@/styles/faculty-content.css";
import type { FacultyStat, FacultyTheme } from "@/lib/facultySection";
import { optimizedImageUrl } from "@/lib/imageProxy";

export default function AcademicPageHero({
  title,
  logoUrl,
  theme,
  breadcrumb,
  description,
  stats = [],
}: {
  title: string;
  logoUrl?: string | null;
  theme: FacultyTheme | "department";
  breadcrumb: string;
  description: string;
  stats?: FacultyStat[];
}) {
  const { t } = useTranslation();
  const logo = logoUrl?.trim();
  const [failedLogo, setFailedLogo] = useState<string>();
  const showLogo = logo && failedLogo !== logo;

  return (
    <header className={`faculty-hero faculty-hero--${theme}`}>
      <div className="faculty-hero__inner section-container">
        <nav className="faculty-hero__breadcrumb" aria-label={breadcrumb}>
          <Link to="/">{t("common.homePage")}</Link>
          <span aria-hidden="true">/</span>
          <span>{breadcrumb}</span>
        </nav>
        <div className="faculty-hero__brand">
          {showLogo && (
            <div className="faculty-hero__logo-wrap">
              <img
                src={optimizedImageUrl(logo, 320)}
                alt={title}
                className="faculty-hero__logo"
                onError={({ currentTarget }) => {
                  if (currentTarget.getAttribute("src") !== logo) {
                    currentTarget.src = logo;
                  } else {
                    setFailedLogo(logo);
                  }
                }}
              />
            </div>
          )}
          <div>
            <h1 className="faculty-hero__title">{title}</h1>
            <p className="faculty-hero__intro">{description}</p>
          </div>
        </div>

        {stats.length > 0 && (
          <ul className="faculty-hero__stats">
            {stats.map((stat) => (
              <li key={stat.labelKey + (stat.value ?? stat.valueKey)} className="faculty-hero__stat">
                <i className={stat.icon} aria-hidden />
                <span className="faculty-hero__stat-value">{stat.valueKey ? t(stat.valueKey) : stat.value}</span>
                <span className="faculty-hero__stat-label">{t(stat.labelKey)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </header>
  );
}
