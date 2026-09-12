import type { ContentBlock } from "@/types/blocks";
import { optimizedImageUrl } from "@/lib/imageProxy";

// Django's media FileFields always serialize as absolute URLs (build_absolute_uri),
// unlike the old CMS's occasional bare "/uploads/..." path — this is just a defensive
// fallback for a value that somehow isn't absolute yet, not the normal case.
function toAbsoluteUrl(path: string): string {
  if (!path || path.startsWith("http")) return path;
  const apiOrigin = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/api\/v1\/?$/, "") || "";
  return apiOrigin ? `${apiOrigin}${path}` : path;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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
export function BlockRenderer({ block }: { block: ContentBlock }) {
  switch (block.block_type) {
    case "heading":
      return <h2>{block.data.text}</h2>;

    case "paragraph":
      return <p>{block.data.text}</p>;

    case "list":
      return (
        <ol>
          {block.data.items.map((item, i) => (
            <li key={i}>{item}</li>
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
      const { image, alt } = block.data;
      if (!image) return null;
      return (
        <figure className="mx-auto max-w-lg">
          <img
            src={optimizedImageUrl(image.file, 900) || image.file}
            alt={alt ?? image.alt_text}
            loading="lazy"
            width={image.width ?? undefined}
            height={image.height ?? undefined}
            className="w-full rounded-xl"
          />
        </figure>
      );
    }

    case "video": {
      const { video, caption } = block.data;
      if (!video) return null;
      return (
        <figure className="mx-auto max-w-2xl">
          <video controls preload="metadata" poster={toAbsoluteUrl(video.poster.file)} className="w-full rounded-xl">
            <source src={toAbsoluteUrl(video.file)} />
          </video>
          {caption && <figcaption className="mt-2 text-sm text-foreground-600">{caption}</figcaption>}
        </figure>
      );
    }

    case "table": {
      const { headers, rows } = block.data;
      return (
        <div className="overflow-x-auto">
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

    case "gallery": {
      const { items } = block.data;
      const visible = items.filter((item) => item.image);
      if (visible.length === 0) return null;
      return (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {visible.map((item, i) => (
            <div key={item.image_id ?? i} className="aspect-square overflow-hidden rounded-lg">
              <img
                src={optimizedImageUrl(item.image!.file, 480) || item.image!.file}
                alt={item.alt ?? item.image!.alt_text}
                loading="lazy"
                className="h-full w-full object-cover"
              />
            </div>
          ))}
        </div>
      );
    }

    case "document": {
      const { document, caption } = block.data;
      if (!document) return null;
      return (
        <figure className="mx-auto max-w-lg">
          <a
            href={toAbsoluteUrl(document.file)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 rounded-xl border border-primary-100 bg-primary-50/40 p-4 transition hover:bg-primary-50"
          >
            <i className="ri-file-pdf-2-line text-2xl text-primary-600" aria-hidden="true" />
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
