/**
 * Interface texts edited in the admin panel ("Sayt matnlari") lie over the wording built into src/i18n/local.
 * The Node server puts them into index.html as a JSON data block (see injectSiteTexts in server/production-server.mjs),
 * so a page opens with the edited wording and needs no request; without that block (the dev server, or Django
 * unreachable when the page was served) they are fetched once after start-up.
 */
export type SiteTextLang = "uz" | "ru" | "en";
export type SiteTexts = Partial<Record<SiteTextLang, Record<string, string>>>;

function cleaned(data: unknown): SiteTexts | null {
  if (!data || typeof data !== "object") return null;
  const out: SiteTexts = {};
  for (const lang of ["uz", "ru", "en"] as const) {
    const bundle = (data as Record<string, unknown>)[lang];
    if (!bundle || typeof bundle !== "object") continue;
    const texts: Record<string, string> = {};
    for (const [key, value] of Object.entries(bundle as Record<string, unknown>)) {
      if (typeof value === "string" && value.trim()) texts[key] = value;
    }
    out[lang] = texts;
  }
  return out;
}

export function readInjectedSiteTexts(): SiteTexts | null {
  try {
    const block = document.getElementById("site-texts");
    return block ? cleaned(JSON.parse(block.textContent || "{}")) : null;
  } catch {
    return null;
  }
}

export async function fetchSiteTexts(): Promise<SiteTexts | null> {
  try {
    const response = await fetch("/api/v1/site-texts");
    return response.ok ? cleaned(await response.json()) : null;
  } catch {
    return null;
  }
}
