// The production server proxies this route and keeps the iMentor credential private.
// Keeping the path relative also works behind a reverse proxy and on any domain.
import { FEATURES } from "@/lib/featureFlags";

const BASE_URL = "/imentor-api";

export async function imentorGet<T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  if (!FEATURES.imentor) {
    // No iMentor API key configured for this deployment — fail immediately
    // rather than fetching a proxy route that isn't wired up. The pages that
    // call this (/test, /keyslar) already render their existing error state
    // gracefully, and Navbar.tsx only links to them once this same flag is on,
    // so this only matters for a visitor landing on the URL directly.
    throw new Error("iMentor is not available in this deployment");
  }
  const url = new URL(BASE_URL.replace(/\/$/, "") + "/" + path.replace(/^\//, ""), window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) url.searchParams.set(key, String(value));
    }
  }

  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error(`iMentor API xatosi: ${response.status}`);
  }

  return response.json() as Promise<T>;
}
