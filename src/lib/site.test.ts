import { describe, expect, it } from "vitest";
import { buildAlternates, isSiteClosed, SITE_URL } from "./site";

describe("buildAlternates", () => {
  it("canonical — текущий адрес, переводы — адреса той же страны по языку", () => {
    const alternates = buildAlternates("/programmes/lu/economics", "en-lv");
    expect(alternates.canonical).toBe(`${SITE_URL}/en-lv/programmes/lu/economics`);
    expect(alternates.languages).toEqual({
      lv: `${SITE_URL}/lv/programmes/lu/economics`,
      en: `${SITE_URL}/en-lv/programmes/lu/economics`,
      lt: `${SITE_URL}/lt-lv/programmes/lu/economics`,
      "x-default": `${SITE_URL}/lv/programmes/lu/economics`,
    });
  });

  it("главная: пустой путь", () => {
    expect(buildAlternates("", "lv").canonical).toBe(`${SITE_URL}/lv`);
  });
});

describe("закрытая выкладка", () => {
  it("закрыт только при SITE_CLOSED=1; без переменной сайт открыт", () => {
    expect(isSiteClosed({ SITE_CLOSED: "1" })).toBe(true);
    expect(isSiteClosed({})).toBe(false);
    expect(isSiteClosed({ SITE_CLOSED: "0" })).toBe(false);
    expect(isSiteClosed({ SITE_CLOSED: "true" })).toBe(false);
  });
});
