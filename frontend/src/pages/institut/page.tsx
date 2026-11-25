import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { getPage } from "@/api/pages";
import { getSettings } from "@/api/settings";
import { INSTITUTE_COUNTER } from "@/lib/instituteStats";
import type { Page } from "@/types/content";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import InnerPageLayout from "@/components/shared/InnerPageLayout";
import MenuSectionNav from "@/components/shared/MenuSectionNav";
import { useMenu } from "@/context/MenuContext";
import { INSTITUTE_ABOUT_MENU_ID, resolveMenuSection } from "@/lib/menuSection";
import { Reveal } from "@/components/Animation";
import { FOUNDED_YEAR } from "@/lib/siteConstants";
import { usePageMeta } from "@/hooks/usePageMeta";

export default function InstitutPage() {
  const { t } = useTranslation();
  const { menu } = useMenu();
  const section = resolveMenuSection(menu, INSTITUTE_ABOUT_MENU_ID);
  usePageMeta(t("footer.institutHaqida"));
  const [missionPage, setMissionPage] = useState<Page | null>(null);
  // the headline figures are the site counter an administrator edits (Sayt sozlamalari), not numbers typed into this page
  const [counter, setCounter] = useState(INSTITUTE_COUNTER);

  useEffect(() => {
    let cancelled = false;
    getSettings().then((settings) => {
      if (!cancelled && settings.counter?.students > 0) setCounter(settings.counter);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const features = [
    { icon: "ri-hospital-line", title: t("institut.feature1.title"), desc: t("institut.feature1.desc") },
    { icon: "ri-graduation-cap-line", title: t("institut.feature2.title"), desc: t("institut.feature2.desc") },
    { icon: "ri-global-line", title: t("institut.feature3.title"), desc: t("institut.feature3.desc") },
    { icon: "ri-microscope-line", title: t("institut.feature4.title"), desc: t("institut.feature4.desc") },
    { icon: "ri-team-line", title: t("institut.feature5.title"), desc: t("institut.feature5.desc") },
    { icon: "ri-heart-pulse-line", title: t("institut.feature6.title"), desc: t("institut.feature6.desc") },
  ];

  const timeline = [
    { year: FOUNDED_YEAR, title: t("institut.timeline1.title"), desc: t("institut.timeline1.desc") },
    { year: "2021", title: t("institut.timeline2.title"), desc: t("institut.timeline2.desc") },
    { year: "2022", title: t("institut.timeline3.title"), desc: t("institut.timeline3.desc") },
    { year: "2023", title: t("institut.timeline4.title"), desc: t("institut.timeline4.desc") },
    { year: "2024", title: t("institut.timeline5.title"), desc: t("institut.timeline5.desc") },
    { year: "2026", title: t("institut.timeline6.title"), desc: t("institut.timeline6.desc") },
  ];

  const stats = [
    { value: FOUNDED_YEAR, label: t("institut.statFounded") },
    { value: counter.professor_teachers.toLocaleString("en-US"), label: t("institut.statProfessors") },
    { value: `${counter.students.toLocaleString("en-US")}+`, label: t("stats.students") },
    { value: "9", label: t("institut.statPartnerCountries") },
  ];

  useEffect(() => {
    getPage("institut-missiyasi-va-kelajak-tasavvuri").then(setMissionPage).catch(() => {});
  }, []);

  return (
    <InnerPageLayout
      title={t("footer.institutHaqida")}
      breadcrumb={t("footer.institut")}
      description={t("institut.heroDescription")}
      sidebar={section && <MenuSectionNav menuId={section.sectionId} />}
    >
      <div className="space-y-8 md:space-y-10">
        <div className="page-card overflow-hidden">
          <img
            src="/images/institut-about.jpg"
            alt={t("institut.heroImageAlt")}
            width={1280}
            height={852}
            className="block aspect-video w-full object-cover sm:aspect-[5/2]"
          />
          <dl className="grid grid-cols-2 gap-px bg-background-200/80 border-t border-background-200/80 md:grid-cols-4">
            {stats.map(({ label, value }) => (
              <div key={label} className="flex flex-col-reverse gap-1 bg-white px-3 py-4 text-center">
                <dt className="text-xs text-foreground-600">{label}</dt>
                <dd className="text-xl font-heading font-bold tabular-nums text-primary-600 md:text-2xl">{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* About */}
        <section className="page-card p-5 md:p-7">
          <Reveal>
            <h2 className="section-title text-xl md:text-2xl mb-3">
              {t("institut.fullName")}
            </h2>
            <p className="text-sm text-foreground-700 leading-relaxed mb-3">
              {t("institut.aboutParagraph1")}
            </p>
            <p className="text-sm text-foreground-700 leading-relaxed mb-4">
              {t("institut.aboutParagraph2")}
            </p>
            <div className="bg-[#0a1158]/[0.06] border-l-4 border-[#ffd600] p-3 rounded-r-xl mb-4">
              <p className="text-[#0a1158] text-sm font-medium leading-relaxed">
                <i className="ri-calendar-check-line inline mr-1" />
                {t("institut.foundedNote")}
              </p>
            </div>
            <div className="flex flex-wrap gap-2.5">
              <Link
                to="/qabul"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-500 hover:bg-primary-600 text-background-50 text-sm font-semibold cursor-pointer transition-colors"
              >
                {t("institut.admission2026")} <i className="ri-arrow-right-line" />
              </Link>
              <Link
                to="/aloqa"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-primary-200 text-primary-700 hover:bg-primary-50 text-sm font-semibold cursor-pointer transition-colors"
              >
                {t("institut.contactUs")}
              </Link>
            </div>
          </Reveal>
        </section>

        {missionPage && missionPage.blocks.length > 0 && (
          <Reveal as="section" className="page-card p-4 md:p-5 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-primary-500 rounded-l-2xl" />
            <div className="w-11 h-11 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center mb-3">
              <i className="ri-flag-line text-xl" />
            </div>
            <h2 className="font-heading text-lg font-semibold text-foreground-900 mb-2">
              {t("institut.missionHeading")}
            </h2>
            <div className="cms-article cms-article--rich space-y-4">
              {missionPage.blocks
                .slice()
                .sort((a, b) => a.order - b.order)
                .map((block) => (
                  <BlockRenderer key={block.id} block={block} />
                ))}
            </div>
          </Reveal>
        )}

        {/* Features */}
        <section className="space-y-4">
          <Reveal>
            <div className="mb-4">
              <h2 className="section-title text-xl md:text-2xl">{t("institut.featuresHeading")}</h2>
            </div>
          </Reveal>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
            {features.map((f, i) => (
              <Reveal key={f.title} delay={i * 60}>
                <div className="group h-full page-card p-4 hover:-translate-y-0.5 hover:shadow-md hover:border-primary-200 transition-all duration-300 relative overflow-hidden">
                  <div className="w-10 h-10 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center mb-3 group-hover:bg-primary-500 group-hover:text-white transition-colors">
                    <i className={`${f.icon} text-lg`} />
                  </div>
                  <h3 className="font-heading text-base font-semibold text-foreground-900 mb-1">{f.title}</h3>
                  <p className="text-sm text-foreground-600 leading-relaxed">{f.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        {/* Timeline */}
        <section className="space-y-4">
          <Reveal>
            <div className="mb-4">
              <h2 className="section-title text-xl md:text-2xl">{t("institut.historyHeading")}</h2>
            </div>
          </Reveal>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {timeline.map((item, i) => (
              <Reveal key={i} delay={i * 50}>
                <div className="page-card p-4 h-full hover:border-primary-200 hover:shadow-md transition-all">
                  <span className="inline-block text-xs font-bold text-primary-600 bg-primary-50 px-2.5 py-0.5 rounded-full mb-2">
                    {item.year}
                  </span>
                  <h3 className="font-heading font-semibold text-foreground-900 text-sm">{item.title}</h3>
                  <p className="text-sm text-foreground-600 mt-1 leading-relaxed">{item.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </section>
      </div>
    </InnerPageLayout>
  );
}
