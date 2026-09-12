import type { SiteSettings } from "../types/content";
import { INSTITUTE_COUNTER } from "@/lib/instituteStats";

// Django has no site-settings model yet (out of scope for this integration
// pass — see instituteStats.ts for the same gap on the counters). Every
// caller treats a missing field as "not shown", so this is what every caller
// gets until that model exists — see getSettings() below.
const EMPTY_SETTINGS: SiteSettings = {
  setting: null,
  logo: null,
  networks: [],
  usefulSites: [],
  counter: INSTITUTE_COUNTER,
};

export async function getSettings(): Promise<SiteSettings> {
  // Django has no settings model at all yet, so this request would always
  // 404 — every caller already falls back to the exact same EMPTY_SETTINGS
  // shape, so making the request buys nothing but a guaranteed failed
  // network call (and the console/best-practices noise that comes with it).
  // Swap this back to a real apiClient.get("settings") call once that model
  // exists.
  return EMPTY_SETTINGS;
}
