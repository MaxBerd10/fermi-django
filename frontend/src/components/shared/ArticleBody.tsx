import { Fragment, type ReactNode } from "react";
import { BlockRenderer } from "@/blocks/BlockRenderer";
import LinkifiedText from "@/blocks/LinkifiedText";
import { optimizedImageUrl } from "@/lib/imageProxy";
import { layoutBlocks, type Picture, type Section } from "@/lib/layoutBlocks";
import type { ContentBlock } from "@/types/blocks";

/** Draws the sections of `layoutBlocks`. All the decisions (what goes beside what) are made there; this only draws. */
function PictureImg({ picture }: { picture: Picture }) {
  const small = optimizedImageUrl(picture.src, 640);
  return (
    <img
      src={small || picture.src}
      alt={picture.alt}
      width={picture.width ?? undefined}
      height={picture.height ?? undefined}
      loading="lazy"
      decoding="async"
      onError={(event) => {
        const image = event.currentTarget;
        if (image.getAttribute("src") !== picture.src) image.src = picture.src;
        else image.closest("figure")?.setAttribute("hidden", "");
      }}
    />
  );
}

function Figure({ picture }: { picture: Picture }) {
  return (
    <figure className={picture.tall ? "article-tall" : undefined}>
      <PictureImg picture={picture} />
    </figure>
  );
}

/** Pictures in a row of their own: one in the middle, two or more as a small gallery. */
function PictureRow({ pictures }: { pictures: Picture[] }) {
  if (pictures.length === 1) return <figure className="article-single"><PictureImg picture={pictures[0]} /></figure>;
  return (
    <div className="article-gallery">
      {pictures.map((picture) => <Figure key={picture.src} picture={picture} />)}
    </div>
  );
}

function drawBlocks(blocks: ContentBlock[]): ReactNode {
  return blocks.map((block) => <BlockRenderer key={block.id} block={block} />);
}

function SectionView({ section }: { section: Section }) {
  // a section the admin marked as a panel (the heading's "Karta" mark): the same section inside a highlighted card
  if (section.kind === "section" && section.panel) {
    return <div className="article-panel"><SectionView section={{ ...section, panel: false }} /></div>;
  }
  switch (section.kind) {
    case "opening":
      return (
        <section className="article-hero">
          <figure><PictureImg picture={section.picture} /></figure>
          <div><BlockRenderer block={section.text} /></div>
        </section>
      );
    case "quote":
      return (
        <section className="article-quote">
          <figure><PictureImg picture={section.picture} /></figure>
          <div><BlockRenderer block={section.text} /></div>
        </section>
      );
    case "person":
      return (
        <section className={section.card ? "article-person article-person--card" : "article-person"}>
          <figure><PictureImg picture={section.picture} /></figure>
          <div>
            <BlockRenderer block={section.heading} />
            {drawBlocks(section.text)}
          </div>
        </section>
      );
    case "footer":
      return (
        <>
          <div className="article-source"><BlockRenderer block={section.source} /></div>
          <div className="article-slogan"><BlockRenderer block={section.slogan} /></div>
          <div className="article-contact"><BlockRenderer block={section.contact} /></div>
        </>
      );
    case "dated":
      return (
        <div className="article-timeline">
          {section.before && section.before.block_type === "list" && (
            <ul className="article-timeline__events">
              {section.before.data.items.map((item, index) => <li key={index}><LinkifiedText text={item} /></li>)}
            </ul>
          )}
          <dl className="article-chronology">
            {section.entries.map(({ period, text }, index) => (
              <div key={index}>
                <dt>{period}</dt>
                <dd>{text}</dd>
              </div>
            ))}
          </dl>
        </div>
      );
    case "story":
      return (
        <section className="article-story">
          <BlockRenderer block={section.heading} />
          <div className="article-story__feature">
            <div><BlockRenderer block={section.lead} /></div>
            <figure><PictureImg picture={section.picture} /></figure>
          </div>
          <div className="article-story__body">{drawBlocks(section.body)}</div>
        </section>
      );
    case "step":
      return (
        <article className="article-step">
          <div className="article-step__head">
            <span className="article-step__num">{section.number}</span>
            <BlockRenderer block={section.heading} />
          </div>
          <div className="article-step__body">{drawBlocks(section.text)}</div>
        </article>
      );
    case "block":
      return <BlockRenderer block={section.block} />;
    case "section":
      if (section.pictures.length === 0) return <>{drawBlocks(section.blocks)}</>;
      if (section.side) {
        // the lead: the text up to the first list or table sits beside the big picture, the rest (the lists) runs under both
        const cut = section.lead ? section.blocks.findIndex((block) => block.block_type === "list" || block.block_type === "table") : -1;
        const beside = cut > 0 ? section.blocks.slice(0, cut) : section.blocks;
        const below = cut > 0 ? section.blocks.slice(cut) : [];
        return (
          <>
            <section className={section.lead ? "article-split article-split--lead" : "article-split"}>
              <div>{drawBlocks(beside)}</div>
              <div className="article-aside">
                {section.pictures.map((picture) => <Figure key={picture.src} picture={picture} />)}
              </div>
            </section>
            {drawBlocks(below)}
          </>
        );
      }
      return (
        <>
          {drawBlocks(section.blocks)}
          <PictureRow pictures={section.pictures} />
        </>
      );
  }
}

export default function ArticleBody({ blocks }: { blocks: ContentBlock[] }) {
  return (
    <>
      {layoutBlocks(blocks).map((section, index) => (
        <Fragment key={index}>
          <SectionView section={section} />
        </Fragment>
      ))}
    </>
  );
}
