/**
 * External systems that live on their own address, in ONE place. They are on subdomains of the old
 * fjsti.uz domain today; when fjsti.uz is switched off, set the new address at build time
 * (VITE_HEMIS_URL=https://hemis.fermi.uz ...) instead of editing every page.
 */
export const HEMIS_URL = (import.meta.env.VITE_HEMIS_URL as string | undefined) || "https://hemis.fjsti.uz";
export const MOODLE_URL = (import.meta.env.VITE_MOODLE_URL as string | undefined) || "https://moodle.fjsti.uz";
export const LIBRARY_URL = (import.meta.env.VITE_LIBRARY_URL as string | undefined) || "https://library.fjsti.uz";
