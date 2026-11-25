import { describe, expect, it, vi } from "vitest";
import type { ContentBlock } from "@/types/blocks";
import { layoutBlocks, picturesOf } from "./layoutBlocks";
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
});
