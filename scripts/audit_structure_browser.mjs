import { existsSync, realpathSync } from "node:fs";
import { writeFile } from "node:fs/promises";
import { delimiter, dirname, join } from "node:path";
import { pathToFileURL } from "node:url";

const origin = new URL(process.env.AUDIT_URL ?? "http://127.0.0.1:3001");
const sectionId = Number(process.env.AUDIT_SECTION_ID ?? 1904);
const output = process.env.AUDIT_EXPORT ?? (sectionId === 1904
  ? "/tmp/fermi-tuzilma-browser-audit.json"
  : `/tmp/fermi-section-${sectionId}-browser-audit.json`);
const playwrightBin = process.env.PATH?.split(delimiter).map((dir) => join(dir, "playwright")).find(existsSync);
if (!playwrightBin) throw new Error("Run with npm exec --package=playwright -- node scripts/audit_structure_browser.mjs");
const { chromium } = await import(pathToFileURL(join(dirname(realpathSync(playwrightBin)), "index.mjs")).href);

const response = await fetch(new URL("/api/v1/menu/", origin), { signal: AbortSignal.timeout(5000) })
  .catch((error) => {
    throw new Error(`Cannot reach the local menu at ${origin.origin} (${error.cause?.code ?? error.message})`, { cause: error });
  });
if (!response.ok) throw new Error(`Menu request failed (${response.status})`);
const menu = await response.json();
function findSection(items) {
  for (const item of items) {
    if (item.id === sectionId) return item;
    const match = findSection(item.children ?? []);
    if (match) return match;
  }
}

const section = findSection(menu);
if (!section) throw new Error(`Menu section ${sectionId} was not found`);

function* links(item) {
  if (item.url && item.url !== "#") {
    const url = new URL(item.url, origin);
    if (url.origin === origin.origin && url.pathname !== "/") yield url.pathname + url.search;
  }
  for (const child of item.children ?? []) yield* links(child);
}

const routes = [...new Set(links(section))];
if (!routes.length) throw new Error(`No local pages were found under menu section ${sectionId}`);
const executablePath = process.env.AUDIT_BROWSER ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const browser = await chromium.launch({ executablePath });
const findings = [];
try {
  for (const language of ["uz", "ru", "en"]) {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.addInitScript((lang) => localStorage.setItem("i18nextLng", lang), language);
    for (const route of routes) {
      try {
        await page.setViewportSize({ width: 1440, height: 900 });
        const result = await page.goto(new URL(route, origin).href, { waitUntil: "domcontentloaded", timeout: 12000 });
        await page.locator(".page-header h1").waitFor({ timeout: 10000 });
        await page.evaluate(() => document.fonts.ready);
        const desktop = await page.evaluate(() => {
          const root = document.querySelector(".inner-page-body");
          const typography = (node) => {
            if (!node) return null;
            const { fontFamily, fontSize, fontWeight, lineHeight } = getComputedStyle(node);
            return { fontFamily, fontSize, fontWeight, lineHeight };
          };
          const headings = [...(root?.querySelectorAll("h2, h3, h4") ?? [])].filter((node) => node.getClientRects().length);
          return {
            title: document.querySelector(".page-header h1")?.textContent?.trim(),
            header: typography(document.querySelector(".page-header h1")),
            headings: headings.map((node) => ({ tag: node.tagName, text: node.textContent.trim(), ...typography(node) })),
            body: typography(root?.querySelector("p")),
            tables: root?.querySelectorAll("table").length ?? 0,
            documentCards: root?.querySelectorAll("[data-file-card]").length ?? 0,
            inlinePdfViewers: root?.querySelectorAll(".cms-roadmap-pdf__iframe").length ?? 0,
            contacts: root?.querySelectorAll("a[href^='tel:']").length ?? 0,
            overflow: document.documentElement.scrollWidth > innerWidth + 1,
          };
        });
        await page.setViewportSize({ width: 390, height: 844 });
        const mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
        findings.push({ route, language, status: result?.status(), desktop, mobileOverflow });
      } catch (error) {
        findings.push({ route, language, error: error.message });
      }
    }
    await page.close();
    await writeFile(output, JSON.stringify({ routes, findings }, null, 2));
    console.log(`${language}: ${routes.length} pages audited`);
  }
} finally {
  await browser.close();
}
console.log(output);
