const SITE_URL = "https://fermi.uz";

/**
 * The address a page declares as its own (<link rel="canonical"> and og:url). index.html only has the home page's
 * address; without a per-route value every inner page told search engines it is a copy of the home page.
 */
export function canonicalUrl(pathname: string): string {
  const path = pathname.replace(/\/+$/, "");
  return SITE_URL + path;
}
