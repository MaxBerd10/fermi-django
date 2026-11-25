import { afterEach, expect, it, vi } from "vitest";
import { getMenu } from "./menu";

vi.mock("../i18n", () => ({ default: { language: "uz", resolvedLanguage: "uz" } }));

afterEach(() => vi.unstubAllGlobals());

it("warms the menu in the requested language while Uzbek is active", async () => {
  vi.stubGlobal("window", { location: { origin: "https://fermi.uz" } });
  const item = {
    id: 1827,
    label: { uz: "Institut haqida", ru: "Об институте", en: "About the institute" },
    url: "",
    order: 1,
    children: [],
  };
  vi.stubGlobal("fetch", vi.fn(async () => Response.json([item])));

  const menus = await Promise.all([getMenu(), getMenu("ru"), getMenu("en")]);
  expect(menus.map(([menu]) => menu.title)).toEqual(Object.values(item.label));
});
