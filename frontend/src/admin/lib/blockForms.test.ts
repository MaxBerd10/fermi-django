import { describe, expect, it } from "vitest";
import {
  addPictures, galleryFormFromServer, galleryFormFromStaged, galleryProblem, galleryStaged, movePicture, removePicture, setGalleryStyle, setPictureAlt,
  addColumn, addRow, chipLabel, decodeStaged, embedProblem, emptyEmbed, emptyTable, encodeStaged, mapSrcFrom, removeColumn, removeRow, setCell, setEmbedField,
  setGroupLabel, setGroupSpans, tableProblem, youtubeIdFrom,
} from "./blockForms";

describe("encodeStaged", () => {
  it("round-trips Uzbek, Russian and the ʻ apostrophe through base64", () => {
    const value = { uz: "Oʻzbek va xorijiy tillar", ru: "Кафедра узбекского", rows: [["№", "1"]] };
    expect(decodeStaged(encodeStaged(value))).toEqual(value);
  });
  it("gives null for a text that is not base64 JSON", () => expect(decodeStaged("@@@")).toBeNull());
});

describe("youtubeIdFrom", () => {
  it.each([
    ["Mg6MBqg4f5o", "Mg6MBqg4f5o"],
    ["https://youtu.be/Mg6MBqg4f5o", "Mg6MBqg4f5o"],
    ["https://youtu.be/Mg6MBqg4f5o?si=abc", "Mg6MBqg4f5o"],
    ["https://www.youtube.com/watch?v=Mg6MBqg4f5o&t=30s", "Mg6MBqg4f5o"],
    ["https://www.youtube.com/watch?list=PL1&v=Mg6MBqg4f5o", "Mg6MBqg4f5o"],
    ["https://www.youtube.com/embed/Mg6MBqg4f5o", "Mg6MBqg4f5o"],
    ["https://www.youtube.com/shorts/Mg6MBqg4f5o", "Mg6MBqg4f5o"],
    ["  https://youtu.be/Mg6MBqg4f5o  ", "Mg6MBqg4f5o"],
  ])("finds the id in %s", (input, id) => expect(youtubeIdFrom(input)).toBe(id));
  it.each(["", "kisqa", "https://example.com/watch?v=Mg6MBqg4f5o", "https://vimeo.com/123456789", "Mg6MBqg4f5oXX"])("refuses %s", (input) => expect(youtubeIdFrom(input)).toBeNull());
});

describe("mapSrcFrom", () => {
  const src = "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d6078.41296!2d71.756!3d40.382";
  it("takes the address alone", () => expect(mapSrcFrom(src)).toBe(src));
  it("takes the src of the whole iframe code Google gives", () =>
    expect(mapSrcFrom(`<iframe src="${src}" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>`)).toBe(src));
  it.each(["", "https://evil.example/maps/embed?pb=!1m18!1m12!1m3", "https://www.google.com/maps/place/Ferghana", "<iframe src='https://evil.example/x'></iframe>"])("refuses %s", (input) => expect(mapSrcFrom(input)).toBeNull());
});

describe("embedProblem", () => {
  it("asks for a video address first", () => expect(embedProblem(emptyEmbed("youtube"))).toMatch(/YouTube/));
  it("accepts a filled video", () => expect(embedProblem(setEmbedField(emptyEmbed("youtube"), "video_id", "Mg6MBqg4f5o"))).toBeNull());
  it("keeps the map height within the range the server accepts", () => {
    const data = setEmbedField(setEmbedField(emptyEmbed("map"), "src", "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3"), "height", 50);
    expect(embedProblem(data)).toMatch(/200/);
  });
});

describe("tables keep the three languages the same shape", () => {
  it("adds and removes a row in every language", () => {
    const grown = addRow(emptyTable(2, 1));
    expect(grown.uz.rows).toHaveLength(2);
    expect(grown.ru.rows).toHaveLength(2);
    expect(grown.en.rows).toHaveLength(2);
    expect(removeRow(grown, 0).en.rows).toHaveLength(1);
  });
  it("never removes the last row or column", () => {
    expect(removeRow(emptyTable(2, 1), 0).uz.rows).toHaveLength(1);
    expect(removeColumn(emptyTable(1, 1), 0).uz.headers).toHaveLength(1);
  });
  it("adds and removes a column in headers, rows and group headings of every language", () => {
    const grouped = setGroupSpans(emptyTable(3, 1), [1, 2]);
    const wider = addColumn(grouped);
    expect(wider.ru.headers).toHaveLength(4);
    expect(wider.en.rows[0]).toHaveLength(4);
    expect(wider.uz.header_groups).toEqual([{ label: "", span: 1 }, { label: "", span: 2 }, { label: "", span: 1 }]);
    expect(wider.uz.header_groups?.reduce((sum, group) => sum + group.span, 0)).toBe(4);
    const narrower = removeColumn(setGroupSpans(emptyTable(3, 1), [1, 2]), 2);
    expect(narrower.uz.header_groups).toEqual([{ label: "", span: 1 }, { label: "", span: 1 }]);
    expect(removeColumn(narrower, 1).uz.header_groups).toEqual([{ label: "", span: 1 }]);
  });
  it("edits a cell and a group label in ONE language only", () => {
    const data = setGroupLabel(setGroupSpans(setCell(emptyTable(2, 1), "ru", 0, 1, "16"), [2]), "uz", 0, "Guruh");
    expect(data.ru.rows[0][1]).toBe("16");
    expect(data.uz.rows[0][1]).toBe("");
    expect(data.uz.header_groups?.[0].label).toBe("Guruh");
    expect(data.en.header_groups?.[0].label).toBe("");
  });
  it("says what is wrong before the server has to", () => {
    expect(tableProblem(emptyTable(2, 1))).toMatch(/UZ/);
    const filled = emptyTable(1, 1);
    filled.uz.headers[0] = filled.ru.headers[0] = filled.en.headers[0] = "№";
    expect(tableProblem(filled)).toBeNull();
    expect(tableProblem(setGroupSpans(filled, [2]))).toMatch(/guruh/);
  });
});

describe("chipLabel", () => {
  it("names a table, a map and a video the way the server does", () => {
    expect(chipLabel("table", emptyTable(2, 3), false)).toBe("Jadval (3 qator) — tahrirlash uchun bosing");
    expect(chipLabel("embed", emptyEmbed("map"))).toBe("Xarita (saqlaganingizda yangilanadi)");
    expect(chipLabel("embed", setEmbedField(emptyEmbed("youtube"), "video_id", "x"), false)).toBe("YouTube video — tahrirlash uchun bosing");
  });
});

describe("galleries keep the same pictures in the three languages", () => {
  const server = {
    uz: { style: "plain", items: [{ image_id: 1, alt: "bir" }, { image_id: 2, alt: "ikki" }] },
    ru: { style: "plain", items: [{ image_id: 1, alt: "один" }, { image_id: 2, alt: "" }] },
    en: { style: "plain", items: [{ image_id: 1, alt: "" }, { image_id: 2, alt: "two" }] },
  };
  const images = { "1": { file: "http://x/a.png" }, "2": { file: "http://x/b.png" } };

  it("opens from the saved block with every language's alt text", () => {
    const form = galleryFormFromServer(server, images);
    expect(form.style).toBe("plain");
    expect(form.pictures.map((p) => [p.image_id, p.url, p.alt.ru, p.alt.en])).toEqual([[1, "http://x/a.png", "один", ""], [2, "http://x/b.png", "", "two"]]);
  });
  it("sends the same pictures in the same order to every language, each with its own alt", () => {
    const form = movePicture(setPictureAlt(galleryFormFromServer(server, images), "ru", 1, "два"), 0, 1);
    const staged = galleryStaged(form);
    for (const lang of ["uz", "ru", "en"] as const) expect(staged[lang].items.map((i) => i.image_id)).toEqual([2, 1]);
    expect(staged.ru.items[0].alt).toBe("два");
    expect(staged.uz.items[0].alt).toBe("ikki");
  });
  it("adds a picked file by its path, removes by position and never moves past the ends", () => {
    const form = addPictures(galleryFormFromServer(server, images), [{ path: "uploads/admin/c.png", url: "http://x/c.png" }]);
    expect(galleryStaged(form).en.items[2]).toMatchObject({ path: "uploads/admin/c.png", url: "http://x/c.png", alt: "" });
    expect(removePicture(form, 0).pictures).toHaveLength(2);
    expect(movePicture(form, 0, -1)).toBe(form);
    expect(movePicture(form, 2, 1)).toBe(form);
  });
  it("round-trips through the staged form (a chip edited twice before the page is saved)", () => {
    const form = setGalleryStyle(addPictures(galleryFormFromServer(server, images), [{ path: "uploads/admin/c.png", url: "http://x/c.png" }]), "certificate");
    expect(galleryFormFromStaged(galleryStaged(form))).toEqual(form);
  });
  it("leaves the style out for the plain default and asks for at least one picture", () => {
    const form = setGalleryStyle(galleryFormFromServer(server, images), "");
    expect(galleryStaged(form).uz.style).toBeUndefined();
    expect(galleryProblem(removePicture(removePicture(form, 0), 0))).toMatch(/kamida/);
    expect(galleryProblem(form)).toBeNull();
  });
  it("names itself like the server does", () => expect(chipLabel("gallery", galleryStaged(galleryFormFromServer(server, images)) as never, false)).toBe("Rasmlar galereyasi (2 ta) — tahrirlash uchun bosing"));
});
