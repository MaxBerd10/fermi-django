import type { ContentBlock, Lang } from "../types";
import { ResponsiveImage } from "../components/ResponsiveImage";

const API_BASE = "http://127.0.0.1:8000";
const toAbsoluteUrl = (path: string) => (path.startsWith("http") ? path : `${API_BASE}${path}`);

/**
 * Each block renders itself from real, validated data for the current
 * language — no fixed heights, no text-align:justify (the source of uneven
 * word-gaps), no truncation. A block simply grows or shrinks with whatever
 * that language's text needs, so switching uz -> ru -> en never breaks the
 * layout around it, and a malformed block can't reach this component at all
 * (the backend rejects it before it's ever saved).
 */
export function BlockRenderer({ block, lang }: { block: ContentBlock; lang: Lang }) {
  switch (block.block_type) {
    case "heading":
      return (
        <h2 className="font-display text-2xl font-bold tracking-tight text-primary-900 text-balance">
          {block.data[lang].text}
        </h2>
      );

    case "paragraph":
      return (
        <p className="text-base leading-relaxed text-foreground-700 text-left">
          {block.data[lang].text}
        </p>
      );

    case "list":
      return (
        <ol className="list-decimal space-y-2 pl-6 text-foreground-700">
          {block.data[lang].items.map((item, i) => (
            <li key={i} className="leading-relaxed marker:font-semibold marker:text-primary-600">
              {item}
            </li>
          ))}
        </ol>
      );

    case "staff_card": {
      const { full_name, title } = block.data[lang];
      return (
        <div className="rounded-xl border border-primary-100 bg-primary-50/40 p-4">
          <p className="font-display font-bold text-primary-900">{full_name}</p>
          {title && <p className="text-sm text-foreground-600">{title}</p>}
        </div>
      );
    }

    case "image": {
      const { image, alt } = block.data[lang];
      if (!image) return null;
      return (
        <figure className="mx-auto">
          <ResponsiveImage
            image={{ ...image, alt_text: alt ?? image.alt_text }}
            maxWidthClass="max-w-lg"
            className="rounded-xl"
          />
        </figure>
      );
    }

    case "video": {
      const { video, caption } = block.data[lang];
      if (!video) return null;
      return (
        <figure className="mx-auto max-w-2xl">
          <video
            controls
            preload="metadata"
            poster={toAbsoluteUrl(video.poster.file)}
            className="w-full rounded-xl"
          >
            <source src={toAbsoluteUrl(video.file)} />
          </video>
          {caption && <figcaption className="mt-2 text-sm text-foreground-600">{caption}</figcaption>}
        </figure>
      );
    }

    default:
      return null;
  }
}
