import { Link } from "react-router-dom";
import type { ReactNode } from "react";

interface Props {
  /** Where "Orqaga" goes (the list this record belongs to). */
  backTo: string;
  saving: boolean;
  /** True while there are edits that were not saved yet. */
  dirty: boolean;
  /** "14:32" of the last successful save in this session. */
  savedAt?: string | null;
  saveLabel?: string;
  /** Extra buttons to the left of "Saqlash" (e.g. "Saytda ko'rish"). */
  children?: ReactNode;
}

/** The save bar stuck to the bottom of the screen: a long form never hides "Saqlash" below the fold, and the bar says
 *  whether the editor still has unsaved work. Sits inside the page's padding, so it spans the full content width. */
export default function FormActionBar({ backTo, saving, dirty, savedAt, saveLabel = "Saqlash", children }: Props) {
  return (
    <div className="sticky bottom-0 z-20 -mx-4 mt-6 border-t border-background-200 bg-background-50/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
      <div className="mx-auto flex max-w-6xl items-center gap-3">
        <Link
          to={backTo}
          className="flex h-10 items-center gap-1.5 rounded-lg border border-background-300 px-4 text-sm font-medium text-foreground-700 hover:bg-background-100"
        >
          <i className="ri-arrow-left-line" aria-hidden="true" />
          <span className="hidden sm:inline">Orqaga</span>
        </Link>

        <div className="min-w-0 flex-1 text-sm" aria-live="polite">
          {dirty ? (
            <span className="flex items-center gap-2 text-amber-800">
              <span className="h-2 w-2 shrink-0 rounded-full bg-amber-500" aria-hidden="true" />
              <span className="truncate">Saqlanmagan o'zgarishlar bor</span>
            </span>
          ) : savedAt ? (
            <span className="flex items-center gap-2 text-green-700">
              <i className="ri-checkbox-circle-line shrink-0" aria-hidden="true" />
              <span className="truncate">Saqlandi, {savedAt}</span>
            </span>
          ) : null}
        </div>

        {children}

        <button
          type="submit"
          disabled={saving}
          className="flex h-10 min-w-28 cursor-pointer items-center justify-center gap-2 rounded-lg bg-primary-500 px-6 text-sm font-semibold text-background-50 hover:bg-primary-600 disabled:opacity-60"
        >
          {saving && <i className="ri-loader-4-line animate-spin" aria-hidden="true" />}
          {saving ? "Saqlanmoqda..." : saveLabel}
        </button>
      </div>
    </div>
  );
}
