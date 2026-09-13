import type { SiteSettings } from "../types/content";
import { INSTITUTE_COUNTER } from "@/lib/instituteStats";

// Django has no site-settings model yet (out of scope for this integration
// pass — see instituteStats.ts for the same gap on the counters). `setting`
// carries the same real contact info Footer.tsx already hardcodes as its
// own fallback (phone/email/address never change per-deployment here) —
// without it, any caller that renders `settings?.setting?.X` directly
// (rather than falling back like Footer.tsx does) silently shows nothing,
// which is what happened on the aloqa page's contact cards.
const EMPTY_SETTINGS: SiteSettings = {
  setting: {
    phone: "+998 95 062-23-45, +998 95 063-23-45",
    email: "info@fjsti.uz, fmioz@mail.ru",
    faks: null,
    address: "Farg'ona sh., Yangi Turon, 2-a uy",
  },
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
