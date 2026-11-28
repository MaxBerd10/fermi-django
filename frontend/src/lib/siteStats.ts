import i18n from "@/i18n";

// Self-hosted page-view tracking — see server/site-stats.mjs. No third-party service;
// the admin panel's own "Statistika" page reads this back via fetchStatsSummary().

export interface SiteStatsMonthSummary {
  month: string; // "YYYY-MM"
  total: number;
  previousTotal: number;
  dailySeries: { date: string; count: number }[];
}

export interface SiteStatsSummary {
  total: number;
  firstTrackedDate: string; // "YYYY-MM-DD" — earliest month the month picker should offer
  distinctPages: number;
  avgPerDay: number;
  today: number;
  yesterday: number;
  last7Days: number;
  previous7Days: number;
  last30Days: number;
  previous30Days: number;
  peakDay: { date: string; count: number };
  dailySeries: { date: string; count: number }[];
  topPages: { path: string; count: number }[];
  hourlyActivity: { hour: string; count: number }[];
  devices: { key: "desktop" | "mobile" | "tablet" | "other"; count: number }[];
  trafficSources: { key: "direct" | "search" | "social" | "referral"; count: number }[];
  // Added later: a server that has not been upgraded yet simply does not send them.
  visitors?: {
    today: number;
    yesterday: number;
    last7Days: number;
    previous7Days: number;
    dailySeries: { date: string; count: number }[];
    since: string | null;
  };
  languages?: { key: "uz" | "ru" | "en"; count: number }[];
  languagesSince?: string | null;
  botHits?: number;
  botsToday?: number;
}

// Captured once at module load (the initial full page load), not re-read per hit —
// document.referrer only reflects the page that led to THIS document; client-side
// route changes within the SPA never change it, which is exactly what "how did this
// visit arrive" attribution needs (the server's own Referer header on the /site-stats/hit
// request itself would only ever say "fermi.uz", since that request is same-origin).
const entryReferrer = typeof document !== "undefined" ? document.referrer : "";

const TASHKENT_DAY = typeof Intl !== "undefined" ? new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tashkent" }) : null;
const VISITOR_KEY = "fermi:visitor";

// A random id this browser makes up once a day and sends with each page view, so the admin panel can count PEOPLE, not
// only page views. It changes every day (nobody can be followed from one day to the next) and the server keeps only a
// count per day, never the id.
function dailyVisitorId(): string | undefined {
  try {
    const day = TASHKENT_DAY ? TASHKENT_DAY.format(new Date()) : new Date().toISOString().slice(0, 10);
    const saved = JSON.parse(window.localStorage.getItem(VISITOR_KEY) || "null");
    if (saved && saved.day === day && typeof saved.id === "string") return saved.id;
    const bytes = new Uint8Array(16);
    window.crypto.getRandomValues(bytes);
    const id = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
    window.localStorage.setItem(VISITOR_KEY, JSON.stringify({ day, id }));
    return id;
  } catch {
    return undefined; // storage blocked (private mode): the view still counts, the visitor just is not counted
  }
}

export function recordPageView(path: string) {
  const body = JSON.stringify({
    path,
    referrer: entryReferrer,
    language: i18n.resolvedLanguage || i18n.language,
    visitor: dailyVisitorId(),
  });
  // sendBeacon survives the page unloading right after a navigation (common right after
  // clicking a link) — fetch with keepalive is the fallback for browsers without it.
  if (navigator.sendBeacon) {
    const blob = new Blob([body], { type: "application/json" });
    if (navigator.sendBeacon("/site-stats/hit", blob)) return;
  }
  fetch("/site-stats/hit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    keepalive: true,
  }).catch(() => {
    // Best-effort — a dropped view-count hit isn't worth surfacing to the visitor.
  });
}

export async function fetchStatsSummary(): Promise<SiteStatsSummary> {
  const res = await fetch("/site-stats/summary");
  if (!res.ok) throw new Error("Statistikani yuklab bo'lmadi");
  return res.json();
}

export async function fetchMonthSummary(month: string): Promise<SiteStatsMonthSummary> {
  const res = await fetch(`/site-stats/month?month=${encodeURIComponent(month)}`);
  if (!res.ok) throw new Error("Oy statistikasini yuklab bo'lmadi");
  return res.json();
}
