import type { ContentBlock, Lang } from "../types";

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
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 text-balance">
          {block.data[lang].text}
        </h2>
      );

    case "paragraph":
      return (
        <p className="text-base leading-relaxed text-slate-700 text-left">
          {block.data[lang].text}
        </p>
      );

    case "list":
      return (
        <ol className="list-decimal space-y-2 pl-6 text-slate-700">
          {block.data[lang].items.map((item, i) => (
            <li key={i} className="leading-relaxed">
              {item}
            </li>
          ))}
        </ol>
      );

    case "staff_card": {
      const { full_name, title } = block.data[lang];
      return (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="font-semibold text-slate-900">{full_name}</p>
          {title && <p className="text-sm text-slate-600">{title}</p>}
        </div>
      );
    }

    case "image":
      // Resolved separately by the page (needs the Image registry) — see
      // DepartmentPage's imageMap. Kept as a documented block type for
      // ad-hoc in-body images distinct from the formal staff/logo fields.
      return null;

    default:
      return null;
  }
}
