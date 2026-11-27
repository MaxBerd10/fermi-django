import { describe, expect, it } from "vitest";
import { loneFileLink } from "./loneFileLink";

describe("loneFileLink", () => {
  it("a text that is one link to a PDF is a file link", () => {
    expect(loneFileLink("[Приказ № 236](https://fermi.uz/media/a/b.pdf)")).toEqual({ title: "Приказ № 236", href: "https://fermi.uz/media/a/b.pdf", extension: "pdf" });
  });

  it("a full stop or semicolon after the link is allowed", () => {
    expect(loneFileLink("[О приёме](https://fermi.uz/media/x.pdf).")?.title).toBe("О приёме");
    expect(loneFileLink("[О приёме](https://fermi.uz/media/x.pdf);")?.extension).toBe("pdf");
  });

  it("a link to lex.uz is typed by the portal", () => {
    expect(loneFileLink("[Указ № УП-6221](https://lex.uz/docs/-5100677)")?.extension).toBe("lex.uz");
  });

  it("a link inside running text is not one", () => {
    expect(loneFileLink("Cm. [приказ](https://fermi.uz/media/x.pdf) для подробностей")).toBeNull();
  });

  it("two links, a plain page link and plain text are not file links", () => {
    expect(loneFileLink("[a](https://fermi.uz/media/a.pdf) [b](https://fermi.uz/media/b.pdf)")).toBeNull();
    expect(loneFileLink("[Сайт](https://example.uz/page)")).toBeNull();
    expect(loneFileLink("Просто текст без ссылки")).toBeNull();
  });

  it("a file name with a bracket pair in its address is kept whole", () => {
    expect(loneFileLink("[Список](https://fermi.uz/media/a(1).pdf)")?.href).toBe("https://fermi.uz/media/a(1).pdf");
  });
});
