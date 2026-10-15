/**
 * The quick buttons of the home page's top section are edited in the admin panel ("Bosh sahifa bloklari -> Tezkor
 * tugmalar"). They sit in the first screen, so the Node server puts them into index.html as a JSON data block
 * (`<script id="home-tools">`, see createInjectedJson in server/production-server.mjs): the page paints with the
 * edited buttons and needs no request first. Without the block (dev server, Django unreachable when the page was
 * served) the built-in buttons show until /api/v1/home-sections answers.
 */
import { resolveLocale } from "@/api/client";
import type { HomeTool } from "@/api/homeSections";

type Lang = "uz" | "ru" | "en";

let cached: unknown | undefined;

/** The block's raw content ({uz, ru, en} per text), or null when the page came without it. */
export function readInjectedHomeTools(): unknown[] | null {
  if (cached === undefined) {
    try {
      const block = document.getElementById("home-tools");
      const parsed = block ? JSON.parse(block.textContent || "{}") : null;
      cached = parsed && Array.isArray(parsed.tools) ? parsed.tools : null;
    } catch {
      cached = null;
    }
  }
  return cached as unknown[] | null;
}

export function resolveHomeTools(raw: unknown[], lang: Lang): HomeTool[] {
  return resolveLocale<HomeTool[]>(raw, lang);
}
