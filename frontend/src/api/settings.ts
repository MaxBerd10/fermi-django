import { apiClient } from "./client";
import type { SiteSettings } from "../types/content";
import { INSTITUTE_COUNTER } from "@/lib/instituteStats";

// Real fallback (not a stub -- see git history for when Django had no
// settings model at all): only used if the request below genuinely
// fails, so a transient network error still leaves the same real
// contact info Footer.tsx already hardcodes as its own independent
// fallback, rather than every caller silently rendering nothing.
const FALLBACK_SETTINGS: SiteSettings = {
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
  try {
    const { data } = await apiClient.get<SiteSettings>("settings");
    return data;
  } catch {
    return FALLBACK_SETTINGS;
  }
}
