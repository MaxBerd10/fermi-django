import { createContext } from "react";

/**
 * The menu section the visitor is reading right now. Content links (a text link inside a page) carry it along,
 * so a page reached from another section can keep that section's list beside it instead of the list jumping
 * to the target page's own section.
 */
export const MenuSectionOriginContext = createContext<number | undefined>(undefined);

/** Addresses of pages that belong to this single-page app; other links (files, outside sites) are left to the browser. */
const APP_ROUTE_RE = /^\/(blog|departments|faculty|leader|news|detail|documents|galereya|video|full-gallery|yangiliklar)(\/|\?|#|$)/;

/** The in-app path of a content link, or null when the browser should handle it. */
export function inAppPath(href: string, origin: string): string | null {
  try {
    const url = new URL(href, origin);
    if (url.origin !== origin) return null;
    const path = url.pathname + url.search + url.hash;
    return APP_ROUTE_RE.test(path) ? path : null;
  } catch {
    return null;
  }
}
