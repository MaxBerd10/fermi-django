import { apiClient } from "./client";
import type { SiteSettings } from "../types/content";
import { INSTITUTE_COUNTER } from "@/lib/instituteStats";

// Django has no site-settings model yet (out of scope for this integration
// pass — see instituteStats.ts for the same gap on the counters). Every caller
// treats a missing field as "not shown", so degrade to an empty shape instead
// of throwing — otherwise every one of this function's several call sites
// would need its own try/catch just to avoid an unhandled rejection.
const EMPTY_SETTINGS: SiteSettings = {
  setting: null,
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
    return EMPTY_SETTINGS;
  }
}
