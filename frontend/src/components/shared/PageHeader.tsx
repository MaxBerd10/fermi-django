import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import BrandMark from "./BrandMark";

interface PageHeaderProps {
  title: string;
  breadcrumb?: string;
  description?: string;
  compact?: boolean;
  /** Optional content rendered beside the title (e.g. a stat/CTA banner) -- sits to
   * its right on wide screens and wraps below it on narrow ones. */
  aside?: ReactNode;
}

export default function PageHeader({ title, breadcrumb, description, compact, aside }: PageHeaderProps) {
  const { t } = useTranslation();

  return (
    <section className="page-header relative overflow-hidden">
      <div className="page-header__glow" aria-hidden />
      <div className="page-header__grid" aria-hidden />

      <div className={`section-container relative z-10 ${compact ? "pt-4 pb-4 sm:pt-5 sm:pb-4 md:pt-6 md:pb-5" : "pt-4 pb-6 sm:pt-5 sm:pb-6 md:pt-6 md:pb-8"}`}>
        <nav
          className="inline-flex flex-wrap items-center gap-2 text-[10px] font-semibold tracking-wide uppercase mb-2.5 px-2.5 py-1 rounded-full bg-white/95 border border-[#e5e5e5]/80 text-[#555555] shadow-sm max-w-full"
          aria-label="Breadcrumb"
        >
          <Link to="/" className="text-[#0a1158] hover:text-[#060a3d] transition-colors cursor-pointer">
            {t("common.homePage")}
          </Link>
          <span className="text-[#ccc]">/</span>
          <span className="text-[#0a1158]">{breadcrumb || title}</span>
        </nav>

        <p className="mb-1.5">
          <BrandMark size="sm" showFull layout="inline" className="text-[#0a1158]" />
        </p>

        <div className="flex flex-wrap items-center gap-5">
          <div className="min-w-0">
            <h1 className="font-heading text-[clamp(1.45rem,3vw,2.15rem)] font-extrabold text-[#0a0a0a] leading-[1.15] tracking-tight max-w-4xl">
              {title}
            </h1>

            {description && (
              <p className="mt-3 text-base text-[#444444] max-w-2xl leading-relaxed">
                {description}
              </p>
            )}
          </div>

          {aside && <div className="flex-1 min-w-[280px] max-w-xl">{aside}</div>}
        </div>

        <div className="page-header__rule mt-6" aria-hidden />
      </div>
    </section>
  );
}
