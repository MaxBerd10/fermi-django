/**
 * One look for the site's page forms (qabul, aloqa, virtual qabulxona, contest application).
 *
 * `.page-input` (global.css) fixes its own height, padding and font-size outside Tailwind's layer, so those
 * sizes can only be set here with `!`: left alone it collapses a field to the height of its text (a textarea to a
 * single line, whatever its `rows`).
 */
export const FORM_LABEL = "block text-sm font-semibold text-foreground-700 mb-1.5";

export const FORM_FIELD = "w-full page-input !h-12 !px-4 !text-base focus:outline-none focus:border-primary-500";

export const FORM_TEXTAREA =
  "w-full page-input !h-auto !min-h-[8rem] !px-4 !py-3 !text-base resize-y focus:outline-none focus:border-primary-500";
