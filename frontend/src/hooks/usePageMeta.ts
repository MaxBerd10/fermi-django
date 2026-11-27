import { useEffect } from "react";
import i18n from "@/i18n";

const SITE_NAME = "FJSTI.uz";

/**
 * This is a pure client-side SPA (no SSR/prerendering), so without this,
 * every route keeps the static <title>/<meta description> from index.html —
 * a shared news/faculty/page link posted anywhere (the institute's own
 * Telegram channel included) previews as the homepage, not the actual
 * content. A page without its own title (the home page) gets the site title in
 * the language of the reader (the keys meta.siteTitle / meta.siteDescription,
 * edited in the admin like every text); index.html keeps the Uzbek one for
 * crawlers that do not run scripts. Resets to the site default on unmount so a
 * page that forgets to call this never inherits a stale title left behind by
 * the previous route.
 */
export function usePageMeta(title?: string | null, description?: string | null) {
  useEffect(() => {
    const defaults = () => ({ title: i18n.t("meta.siteTitle"), description: i18n.t("meta.siteDescription") });
    const descTag = document.querySelector('meta[name="description"]');
    const apply = () => {
      const site = defaults();
      document.title = title ? `${title} | ${SITE_NAME}` : site.title;
      descTag?.setAttribute("content", description || site.description);
    };
    apply();
    i18n.on("languageChanged", apply);
    return () => {
      i18n.off("languageChanged", apply);
      const site = defaults();
      document.title = site.title;
      descTag?.setAttribute("content", site.description);
    };
  }, [title, description]);
}
