import { useState } from "react";
import { useTranslation } from "react-i18next";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import { getFacultyPageConfig } from "@/lib/facultySection";
import type { ContentBlock } from "@/types/blocks";

/** The page's blocks, in two groups: a heading together with the block right after it (a paragraph or a list) is a section shown open; every other block
 * (loose paragraphs) goes into the "more" accordion, in the order it has on the page. The structure is in the blocks, edited in the admin. */
function splitSections(ordered: ContentBlock[]) {
  const sections: ContentBlock[][] = [];
  const loose: ContentBlock[] = [];
  for (let i = 0; i < ordered.length; i += 1) {
    const block = ordered[i];
    const next = ordered[i + 1];
    if (block.block_type === "heading" && (next?.block_type === "paragraph" || next?.block_type === "list")) {
      sections.push([block, next]);
      i += 1;
    } else if (block.block_type === "heading") {
      sections.push([block]);
    } else {
      loose.push(block);
    }
  }
  return { sections, loose };
}

export default function FacultyOverview({ slug, blocks, logoUrl }: { slug: string; blocks: ContentBlock[]; logoUrl?: string | null }) {
  const { t } = useTranslation();
  const { introKey, missionKey, stats } = getFacultyPageConfig(slug);
  const logo = logoUrl?.trim();
  const [failedLogo, setFailedLogo] = useState<string>();
  const { sections, loose } = splitSections([...blocks].sort((a, b) => a.order - b.order));
  const articleClass = "academic-page__article faculty-page__article cms-article cms-article--rich cms-article--menu-section cms-article--fakultet space-y-4";

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

      {sections.length > 0 && (
        <div className={articleClass}>
          {sections.flat().map((block) => <BlockRenderer key={block.id} block={block} />)}
        </div>
      )}

      {loose.length > 0 && (
        <details className="faculty-overview__details">
          <summary>
            <i className="ri-file-list-3-line" aria-hidden="true" />
            <span>{t("faculty.historyMore")}</span>
            <i className="ri-arrow-down-s-line" aria-hidden="true" />
          </summary>
          <div className={articleClass}>
            {loose.map((block) => <BlockRenderer key={block.id} block={block} />)}
          </div>
        </details>
      )}
    </section>
  );
}
