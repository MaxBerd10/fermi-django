import { describe, expect, it } from "vitest";
import { splitLinks } from "./textLinks";

describe("splitLinks", () => {
  it("leaves a text without links as one piece", () => {
    expect(splitLinks("Oddiy matn")).toEqual([{ text: "Oddiy matn" }]);
  });

  it("turns [label](url) into a link that shows the label", () => {
    expect(splitLinks("Qarang: [Taʻlim toʻgʻrisida](https://lex.uz/docs/-5100677) qonuni")).toEqual([
      { text: "Qarang: " },
      { text: "Taʻlim toʻgʻrisida", href: "https://lex.uz/docs/-5100677", external: true },
      { text: " qonuni" },
    ]);
  });

  it("keeps bare addresses and e-mails clickable, without the closing punctuation", () => {
    expect(splitLinks("Sayt https://fjsti.uz/test. Pochta: info@fjsti.uz")).toEqual([
      { text: "Sayt " },
      { text: "https://fjsti.uz/test", href: "https://fjsti.uz/test", external: true },
      { text: ". Pochta: " },
      { text: "info@fjsti.uz", href: "mailto:info@fjsti.uz", external: false },
    ]);
  });

  it("does not link a label whose address is not http(s)", () => {
    expect(splitLinks("[x](javascript:alert(1))")).toEqual([{ text: "[x](javascript:alert(1))" }]);
  });

  it("links a labelled address inside the site without opening a new tab", () => {
    expect(splitLinks("[Xalqaro hamkorlik](/detail/xalqaro-hamkorlik-14?menu_id=71)")).toEqual([
      { text: "Xalqaro hamkorlik", href: "/detail/xalqaro-hamkorlik-14?menu_id=71", external: false },
    ]);
  });

  it("does not take a protocol-relative address (//host) for an address inside the site", () => {
    expect(splitLinks("[x](//evil.example/a)")).toEqual([{ text: "[x](//evil.example/a)" }]);
  });

  it("allows brackets and parentheses in the address of a labelled link", () => {
    const [piece] = splitLinks("[PDF](https://fermi.uz/media/a%20b(1).pdf)");
    expect(piece).toEqual({ text: "PDF", href: "https://fermi.uz/media/a%20b(1).pdf", external: true });
  });
});
