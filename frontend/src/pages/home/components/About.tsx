import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getPage } from "@/api/pages";
import type { Page } from "@/types/content";
import { optimizedImageUrl } from "@/lib/imageProxy";
import { FOUNDED_YEAR } from "@/lib/siteConstants";

// The institute's own founding decree, real content migrated from the old
// site's /about/<slug> endpoint (Page has no title field, so the decree's
// own title -- always its 3rd block here, after the two short preamble
// headings "O'ZBEKISTON RESPUBLIKASI PREZIDENTINING" / "QARORI" -- and its
// first real paragraph are read positionally rather than duplicated as a
// separate i18n string).
const SLUG = "fargona-jamoat-salomatligi-tibbiyot-institutini-tashkil-etish-togrisida";

export default function About() {
  const { t } = useTranslation();
  const [page, setPage] = useState<Page | null>(null);

  useEffect(() => {
    getPage(SLUG).then(setPage).catch(() => {});
  }, []);

  if (!page) return null;

  const blocks = page.blocks.slice().sort((a, b) => a.order - b.order);
  const image = blocks.find((b) => b.block_type === "image");
  const headings = blocks.filter((b) => b.block_type === "heading");
  const heading = headings[2] ?? headings[0];

  const title = heading?.data.text ?? "";
  const introText = blocks
    .filter((b) => b.block_type === "heading" || b.block_type === "paragraph")
    .map((b) => b.data.text)
    .filter(Boolean)
    .join(" ");
  const imageFile = image?.data.image?.file;

  return (
    <section className="py-5 md:py-6 bg-transparent overflow-hidden border-t border-[#e5e5e5]/60">
      <div className="section-container relative z-10 grid lg:grid-cols-12 gap-5 lg:gap-8 lg:items-stretch">
        <div className="lg:col-span-5 flex flex-col justify-start">
          <p className="section-eyebrow !mb-1.5">{t("footer.institutHaqida")}</p>
          {title && (
            <h2 className="font-heading text-xl md:text-2xl font-bold text-[#0a0a0a] tracking-tight !leading-snug">
              {title}
            </h2>
          )}
          {introText && (
            <p className="mt-3 text-sm md:text-[0.9375rem] text-foreground-600 leading-relaxed line-clamp-[12]">
              {introText}
            </p>
          )}
          <p className="mt-3 text-sm text-foreground-700 leading-relaxed">{t("about.missionNote")}</p>
          <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm font-medium text-foreground-700">
            <span>{t("about.badgeAccreditation")}</span>
            <span className="h-3.5 w-px bg-[#e5e5e5]" aria-hidden="true" />
            <span>{t("about.badgeProfessors")}</span>
            <span className="h-3.5 w-px bg-[#e5e5e5]" aria-hidden="true" />
            <span>{t("about.badgeInternational")}</span>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2">
            <Link to={`/about/${SLUG}`} className="uni-btn cursor-pointer">
              {t("about.readMore")}
              <i className="ri-arrow-right-line" />
            </Link>
          </div>
        </div>
        <div className="lg:col-span-7 w-full lg:self-start">
          <div className="relative w-full aspect-[16/10] overflow-hidden border border-primary-100 rounded-2xl shadow-[0_12px_36px_rgba(10,17,88,0.08)] bg-background-100">
            {imageFile && (
              <img
                alt={title}
                className="absolute inset-0 w-full h-full object-cover object-center"
                src={optimizedImageUrl(imageFile, 640)}
                srcSet={[320, 480, 640, 900].map((width) => `${optimizedImageUrl(imageFile, width)} ${width}w`).join(", ")}
                sizes="(min-width: 1024px) 640px, (min-width: 640px) 50vw, 100vw"
                width={900}
                height={563}
                decoding="async"
              />
            )}
            <div className="absolute left-0 bottom-0 bg-primary-950 px-4 py-2.5 flex items-baseline gap-2">
              <span className="font-heading text-base font-semibold text-secondary-400">{FOUNDED_YEAR}</span>
              <span className="text-[0.65rem] uppercase tracking-[0.14em] text-white/70">{t("about.foundedYear")}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
