import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import LinkifiedText from "@/blocks/LinkifiedText";
import { optimizedImageUrl } from "@/lib/imageProxy";
import type { ContentBlock, LocalizedImage } from "@/types/blocks";

// a (nearly) square picture is a logo or an emblem: shown whole, not cropped like a photograph (the size comes from the record, or from the picture itself once it is loaded)
const isSquare = (width?: number | null, height?: number | null) => Boolean(width && height && Math.abs(width / height - 1) < 0.12);

function DepartmentImage({ image, alt }: { image: LocalizedImage; alt: string }) {
  const original = image.file;
  const [source, setSource] = useState(() => optimizedImageUrl(original, 900));
  const [loadedSquare, setLoadedSquare] = useState(false);

  if (!source) return null;

  const square = isSquare(image.width, image.height) || loadedSquare;
  return (
    <figure className={`department-article__figure${square ? " department-article__figure--square" : ""}`}>
      <img src={source} alt={alt} loading="lazy" decoding="async"
        width={image.width ?? undefined} height={image.height ?? undefined}
        onLoad={(event) => setLoadedSquare(isSquare(event.currentTarget.naturalWidth, event.currentTarget.naturalHeight))}
        onError={() => setSource(source === original ? "" : original)} />
    </figure>
  );
}

function numberedText(block: ContentBlock) {
  return block.block_type === "paragraph" && !block.data.bold
    ? block.data.text.match(/^\s*(\d{1,2})[.)]\s*(\S[\s\S]*)$/)
    : null;
}

function datedEntry(block: ContentBlock) {
  if (block.block_type !== "paragraph" || block.data.bold) return null;
  const text = block.data.text.trim();
  return text.length <= 160
    ? text.match(/^((?:18|19|20)\d{2}(?:\s*[-–—]\s*(?:18|19|20)\d{2})?)(?=[-–—.:,;\s]|$)(.*)$/s)
    : null;
}

/** The lower-case closing word of an Uzbek patronymic ("Saidova Sohibahon Abrorjon qizi", "Рахматшоев Муслимбек Нозимжон угли"): part of the name, not a lower-case word that ends a title. */
const PATRONYMIC_PARTICLE = /^(?:qizi|kizi|ogli|ugli|o[ʻʼ‘’']g[ʻʼ‘’']li|кизи|қизи|угли|ўғли)$/iu;

/**
 * A name with no portrait beside it is taken for a member of staff only when it ends like a full name (a patronymic: -ovich, -evna, qizi, oʻgʻli, -ович, -овна, кизи, угли ...).
 * Every English title in Title Case ("International Cooperation", "The Department's Research Work") looks like a name otherwise.
 */
const PATRONYMIC_END = /(?:(?:o|e|ye|yo)?v(?:ich|na)|qizi|kizi|ogli|ugli|o[ʻʼ‘’']g[ʻʼ‘’']li|(?:ов|ев|ёв)(?:ич|на)|ична|кизи|қизи|угли|ўғли)$/iu;

function looksLikeFullName(name: string): boolean {
  return PATRONYMIC_END.test(name.trim());
}

function profileName(block: ContentBlock) {
  if (block.block_type !== "heading" && !(block.block_type === "paragraph" && block.data.bold)) return;
  const text = block.data.text.trim();
  const all = text.split(/\s+/);
  const words = all.length > 2 && PATRONYMIC_PARTICLE.test(all[all.length - 1]) ? all.slice(0, -1) : all;
  if (words.length >= 2 && words.length <= 5 &&
      words.every((word) => /^[\p{L}ʻʼ’'-]+$/u.test(word)) &&
      /^\p{Lu}/u.test(words[0]) && /^\p{Lu}/u.test(words[words.length - 1]) &&
      words.filter((word) => /^\p{Lu}/u.test(word)).length >= words.length - 1) {
    return text;
  }
}

function DepartmentArticleProfile({
  name, image, role, biography,
}: {
  name: string;
  image?: LocalizedImage;
  role?: string;
  biography?: ContentBlock[];
}) {
  const { t } = useTranslation();

  return (
    <section className={`department-article__profile${image ? "" : " department-article__profile--plain"}`}>
      {image && <DepartmentImage image={image} alt={name} />}
      <div className="department-article__profile-info">
        <h3 className="leader-prorector__name">{name}</h3>
        {role && <p><LinkifiedText text={role} /></p>}
      </div>
      {biography && biography.length > 0 && (
        <details className="department-article__profile-bio">
          <summary>{t("leader.biography")}</summary>
          {biography.map((block) => <BlockRenderer key={block.id} block={block} />)}
        </details>
      )}
    </section>
  );
}

export default function DepartmentArticle({ blocks }: { blocks: ContentBlock[] }) {
  const { t } = useTranslation();
  const [selected, setSelected] = useState(0);
  const lead: ReactNode[] = [];
  const topics: { title: string; items: ReactNode[]; visible: boolean }[] = [];
  let content = lead;
  let hasLead = false;

  function addTopic(title: string, visible = false) {
    content = [];
    topics.push({ title, items: content, visible });
  }
  const staff: ReactNode[] = [];
  const media: ReactNode[] = [];

  for (let index = 0; index < blocks.length; index += 1) {
    const block = blocks[index];
    if (block.block_type === "staff_card") {
      staff.push(<DepartmentArticleProfile key={block.id} name={block.data.full_name} role={block.data.title} />);
      continue;
    }
    const name = profileName(block);
    const portrait = blocks[index + 1];

    if (name && portrait?.block_type === "image" && portrait.data.style !== "diagram" && portrait.data.image) {
      const image = portrait.data.image;
      if (!image.width || !image.height || image.height >= image.width) {
        const biography: ContentBlock[] = [];
        index += 1;
        let next = blocks[index + 1];
        let role: string | undefined;
        if (next?.block_type === "paragraph" && !next.data.bold && !numberedText(next) &&
            next.data.text.trim().length <= 120 && !/[:;]\s*$/.test(next.data.text)) {
          role = next.data.text;
          index += 1;
          next = blocks[index + 1];
        }
        while (next?.block_type === "paragraph" && !next.data.bold && !numberedText(next)) {
          biography.push(next);
          index += 1;
          next = blocks[index + 1];
        }
        staff.push(<DepartmentArticleProfile key={`${block.id}:${image.file}`} name={name} image={image}
          role={role} biography={biography} />);
        continue;
      }
    }

    const date = datedEntry(block);
    if (date) {
      const entries = [{ id: block.id, period: date[1], text: block.block_type === "paragraph" ? block.data.text.trim() : "" }];
      while (index + 1 < blocks.length) {
        const candidate = blocks[index + 1];
        const match = datedEntry(candidate);
        if (!match || candidate.block_type !== "paragraph") break;
        entries.push({ id: candidate.id, period: match[1], text: candidate.data.text.trim() });
        index += 1;
      }
      addTopic(t("department.historyPeriods"), true);
      const continuation = blocks[index + 1];
      const hasContinuation = continuation?.block_type === "paragraph" && !continuation.data.bold &&
        /^\s*(?:18|19|20)\d{2}\s*[-–—]\s*(?:18|19|20)\d{2}\b/.test(continuation.data.text);
      content.push(
        <ol className="department-article__dates" key={block.id}>
          {entries.map(({ id, period, text }) => (
            <li className="department-article__date" key={id}>
              <span className="department-article__year">{period}</span>
              <span><LinkifiedText text={text.slice(period.length).replace(/^[-–—]yil(?:larda|da)\b/i, "").replace(/^\s*[-–—:,.]\s*/, "").trim()} /></span>
            </li>
          ))}
        </ol>,
      );
      if (hasContinuation) {
        content.push(
          <details className="department-article__topic" key={continuation.id}>
            <summary>{t("department.detailsMore")}</summary>
            <div><BlockRenderer block={continuation} /></div>
          </details>,
        );
        index += 1;
      }
      continue;
    }

    if (name && looksLikeFullName(name) && blocks[index + 1]?.block_type === "paragraph") {
      // a person's name with no portrait: the same profile card, without a photo (role = a short first line, biography = the paragraphs under it)
      const biography: ContentBlock[] = [];
      let next = blocks[index + 1];
      let role: string | undefined;
      if (next?.block_type === "paragraph" && !next.data.bold && !numberedText(next) &&
          next.data.text.trim().length <= 120 && !/[:;]\s*$/.test(next.data.text) && blocks[index + 2]?.block_type === "paragraph") {
        role = next.data.text;
        index += 1;
        next = blocks[index + 1];
      }
      while (next?.block_type === "paragraph" && !next.data.bold && !numberedText(next)) {
        biography.push(next);
        index += 1;
        next = blocks[index + 1];
      }
      if (role || biography.length) {
        staff.push(<DepartmentArticleProfile key={block.id} name={name} role={role} biography={biography} />);
        continue;
      }
    }

    if (block.block_type === "heading" ||
        (block.block_type === "paragraph" && block.data.bold && block.data.text.trim().length <= 100)) {
      const title = block.data.text.trim().replace(/:\s*$/, "");
      const names = blocks[index + 1];
      const clubs = names?.block_type === "heading" || names?.block_type === "paragraph"
        ? [...names.data.text.matchAll(/[«“"]([^»”"]+)[»”"]/g)].map((match) => match[1])
        : [];
      if (clubs.length > 1 && /to[ʻ‘’']garak|круж|\bclubs?\b/i.test(title)) {
        addTopic(title, true);
        content.push(<ul className="department-article__subjects-list" key={block.id}>
          {clubs.map((name) => <li key={name}><i className="ri-team-line" aria-hidden="true" /> {name}</li>)}
        </ul>);
        index += 1;
        continue;
      }
      addTopic(title);
      if (block.data.text.trim().endsWith(":")) {
        const subjects: { id: number; text: string }[] = [];
        while (index + 1 < blocks.length) {
          const item = blocks[index + 1];
          if (item.block_type !== "paragraph" || !item.data.bold || item.data.text.trim().length > 85 ||
              /[:;]\s*$/.test(item.data.text) || blocks[index + 2]?.block_type === "image") break;
          subjects.push({ id: item.id, text: item.data.text });
          index += 1;
        }
        if (subjects.length) {
          topics[topics.length - 1].visible = true;
          content.push(<ul className="department-article__subjects-list" key={block.id}>
            {subjects.map((subject) => <li key={subject.id}><LinkifiedText text={subject.text} /></li>)}
          </ul>);
          addTopic(t("department.detailsMore"));
        }
      }
      continue;
    }

    const first = numberedText(block);
    const next = blocks[index + 1] && numberedText(blocks[index + 1]);

    if (first && next && Number(next[1]) === Number(first[1]) + 1) {
      const items = [{ id: block.id, text: first[2] }];
      while (index + 1 < blocks.length) {
        const candidate = blocks[index + 1];
        const item = numberedText(candidate);
        if (!item || Number(item[1]) !== Number(first[1]) + items.length) break;
        items.push({ id: candidate.id, text: item[2] });
        index += 1;
      }
      if (content === lead) addTopic(t("department.detailsMore"));
      content.push(
        <ol key={block.id} start={Number(first[1])} className="department-article__list">
          {items.map((item, offset) => (
            <li key={item.id} className="department-article__item">
              <span aria-hidden="true">{Number(first[1]) + offset}</span>
              <LinkifiedText text={item.text} />
            </li>
          ))}
        </ol>,
      );
    } else if (block.block_type === "image" && block.data.style !== "diagram" && block.data.image) {
      const image = block.data.image;
      const afterImage = blocks[index + 1];
      const photograph = <DepartmentImage key={`${block.id}:${image.file}`} image={image}
        alt={block.data.alt || image.alt_text} />;
      if (image.width && image.height && image.width > image.height &&
          afterImage?.block_type === "paragraph" && !afterImage.data.bold &&
          !numberedText(afterImage) && afterImage.data.text.trim().length >= 80) {
        media.push(
          <div className="department-article__feature" key={block.id}>
            {photograph}
            <BlockRenderer block={afterImage} />
          </div>,
        );
        index += 1;
      } else {
        media.push(<div className="department-article__feature" key={block.id}>{photograph}</div>);
      }
    } else if (block.block_type === "gallery" || block.block_type === "video") {
      media.push(<div className="department-article__media-wide" key={block.id}><BlockRenderer block={block} /></div>);
    } else {
      if (content === lead && !hasLead && block.block_type === "paragraph" &&
          !block.data.bold && !first && block.data.text.trim().length <= 480) {
        hasLead = true;
      } else if (content === lead) {
        addTopic(t("department.detailsMore"));
      }
      if (content === lead) {
        content.push(<div className="department-overview__lead" key={block.id}><BlockRenderer block={block} /></div>);
      } else {
        content.push(<BlockRenderer key={block.id} block={block} />);
      }
    }
  }

  const overview = [...lead, ...topics.map(({ title, items, visible }, index) => {
    if (!items.length) return null;
    return visible ? (
      <section className="department-overview__section" key={index}>
        <h3>{title}</h3>
        {items}
      </section>
    ) : (
      <details className="department-article__topic" key={index}>
        <summary>{title}</summary>
        <div className="space-y-3">{items}</div>
      </details>
    );
  }).filter(Boolean)];
  const sections = [
    { label: "department.sections.overview", items: overview },
    { label: "department.sections.staff", items: staff },
    { label: "department.sections.media", items: media },
  ];
  const active = sections[selected].items.length ? selected : sections.findIndex(({ items }) => items.length > 0);
  if (active < 0) return null;
  const hasMultipleSections = sections.filter(({ items }) => items.length > 0).length > 1;

  return (
    <>
      {hasMultipleSections && (
        <div className="department-section-switch" role="group" aria-label={t("department.aboutTitle")}>
          {sections.map(({ label, items }, index) => items.length > 0 && (
            <button key={label} type="button" aria-pressed={active === index} onClick={() => setSelected(index)}>
              {t(label)}
            </button>
          ))}
        </div>
      )}
      <div key={active} className={
        sections[active].items === staff ? "department-article__staff"
          : sections[active].items === media ? "department-article__media"
            : "department-article__flow"
      }>
        {sections[active].items}
      </div>
    </>
  );
}
