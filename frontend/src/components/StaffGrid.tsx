import type { Lang, StaffMember } from "../types";
import { ResponsiveImage } from "./ResponsiveImage";

/**
 * A CSS grid with auto-fill columns — cards never stretch to fill a lone
 * empty slot, and each card's height is set by its own content (name + title
 * + bio can each be a different length per language) rather than a shared
 * fixed height that the longest one would overflow.
 */
export function StaffGrid({ staff, lang }: { staff: StaffMember[]; lang: Lang }) {
  if (staff.length === 0) return null;
  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(11rem,1fr))] gap-4">
      {staff.map((member) => (
        <article key={member.id} className="page-card flex flex-col overflow-hidden">
          {member.photo ? (
            <ResponsiveImage image={member.photo} maxWidthClass="max-w-none" className="aspect-[3/4] object-cover" />
          ) : (
            <div className="aspect-[3/4] bg-primary-50" />
          )}
          <div className="p-3">
            <p className="font-display font-bold text-primary-900 leading-snug">{member.full_name[lang]}</p>
            {member.title[lang] && (
              <p className="mt-0.5 text-sm text-foreground-600 leading-snug">{member.title[lang]}</p>
            )}
          </div>
        </article>
      ))}
    </div>
  );
}
