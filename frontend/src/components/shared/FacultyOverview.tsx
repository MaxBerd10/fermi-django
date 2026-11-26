import { useState } from "react";
import { useTranslation } from "react-i18next";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import LinkifiedText from "@/blocks/LinkifiedText";
import { getFacultyPageConfig } from "@/lib/facultySection";
import type { ContentBlock } from "@/types/blocks";

const pediatricPrograms = [
  { title: "faculty.program.pediatrics", codes: "60910300", heading: 26922, description: 26923 },
  { title: "faculty.program.dentistry", codes: "60910100", heading: 26924, description: 26925 },
  { title: "faculty.program.pharmacy", codes: "60910700 / 60910800", heading: 26920, description: 26921 },
];

const facultySections: Record<string, {
  intro: number;
  items?: { heading: number; first: number; last: number; title: string; icon: string };
}> = {
  "davolash-ishi": { intro: 26892 },
  "pediatriya-fakulteti": {
    intro: 26919,
    items: { heading: 26930, first: 26931, last: 26937, title: "faculty.departmentsTitle", icon: "ri-building-4-line" },
  },
  "tibbiy-profilaktika-va-jamoat-salomatligi-fakulteti": {
    intro: 26895,
    items: { heading: 26896, first: 26897, last: 26903, title: "faculty.departmentsTitle", icon: "ri-building-4-line" },
  },
  "xalqaro-fakultet": {
    intro: 26907,
    items: { heading: 26909, first: 26910, last: 26917, title: "faculty.internationalActivities", icon: "ri-global-line" },
  },
};

export default function FacultyOverview({ slug, blocks, logoUrl }: { slug: string; blocks: ContentBlock[]; logoUrl?: string | null }) {
  const { t } = useTranslation();
  const { introKey, missionKey, stats } = getFacultyPageConfig(slug);
  const logo = logoUrl?.trim();
  const [failedLogo, setFailedLogo] = useState<string>();
  const ordered = [...blocks].sort((a, b) => a.order - b.order);
  const byId = new Map(ordered.map((block) => [block.id, block]));
  const used = new Set<number>();
  const clinical = slug === "davolash-ishi";
  const pediatric = slug === "pediatriya-fakulteti";
  const section = facultySections[slug];
  const intro = section ? byId.get(section.intro) : undefined;
  const items = section?.items;
  const clinics = clinical ? byId.get(26894) : undefined;
  const programs = pediatric ? pediatricPrograms.flatMap((program) => {
    const heading = byId.get(program.heading);
    const description = byId.get(program.description);
    if (heading?.block_type !== "paragraph" || description?.block_type !== "paragraph") return [];
    used.add(heading.id);
    used.add(description.id);
    return [{ ...program, text: description.data.text }];
  }) : [];
  const entries = items ? ordered.filter((block) =>
    block.block_type === "paragraph" && block.id >= items.first && block.id <= items.last,
  ) : [];

  if (intro?.block_type === "paragraph") {
    const preceding = pediatric ? byId.get(26918) : undefined;
    if (preceding?.block_type === "paragraph" && preceding.data.text.trim() === intro.data.text.trim()) {
      used.add(preceding.id);
    }
  }
  if (clinics?.block_type === "list") used.add(clinics.id);
  if (items && entries.length) {
    const heading = byId.get(items.heading);
    if (heading?.block_type === "paragraph") used.add(heading.id);
    entries.forEach((block) => used.add(block.id));
  }

  const remaining = ordered.filter((block) => !used.has(block.id));
  const article = (
    <div className="academic-page__article faculty-page__article cms-article cms-article--rich cms-article--menu-section cms-article--fakultet space-y-4">
      {remaining.map((block) => <BlockRenderer key={block.id} block={block} />)}
    </div>
  );

  return (
    <section className="faculty-overview" aria-labelledby="faculty-about-heading">
      <h2 id="faculty-about-heading" className="academic-page__title">{t("faculty.aboutTitle")}</h2>
      <div className="faculty-overview__summary">
        <div className="faculty-overview__intro">
          {logo && failedLogo !== logo && (
            <div className="faculty-hero__logo-wrap">
              <img src={logo} alt="" className="faculty-hero__logo" onError={() => setFailedLogo(logo)} />
            </div>
          )}
          <p className="faculty-overview__lead">{t(introKey)}</p>
        </div>
        {stats.length > 0 ? (
          <ul className="faculty-overview__stats">
            {stats.map((stat) => (
              <li key={stat.labelKey + (stat.value ?? stat.valueKey)} className="faculty-overview__stat">
                <i className={stat.icon} aria-hidden />
                <span className="faculty-overview__stat-value">{stat.valueKey ? t(stat.valueKey) : stat.value}</span>
                <span className="faculty-overview__stat-label">{t(stat.labelKey)}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
      {missionKey && (
        <section className="faculty-overview__mission">
          <h3>{t("faculty.missionTitle")}</h3>
          <p>{t(missionKey)}</p>
        </section>
      )}

      {programs.length > 0 && (
        <section>
          <h3>{t("faculty.programsTitle")}</h3>
          <ul className="faculty-overview__programs">
            {programs.map((program) => (
              <li key={program.heading}>
                <span className="faculty-overview__code">{program.codes}</span>
                <h4>{t(program.title)}</h4>
                <p>{program.text}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {clinics?.block_type === "list" && (
        <section>
          <h3>{t("faculty.clinicsTitle")}</h3>
          <ul className="faculty-overview__links">
            {[...new Set(clinics.data.items)].map((item) => (
              <li key={item}><i className="ri-hospital-line" aria-hidden="true" /><span><LinkifiedText text={item} /></span></li>
            ))}
          </ul>
        </section>
      )}

      {items && entries.length > 0 && (
        <section>
          <h3>{t(items.title)}</h3>
          <ul className="faculty-overview__links">
            {entries.map((block) => block.block_type === "paragraph" && (
              <li key={block.id}><i className={items.icon} aria-hidden="true" /><span><LinkifiedText text={block.data.text.replace(/^\s*(?:\d+[.)]|[-–—])\s*/, "")} /></span></li>
            ))}
          </ul>
        </section>
      )}

      {remaining.length > 0 && ((missionKey || used.size > 0) ? (
        <details className="faculty-overview__details">
          <summary>
            <i className="ri-file-list-3-line" aria-hidden="true" />
            <span>{t("faculty.historyMore")}</span>
            <i className="ri-arrow-down-s-line" aria-hidden="true" />
          </summary>
          {article}
        </details>
      ) : article)}
    </section>
  );
}
