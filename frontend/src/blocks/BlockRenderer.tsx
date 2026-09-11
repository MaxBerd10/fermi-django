import type { ContentBlock, Lang } from "../types";
import { ResponsiveImage } from "../components/ResponsiveImage";

const API_BASE = "http://127.0.0.1:8000";
const toAbsoluteUrl = (path: string) => (path.startsWith("http") ? path : `${API_BASE}${path}`);

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

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

    case "table": {
      const { headers, rows } = block.data[lang];
      return (
        <div className="overflow-x-auto rounded-xl border border-primary-100">
          <table className="w-full min-w-max border-collapse text-left text-sm">
            <thead className="bg-primary-50/60">
              <tr>
                {headers.map((header, i) => (
                  <th key={i} className="px-4 py-2 font-display font-bold text-primary-900">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i} className="border-t border-primary-100">
                  {row.map((cell, j) => (
                    <td key={j} className="px-4 py-2 text-foreground-700">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    case "gallery": {
      const { items } = block.data[lang];
      const visible = items.filter((item) => item.image);
      if (visible.length === 0) return null;
      return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {visible.map((item, i) => (
            <div key={item.image_id ?? i} className="aspect-square overflow-hidden rounded-lg">
              <img
                src={toAbsoluteUrl(item.image!.file)}
                alt={item.alt ?? item.image!.alt_text}
                className="h-full w-full object-cover"
                loading="lazy"
              />
            </div>
          ))}
        </div>
      );
    }

    case "document": {
      const { document, caption } = block.data[lang];
      if (!document) return null;
      return (
        <figure className="mx-auto max-w-lg">
          <a
            href={toAbsoluteUrl(document.file)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 rounded-xl border border-primary-100 bg-primary-50/40 p-4 transition hover:bg-primary-50"
          >
            <svg viewBox="0 0 24 24" className="h-8 w-8 shrink-0 text-primary-600" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
              <path d="M14 3v5h5" />
            </svg>
            <span className="min-w-0">
              <span className="block truncate font-display font-bold text-primary-900">
                {document.title || document.filename}
              </span>
              <span className="text-sm text-foreground-600">PDF · {formatFileSize(document.file_size)}</span>
            </span>
          </a>
          {caption && <figcaption className="mt-2 text-sm text-foreground-600">{caption}</figcaption>}
        </figure>
      );
    }

    default:
      return null;
  }
}
