import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { ContentBlock } from "@/types/blocks";
import { optimizedImageUrl } from "@/lib/imageProxy";
import RawHtmlBlock from "./RawHtmlBlock";
import DocumentCard, { humanizeFilename } from "./DocumentCard";
import LinkifiedText from "./LinkifiedText";
import { isChapterHeading } from "@/lib/layoutBlocks";
import RoadmapPdfFrame from "./RoadmapPdfFrame";

// Django's media FileFields always serialize as absolute URLs (build_absolute_uri),
// unlike the old CMS's occasional bare "/uploads/..." path — this is just a defensive
// fallback for a value that somehow isn't absolute yet, not the normal case.
function toAbsoluteUrl(path: string): string {
  if (!path || path.startsWith("http")) return path;
  const apiOrigin = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/api\/v1\/?$/, "") || "";
  return apiOrigin ? `${apiOrigin}${path}` : path;
}

function documentHref(path: string): string {
  if (import.meta.env.DEV) {
    // Serve local uploads through the same Vite proxy as the CMS requests.
    const localMedia = path.match(/^https?:\/\/(?:127\.0\.0\.1|localhost):8000(\/media\/.*)$/i);
    if (localMedia) return localMedia[1];
  }
  return toAbsoluteUrl(path);
}

/**
 * One video. A portrait video (phone format, 9:16) would be ~1200px tall in the usual 672px column, taller than the
 * screen, so once the browser knows the real size of the video a portrait one gets a narrower column (it then fits
 * on a screen, and the player controls stay in view); a landscape video keeps the full width.
 */
function VideoBlock({ src, poster, caption }: { src: string; poster: string; caption?: string }) {
  const [portrait, setPortrait] = useState(false);
  return (
    <figure className={`mx-auto ${portrait ? "max-w-sm" : "max-w-2xl"}`}>
      <video
        controls
        preload="metadata"
        poster={poster}
        className="w-full rounded-xl"
        onLoadedMetadata={(e) => setPortrait(e.currentTarget.videoHeight > e.currentTarget.videoWidth)}
      >
        <source src={src} />
      </video>
      {caption && <figcaption className="mt-2 text-sm text-foreground-600">{caption}</figcaption>}
    </figure>
  );
}

/**
 * Renders one CMS content block (apps.content.ContentBlock) — ported from the
 * Django-content prototype's BlockRenderer, restyled with fjstiWeb-main's own
 * Tailwind tokens (same primary/secondary/foreground names, so the port is
 * near 1:1) instead of inventing a new stylesheet. `block.data` is already
 * resolved to the active language by the API client (see resolveLocale in
 * api/client.ts), so unlike the prototype this takes no `lang` prop.
 *
 * heading/paragraph/list/table render bare semantic tags with no class of
 * their own — the caller wraps a page's block list in the site's existing
 * `.cms-article`/`.prose-content` container (src/styles/cms-content.css), so
 * they get the same typography the old CKEditor-HTML content already had.
 * Only the block types with no equivalent in that freeform-HTML world
 * (staff_card/image/video/gallery/document) get their own Tailwind classes.
 *
 * A block simply grows or shrinks with whatever its content needs — no fixed
 * heights, no forced truncation — so switching uz/ru/en never breaks the
 * surrounding layout, and a malformed block can't reach this component at all
 * (the backend rejects invalid block data before it's ever saved).
 */
export function BlockRenderer({ block, documentTitle, showPdf = false }: {
  block: ContentBlock;
  documentTitle?: string;
  showPdf?: boolean;
}) {
  const { t } = useTranslation();
  switch (block.block_type) {
    case "heading":
      return block.data.level === 3 ? <h3>{block.data.text}</h3> : <h2 data-chapter={isChapterHeading(block.data.text) || undefined}>{block.data.text}</h2>;

    case "paragraph":
      // A paragraph whose text holds line breaks is a verse (poem stanza): keep its lines, see .cms-verse.
      if (block.data.text.includes("\n")) {
        return <p className="cms-verse"><LinkifiedText text={block.data.text} /></p>;
      }
      return block.data.bold ? (
        <p>
          <strong><LinkifiedText text={block.data.text} /></strong>
        </p>
      ) : (
        <p><LinkifiedText text={block.data.text} /></p>
      );

    case "list":
      return (
        <ol>
          {block.data.items.map((item, i) => (
            <li key={i}><LinkifiedText text={item} /></li>
          ))}
        </ol>
      );

    case "staff_card": {
      const { full_name, title } = block.data;
      return (
        <div className="rounded-xl border border-primary-100 bg-primary-50/40 p-4">
          <p className="font-display font-bold text-primary-900">{full_name}</p>
          {title && <p className="text-sm text-foreground-600">{title}</p>}
        </div>
      );
    }

    case "image": {
      const { image, alt, style } = block.data;
      if (!image) return null;

      if (style === "diagram") {
        return (
          <figure className="cms-diagram-page">
            <a
              href={image.file}
              target="_blank"
              rel="noopener noreferrer"
              className="cms-diagram-frame cms-diagram-frame__btn"
              aria-label={`${alt ?? image.alt_text} — ${t("structure.enlarge")}`}
            >
              <img
                src={optimizedImageUrl(image.file, 1600) || image.file}
                alt={alt ?? image.alt_text}
                width={image.width ?? undefined}
                height={image.height ?? undefined}
                decoding="async"
                className="cms-diagram-frame__img"
                onError={(event) => {
                  const preview = event.currentTarget;
                  if (preview.getAttribute("src") !== image.file) preview.src = image.file;
                }}
              />
              <span className="cms-diagram-action">
                <i className="ri-zoom-in-line" aria-hidden="true" />
                {t("structure.enlarge")}
              </span>
            </a>
          </figure>
        );
      }

      return (
        <figure className="mx-auto max-w-lg">
          <img
            src={optimizedImageUrl(image.file, 900) || image.file}
            alt={alt ?? image.alt_text}
            loading="lazy"
            width={image.width ?? undefined}
            height={image.height ?? undefined}
            className="w-full rounded-xl"
            onError={({ currentTarget }) => {
              if (currentTarget.getAttribute("src") !== image.file) currentTarget.src = image.file;
            }}
          />
        </figure>
      );
    }

    case "video": {
      const { video, caption } = block.data;
      if (!video) return null;
      return <VideoBlock src={toAbsoluteUrl(video.file)} poster={toAbsoluteUrl(video.poster.file)} caption={caption} />;
    }

    case "table": {
      const { headers, rows } = block.data;
      return (
        // max-w-full is load-bearing, not decorative: without an explicit
        // width ceiling, this wrapper's own box grows to fit a wide table
        // (e.g. grantlar-taqsimoti's 11-column combined header) instead of
        // scrolling it -- the overflow leaked out to the whole page
        // (confirmed: document.body.scrollWidth exceeded the viewport)
        // rather than staying contained in this div's own scrollbar.
        <div className="overflow-x-auto max-w-full">
          <table>
            <thead>
              <tr>
                {headers.map((header, i) => (
                  <th key={i}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i}>
                  {row.map((cell, j) => (
                    <td key={j}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    case "raw_html":
      return (
        <RawHtmlBlock
          html={block.data.html}
          className="cms-article--rich"
          pdfTitle={showPdf ? documentTitle : undefined}
        />
      );

    case "gallery": {
      const { items, style } = block.data;
      const visible = items.filter((item) => item.image);
      if (visible.length === 0) return null;

      if (style === "certificate") {
        return (
          <div className="cms-cert-page">
            <ul className="cms-cert-gallery" role="list">
              {visible.map(({ image, image_id, alt }, index) => {
                if (!image) return null;
                const title = alt?.trim() || image.alt_text?.trim();
                return (
                  <li key={image_id ?? index}>
                    <a
                      href={image.file}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="cms-cert-card cms-cert-card--link"
                      aria-label={title ? `${title} — ${t("document.open")}` : t("document.open")}
                    >
                      <div className="cms-cert-card__preview">
                        <img
                          src={optimizedImageUrl(image.file, 640) || image.file}
                          alt=""
                          loading="lazy"
                          decoding="async"
                          className="cms-cert-card__img"
                          onError={(event) => {
                            const preview = event.currentTarget;
                            if (preview.getAttribute("src") !== image.file) preview.src = image.file;
                          }}
                        />
                      </div>
                      <span className="cms-cert-card__caption">
                        <span className="cms-cert-card__title">{title || t("document.open")}</span>
                        <i className="ri-arrow-right-up-line" aria-hidden="true" />
                      </span>
                    </a>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      }

      return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {visible.map((item, i) => {
            const image = item.image!;
            return (
              <div key={item.image_id ?? i} className="aspect-square overflow-hidden rounded-lg">
                <img
                  src={optimizedImageUrl(image.file, 480) || image.file}
                  alt={item.alt ?? image.alt_text}
                  loading="lazy"
                  className="h-full w-full object-cover"
                  onError={({ currentTarget }) => {
                    if (currentTarget.getAttribute("src") !== image.file) currentTarget.src = image.file;
                  }}
                />
              </div>
            );
          })}
        </div>
      );
    }

    case "document": {
      const { document, caption, style } = block.data;
      if (!document) return null;
      const documentUrl = documentHref(document.file);

      const title = caption || document.title || documentTitle || humanizeFilename(document.filename);

      const isPdf = /\.pdf$/i.test(document.filename.trim()) || /\.pdf(?:[?#]|$)/i.test(documentUrl);
      if (style === "roadmap" || (showPdf && isPdf)) {
        return (
          <RoadmapPdfFrame
            key={documentUrl}
            src={documentUrl}
            title={title}
            filename={document.filename}
            fileSize={document.file_size}
          />
        );
      }

      return (
        <DocumentCard
          url={documentUrl}
          title={title}
          filename={document.filename}
          fileSize={document.file_size}
        />
      );
    }

    default:
      return null;
  }
}
