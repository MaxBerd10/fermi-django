// Shared by DocumentCard (a document block) and lib/fileLinkCards (a file link found inside CMS
// HTML), so the two always look the same.
export const CARD_CLASS =
  "mt-6 flex flex-col gap-4 rounded-2xl border border-primary-100 bg-primary-50/40 p-4 lg:flex-row lg:items-center lg:p-5";
export const CARD_MAIN_CLASS = "flex min-w-0 flex-1 items-center gap-4";
export const CARD_ICON_CLASS =
  "flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-[#0a1158] text-xl text-[#ffd600]";
export const CARD_TITLE_CLASS = "block font-heading text-base font-bold leading-snug text-primary-900";
export const CARD_META_CLASS = "mt-0.5 block text-sm text-foreground-600";
export const CARD_ACTIONS_CLASS = "flex flex-col gap-2.5 sm:flex-row";
export const PRIMARY_BUTTON_CLASS =
  "cms-download-btn inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-[#0a1158] px-5 text-sm font-semibold text-white shadow-md transition-colors hover:bg-[#060a3d]";
export const SECONDARY_BUTTON_CLASS =
  "cms-download-btn inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-primary-200 bg-white px-5 text-sm font-semibold text-primary-900 transition-colors hover:border-[#0a1158]";

/** Remix icon for a file extension -- all of these exist in the remixicon subset font. */
export function fileIconClass(extension: string): string {
  const ext = extension.toLowerCase();
  if (ext === "pdf") return "ri-file-pdf-2-line";
  if (ext.startsWith("xls")) return "ri-file-excel-2-line";
  return "ri-file-text-line";
}
