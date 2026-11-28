import { describe, expect, it } from "vitest";
import { canonicalUrl } from "./canonicalUrl";

describe("canonicalUrl", () => {
  it("the home page is the bare site address", () => {
    expect(canonicalUrl("/")).toBe("https://fermi.uz");
  });

  it("an inner page is its own address, never the home page", () => {
    expect(canonicalUrl("/blog/1827/institut-missiyasi-va-kelajak-tasavvuri")).toBe("https://fermi.uz/blog/1827/institut-missiyasi-va-kelajak-tasavvuri");
  });

  it("a trailing slash does not make a second address", () => {
    expect(canonicalUrl("/aloqa/")).toBe("https://fermi.uz/aloqa");
  });
});
