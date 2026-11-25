import { Fragment, type ReactNode } from "react";
import { BlockRenderer } from "@/blocks/BlockRenderer";
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
        <section className="article-person">
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
    case "block":
      return <BlockRenderer block={section.block} />;
    case "section":
      if (section.pictures.length === 0) return <>{drawBlocks(section.blocks)}</>;
      if (section.side) {
        return (
          <section className="article-split">
            <div>{drawBlocks(section.blocks)}</div>
            <div className="article-aside">
              {section.pictures.map((picture) => <Figure key={picture.src} picture={picture} />)}
            </div>
          </section>
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
