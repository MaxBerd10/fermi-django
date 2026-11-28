import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const TASHKENT = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tashkent", year: "numeric", month: "2-digit", day: "2-digit" });
const dayKey = (daysAgo = 0) => TASHKENT.format(new Date(Date.now() - daysAgo * 86_400_000));

// the statistics file exactly as the site wrote it BEFORE visitors / languages / bot counting existed
function legacyFile() {
  return {
    total: 1234,
    byDate: { [dayKey(0)]: 40, [dayKey(1)]: 55, [dayKey(2)]: 30, [dayKey(10)]: 7 },
    byPath: { "/": 600, "/qabul": 200, "/yangiliklar": 150 },
    byHour: { [`${dayKey(0)}-09`]: 12, [`${dayKey(0)}-10`]: 28 },
    byDevice: { desktop: 400, mobile: 800, tablet: 34 },
    bySource: { direct: 700, search: 400, social: 100, referral: 34 },
  };
}

let dir;
async function load() {
  process.env.SITE_STATS_DIR = dir;
  vi.resetModules();
  return import("./site-stats.mjs");
}
const files = () => readdirSync(dir).sort();
const readStats = () => JSON.parse(readFileSync(join(dir, "site-stats.json"), "utf8"));

beforeEach(() => {
  dir = mkdtempSync(join(tmpdir(), "site-stats-"));
});
afterEach(() => {
  rmSync(dir, { recursive: true, force: true });
  delete process.env.SITE_STATS_DIR;
});

describe("the statistics collected before this change", () => {
  it("shows the same numbers after the upgrade", async () => {
    writeFileSync(join(dir, "site-stats.json"), JSON.stringify(legacyFile()));
    const stats = await load();
    const summary = stats.getStatsSummary();
    expect(summary.total).toBe(1234);
    expect(summary.today).toBe(40);
    expect(summary.yesterday).toBe(55);
    expect(summary.last7Days).toBe(40 + 55 + 30);
    expect(summary.devices.find((d) => d.key === "mobile").count).toBe(800);
    expect(summary.trafficSources.find((s) => s.key === "search").count).toBe(400);
    expect(summary.topPages[0]).toEqual({ path: "/", count: 600 });
    expect(stats.getMonthSummary(dayKey(10).slice(0, 7)).total).toBeGreaterThanOrEqual(7);
  });

  it("keeps every old number in the file after new visits are written", async () => {
    writeFileSync(join(dir, "site-stats.json"), JSON.stringify(legacyFile()));
    const stats = await load();
    stats.recordHit("/qabul", { userAgent: "Mozilla/5.0 (iPhone)", referer: "" });
    stats.flushStats();
    const saved = readStats();
    expect(saved.total).toBe(1235);
    expect(saved.byDate[dayKey(0)]).toBe(41);
    expect(saved.byDate[dayKey(1)]).toBe(55);
    expect(saved.byDate[dayKey(10)]).toBe(7);
    expect(saved.byPath["/qabul"]).toBe(201);
    expect(saved.byDevice.mobile).toBe(801);
    expect(saved.bySource.search).toBe(400);
  });

  it("is copied once, byte for byte, before the new code ever writes", async () => {
    const original = JSON.stringify(legacyFile());
    writeFileSync(join(dir, "site-stats.json"), original);
    const stats = await load();
    expect(readFileSync(join(dir, "site-stats.pre-visitors.json"), "utf8")).toBe(original);
    stats.recordHit("/", { userAgent: "Mozilla/5.0" });
    stats.flushStats();
    await load(); // a restart must not overwrite the copy with the new format
    expect(readFileSync(join(dir, "site-stats.pre-visitors.json"), "utf8")).toBe(original);
  });
});

describe("a damaged statistics file", () => {
  it("is set aside, never deleted, and the newest daily backup is restored", async () => {
    writeFileSync(join(dir, "site-stats.json"), '{"total": 12, "byDate": {"2026-1');
    writeFileSync(join(dir, "site-stats.backup-2026-11-20.json"), JSON.stringify({ ...legacyFile(), total: 500 }));
    writeFileSync(join(dir, "site-stats.backup-2026-11-27.json"), JSON.stringify(legacyFile()));
    const stats = await load();
    expect(stats.getStatsSummary().total).toBe(1234);
    const corrupt = files().filter((f) => f.startsWith("site-stats.corrupt-"));
    expect(corrupt).toHaveLength(1);
    expect(readFileSync(join(dir, corrupt[0]), "utf8")).toBe('{"total": 12, "byDate": {"2026-1');
  });

  it("with no backup starts empty but still keeps the damaged file", async () => {
    writeFileSync(join(dir, "site-stats.json"), "not json at all");
    const stats = await load();
    expect(stats.getStatsSummary().total).toBe(0);
    expect(files().some((f) => f.startsWith("site-stats.corrupt-"))).toBe(true);
  });

  it("a missing file with backups present is restored from the newest backup", async () => {
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, "site-stats.backup-2026-11-27.json"), JSON.stringify(legacyFile()));
    const stats = await load();
    expect(stats.getStatsSummary().total).toBe(1234);
  });
});

describe("saving", () => {
  it("writes through a temporary file that is gone afterwards and leaves valid JSON", async () => {
    const stats = await load();
    stats.recordHit("/", { userAgent: "Mozilla/5.0" });
    stats.flushStats();
    expect(files().some((f) => f.endsWith(".tmp"))).toBe(false);
    expect(readStats().total).toBe(1);
  });

  it("keeps a daily backup and prunes to the newest 14", async () => {
    for (let i = 1; i <= 20; i++) {
      const day = String(i).padStart(2, "0");
      writeFileSync(join(dir, `site-stats.backup-2026-10-${day}.json`), JSON.stringify(legacyFile()));
    }
    writeFileSync(join(dir, "site-stats.json"), JSON.stringify(legacyFile()));
    const stats = await load();
    stats.recordHit("/", { userAgent: "Mozilla/5.0" });
    stats.flushStats();
    const backups = files().filter((f) => /^site-stats\.backup-\d{4}-\d{2}-\d{2}\.json$/.test(f));
    expect(backups.length).toBe(14);
    expect(backups).toContain(`site-stats.backup-${dayKey(0)}.json`);
    expect(backups).not.toContain("site-stats.backup-2026-10-01.json");
  });
});

describe("what is counted", () => {
  it("does not count robots and automated checkers, but counts them apart", async () => {
    const stats = await load();
    for (const userAgent of [
      "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/120.0 Safari/537.36",
      "Mozilla/5.0 (Macintosh) Chrome-Lighthouse",
      "curl/8.4.0",
      "python-requests/2.31",
      "TelegramBot (like TwitterBot)",
    ]) {
      expect(stats.recordHit("/", { userAgent })).toBe(true);
    }
    stats.recordHit("/", { userAgent: "Mozilla/5.0 (Windows NT 10.0) Chrome/120 Safari/537.36" });
    const summary = stats.getStatsSummary();
    expect(summary.total).toBe(1);
    expect(summary.today).toBe(1);
    expect(summary.botHits).toBe(6);
  });

  it("does not mistake a real phone or browser for a robot", async () => {
    const stats = await load();
    for (const userAgent of [
      "Mozilla/5.0 (Linux; Android 12; CUBOT P50) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Mobile Safari/537.36",
      "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) YaBrowser/23.9 Safari/537.36",
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36 OPR/105.0",
    ]) {
      stats.recordHit("/", { userAgent });
    }
    expect(stats.getStatsSummary().total).toBe(4);
    expect(stats.getStatsSummary().botHits).toBe(0);
  });

  it("counts a visitor once a day however many pages they open", async () => {
    const stats = await load();
    const ua = "Mozilla/5.0 (Windows NT 10.0) Chrome/120";
    stats.recordHit("/", { userAgent: ua, visitor: "aaaaaaaaaaaa1111" });
    stats.recordHit("/qabul", { userAgent: ua, visitor: "aaaaaaaaaaaa1111" });
    stats.recordHit("/", { userAgent: ua, visitor: "bbbbbbbbbbbb2222" });
    const summary = stats.getStatsSummary();
    expect(summary.today).toBe(3);
    expect(summary.visitors.today).toBe(2);
    expect(summary.visitors.dailySeries.at(-1).count).toBe(2);
  });

  it("ignores a malformed visitor id", async () => {
    const stats = await load();
    stats.recordHit("/", { userAgent: "Mozilla/5.0", visitor: "<script>alert(1)</script>" });
    stats.recordHit("/", { userAgent: "Mozilla/5.0", visitor: "x" });
    expect(stats.getStatsSummary().visitors.today).toBe(0);
    expect(stats.getStatsSummary().today).toBe(2);
  });

  it("splits the views by language and ignores an unknown one", async () => {
    const stats = await load();
    const ua = "Mozilla/5.0 (Windows NT 10.0) Chrome/120";
    stats.recordHit("/", { userAgent: ua, language: "uz" });
    stats.recordHit("/", { userAgent: ua, language: "ru-RU" });
    stats.recordHit("/", { userAgent: ua, language: "ru" });
    stats.recordHit("/", { userAgent: ua, language: "en" });
    stats.recordHit("/", { userAgent: ua, language: "xx" });
    const languages = Object.fromEntries(stats.getStatsSummary().languages.map((l) => [l.key, l.count]));
    expect(languages).toEqual({ uz: 1, ru: 2, en: 1 });
  });

  it("still counts a page view from an old, cached page that sends no language or visitor", async () => {
    const stats = await load();
    stats.recordHit("/", { userAgent: "Mozilla/5.0 (Windows NT 10.0) Chrome/120" });
    const summary = stats.getStatsSummary();
    expect(summary.total).toBe(1);
    expect(summary.visitors.today).toBe(0);
    expect(summary.languages.every((l) => l.count === 0)).toBe(true);
  });

  it("persists the new counters and loads them back", async () => {
    let stats = await load();
    const ua = "Mozilla/5.0 (Windows NT 10.0) Chrome/120";
    stats.recordHit("/", { userAgent: ua, language: "ru", visitor: "cccccccccccc3333" });
    stats.recordHit("/", { userAgent: "curl/8" });
    stats.flushStats();
    stats = await load();
    const summary = stats.getStatsSummary();
    expect(summary.total).toBe(1);
    expect(summary.botHits).toBe(1);
    expect(summary.visitors.today).toBe(1);
    expect(summary.languages.find((l) => l.key === "ru").count).toBe(1);
  });
});
