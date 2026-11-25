import { describe, expect, it, vi } from "vitest";
import type { ContentBlock } from "@/types/blocks";
import { isChapterHeading, layoutBlocks, picturesOf } from "./layoutBlocks";
import { resolveLocale } from "../api/client";

vi.mock("../i18n", () => ({ default: {} }));

let nextId = 1;
const base = <T extends ContentBlock["block_type"]>(block_type: T, data: unknown) =>
  ({ id: nextId++, order: nextId, block_type, data }) as unknown as ContentBlock;

const p = (text: string) => base("paragraph", { text });
const h = (text: string, level: 2 | 3 = 2) => base("heading", { text, level });
const list = (n: number) => base("list", { items: Array.from({ length: n }, (_, i) => `item ${i}`) });
const table = (rows: number) => base("table", { headers: ["a", "b"], rows: Array.from({ length: rows }, () => ["x", "y"]) });
const img = (file: string, width = 960, height = 640) =>
  base("image", { image_id: 1, alt: "", image: { id: 1, file, width, height, alt_text: "" } });
const brokenImg = () => base("image", { image_id: 2, alt: "", image: null });
const rawText = () => base("raw_html", { html: "<p>some old html text that is long enough</p>", slug: "x" });

const kinds = (blocks: ContentBlock[]) => layoutBlocks(blocks).map((s) => s.kind);

describe("layoutBlocks", () => {
  it("opening: first paragraph followed by an image", () => {
    expect(layoutBlocks([p("a"), img("x.webp"), h("H")])[0].kind).toBe("opening");
  });

  it.each([false, true])("uses one quotation layout across translations (quote=%s)", (quote) => {
    const block = base("paragraph", {
      uz: { text: quote ? "«Soʻzlar». — Muallif" : "Institut «FerMI» nomi bilan tanilgan." },
      ru: { text: "Текст без кавычек." },
      en: { text: '"Quoted words" — Author' },
    });
    for (const lang of ["uz", "ru", "en"] as const) {
      const paragraph = resolveLocale<ContentBlock>(block, lang);
      expect(kinds([h("A"), paragraph, img("portrait.webp")]).includes("quote")).toBe(quote);
    }
  });

  it("a quotation followed by a run of pictures is not a quote card", () => {
    const quote = base("paragraph", { text: "Words", quote: true });
    expect(kinds([h("A"), quote, img("1.webp"), img("2.webp"), img("3.webp")])).not.toContain("quote");
  });

  it("opening needs exactly one picture after the text", () => {
    expect(layoutBlocks([p("a"), img("1.webp"), img("2.webp")])[0].kind).not.toBe("opening");
  });

  it("renders a date-only list as a chronology across languages", () => {
    const entries = ["1992–1997 — A", "2021 yildan — B", "с 2021 года — C", "since 2021 — D"];
    expect(kinds([base("list", { items: entries })])).toEqual(["dated"]);
    expect(kinds([base("list", { items: [...entries, "General information"] })])).toEqual(["section"]);
  });

  it("person: level-3 heading, image, paragraphs", () => {
    const sections = layoutBlocks([h("History"), h("MIRZAEV", 3), img("m.webp"), p("born"), p("worked"), h("NISHONOV", 3), img("n.webp"), p("lived")]);
    const people = sections.filter((s) => s.kind === "person");
    expect(people).toHaveLength(2);
    expect(people[0].kind === "person" && people[0].text).toHaveLength(2);
  });

  it("section with long text puts pictures beside it", () => {
    const long = layoutBlocks([h("A"), list(4), img("1.webp"), img("2.webp")]);
    const short = layoutBlocks([h("B"), p("one line"), img("1.webp"), img("2.webp"), img("3.webp")]);
    const side = (sections: ReturnType<typeof layoutBlocks>) => sections.find((s) => s.kind === "section" && s.pictures.length > 0);
    expect(side(long)?.kind === "section" && side(long)).toMatchObject({ side: true });
    expect(side(short)?.kind === "section" && side(short)).toMatchObject({ side: false });
  });

  it("layout does not change with text length", () => {
    const make = (n: number) => [h("A".repeat(n)), p("t".repeat(n * 10)), list(2), img("1.webp"), h("B".repeat(n)), table(5), img("2.webp")];
    const shape = (blocks: ContentBlock[]) => layoutBlocks(blocks).map((s) => (s.kind === "section" ? `section:${s.side}:${s.pictures.length}` : s.kind));
    expect(shape(make(30))).toEqual(shape(make(3)));
  });

  it("pictures before the first heading are a row, not a side column", () => {
    const sections = layoutBlocks([img("1.webp"), img("2.webp"), h("A"), list(4)]);
    const first = sections[0];
    expect(first.kind).toBe("section");
    expect(first.kind === "section" && first.side).toBe(false);
    expect(first.kind === "section" && first.pictures).toHaveLength(2);
  });

  it("exactly three trailing paragraphs after the last list or table are the footer", () => {
    expect(kinds([h("A"), list(2), p("source"), p("slogan"), p("contact")])).toContain("footer");
    expect(kinds([h("A"), list(2), p("source"), p("contact")])).not.toContain("footer");
  });

  it("image with image: null is ignored", () => {
    expect(() => layoutBlocks([h("A"), p("x"), brokenImg()])).not.toThrow();
    expect(picturesOf(brokenImg())).toEqual([]);
  });

  it("raw_html text block and an empty page", () => {
    expect(layoutBlocks([rawText()]).map((s) => s.kind)).toEqual(["block"]);
    expect(layoutBlocks([])).toEqual([]);
  });

  it("tall picture", () => {
    expect(picturesOf(img("t.webp", 540, 690))[0].tall).toBe(true);
    expect(picturesOf(img("w.webp", 960, 640))[0].tall).toBe(false);
  });

  it("old raw_html is always a plain block, even when it holds nothing but a picture", () => {
    for (const src of ["https://fermi.uz/media/migrated/img/x.jpg", "/images/hisobot/p1.webp"]) {
      const old = base("raw_html", { html: `<p><img src="${src}" alt="x" width="960" height="640"></p>`, slug: "y" });
      expect(picturesOf(old)).toEqual([]);
      expect(layoutBlocks([old]).map((s) => s.kind)).toEqual(["block"]);
    }
  });
  it("a list that only starts with a year is not a chronology, in any language", () => {
    const block = base("list", {
      uz: { items: ["2027-yil aprel: A", "2027-yil may: B"] },
      ru: { items: ["Апрель 2027 г.: А", "Май 2027 г.: Б"] },
      en: { items: ["April 2027: A", "May 2027: B"] },
    });
    for (const lang of ["uz", "ru", "en"] as const) expect(kinds([resolveLocale<ContentBlock>(block, lang)])).toEqual(["section"]);
  });

  it("a chronology is a chronology in every language even when one translation words an entry differently", () => {
    const block = base("list", {
      uz: { items: ["1992–1997 — A", "2021 yildan — B"] },
      ru: { items: ["1992-1997 — А", "Весной 2021 года: Б"] },
      en: { items: ["1992-1997 — A", "since 2021 — B"] },
    });
    for (const lang of ["uz", "ru", "en"] as const) expect(kinds([resolveLocale<ContentBlock>(block, lang)])).toEqual(["dated"]);
  });
  it("a run of people is a list of profile cards; one person alone (the rector) is not", () => {
    const run = layoutBlocks([h("History"), h("A", 3), img("a.webp"), p("born"), h("B", 3), img("b.webp"), p("lived")]);
    expect(run.filter((s) => s.kind === "person").map((s) => s.kind === "person" && s.card)).toEqual([true, true]);
    const alone = layoutBlocks([h("Rector"), h("A", 3), img("a.webp"), p("address"), h("Next"), p("text")]);
    expect(alone.filter((s) => s.kind === "person").map((s) => s.kind === "person" && s.card)).toEqual([false]);
  });

  it("a prose list directly followed by a dated list is one timeline", () => {
    const sections = layoutBlocks([h("Stages"), list(3), base("list", { items: ["1992–1997 — A", "1998–2005 — B"] }), p("after")]);
    const dated = sections.find((s) => s.kind === "dated");
    expect(dated?.kind === "dated" && dated.before?.block_type).toBe("list");
    expect(dated?.kind === "dated" && dated.entries).toHaveLength(2);
    expect(sections.filter((s) => s.kind === "section").flatMap((s) => (s.kind === "section" ? s.blocks.map((b) => b.block_type) : []))).not.toContain("list");
  });

  it("a short heading that ends with a number is a step card; an article heading is not", () => {
    const step = layoutBlocks([h("About"), h("USMLE Step 1", 3), p("text one"), h("USMLE Step 2", 3), p("text two")]);
    expect(step.filter((s) => s.kind === "step").map((s) => s.kind === "step" && s.number)).toEqual(["1", "2"]);
    expect(kinds([h("A"), h("1-modda. Ushbu kodeks bilan tartibga solinadigan munosabatlar", 3), p("text")])).not.toContain("step");
  });
  it("a heading, paragraphs only and one landscape picture (first or last) is a story: the first paragraph beside the picture, the rest below", () => {
    const first = layoutBlocks([h("Top"), p("t"), h("Page of history"), img("a.webp"), p("one"), p("two"), p("three"), h("Next"), p("x")]).find((s) => s.kind === "story");
    expect(first?.kind === "story" && first.body).toHaveLength(2);
    const last = layoutBlocks([h("Top"), p("t"), h("Cooperation"), p("one"), img("a.webp")]).find((s) => s.kind === "story");
    expect(last?.kind === "story" && last.body).toHaveLength(0);
  });

  it("a portrait picture, a list, or a picture between paragraphs is not a story", () => {
    expect(kinds([h("Top"), p("t"), h("Rector"), img("r.webp", 540, 690), p("one"), p("two"), p("three")])).not.toContain("story");
    expect(kinds([h("Top"), p("t"), h("Rector"), img("r.webp", 960, 883), p("one"), p("two"), p("three")])).not.toContain("story");
    expect(kinds([h("Top"), p("t"), h("A"), p("one"), list(2), img("a.webp")])).not.toContain("story");
    expect(kinds([h("Top"), p("t"), h("A"), p("one"), img("a.webp"), p("two"), p("three"), p("four")])).not.toContain("story");
  });
  it("a heading that numbers a chapter (1-bob, Глава 1, Chapter 1) is a chapter band; other headings are not", () => {
    for (const text of ["1-BOB UMUMIY QOIDALAR", "1-bob. Umumiy qoidalar", "Глава 1. Общие положения", "ГЛАВА 1 ОБЩИЕ ПОЛОЖЕНИЯ", "Chapter 1 General rules"]) expect(isChapterHeading(text)).toBe(true);
    for (const text of ["1. Stomatologiya markazi", "Kelajak haqidagi tasavvur", "1-modda. Ushbu kodeks", "2027-yil vazifalari"]) expect(isChapterHeading(text)).toBe(false);
  });
  it("the first section of a page with one picture is the lead: a big picture beside its introduction; later sections are not", () => {
    const sections = layoutBlocks([h("About"), p("one"), p("two"), img("a.webp"), h("Later"), list(4), p("x"), img("b.webp")]);
    const flags = sections.filter((s) => s.kind === "section" && s.side).map((s) => s.kind === "section" && s.lead);
    expect(flags).toEqual([true, false]);
    const two = layoutBlocks([h("About"), p("one"), p("two"), img("a.webp"), img("b.webp")]).find((s) => s.kind === "section" && s.pictures.length > 0);
    expect(two?.kind === "section" && two.lead).toBe(false);
  });
});
