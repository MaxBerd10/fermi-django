import { describe, expect, it } from "vitest";
import type { ContentBlock } from "@/types/blocks";
import { layoutBlocks, picturesOf } from "./layoutBlocks";

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

  it("quote needs « » or \" \"", () => {
    const quote = layoutBlocks([p("intro"), img("hero.webp"), h("H"), p("«Words» — Name"), img("person.webp")]);
    expect(quote.map((s) => s.kind)).toContain("quote");
    const plain = layoutBlocks([p("intro"), img("hero.webp"), h("H"), p("plain words"), img("chart.webp")]);
    expect(plain.map((s) => s.kind)).not.toContain("quote");
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

  it("legacy image-only raw_html of another page stays a plain block", () => {
    const other = base("raw_html", { html: '<p><img src="https://fermi.uz/media/migrated/img/x.jpg" alt="x" width="960" height="640"></p>', slug: "y" });
    expect(picturesOf(other)).toEqual([]);
    expect(layoutBlocks([other]).map((s) => s.kind)).toEqual(["block"]);
  });

  it("legacy image-only raw_html is read as pictures", () => {
    const legacy = base("raw_html", { html: '<p><img src="/images/hisobot/p1.webp" alt="x" width="960" height="640"></p>', slug: "x" });
    expect(picturesOf(legacy)).toHaveLength(1);
  });
});
