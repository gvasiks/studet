import { describe, expect, it } from "vitest";
import {
  countries,
  countryOf,
  defaultLocale,
  isLocale,
  languageOf,
  legacyLocales,
  localeFor,
  localeForBrowser,
  locales,
  localesOfCountry,
  nativeLocale,
} from "./config";

describe("адрес = язык + страна", () => {
  it("латышский и английский адреса ведут в каталог Латвии", () => {
    expect(languageOf("lv")).toBe("lv");
    expect(countryOf("lv")).toBe("LV");
    expect(languageOf("en-lv")).toBe("en");
    expect(countryOf("en-lv")).toBe("LV");
  });

  it("латвийский каталог открыт на трёх языках, литовский — только с флагом", () => {
    expect(locales).toEqual(["lv", "en-lv", "lt-lv"]);
    for (const locale of ["lt", "en-lt", "lv-lt"]) expect(isLocale(locale), locale).toBe(false);
    expect(isLocale("lt-lv")).toBe(true);
  });

  it("старый /en больше не адрес сайта, но известен как переименованный", () => {
    expect(isLocale("en")).toBe(false);
    expect(isLocale("en-lv")).toBe(true);
    expect(legacyLocales.en).toBe("en-lv");
  });

  it("у страны основной язык стоит первым", () => {
    expect(localesOfCountry("LV")).toEqual(["lv", "en-lv", "lt-lv"]);
    expect(nativeLocale("LV")).toBe("lv");
    expect(defaultLocale).toBe("lv");
  });

  it("список стран собирается из адресов", () => {
    expect(countries).toEqual(["LV"]);
  });

  it("в другую страну посетитель попадает на своём языке", () => {
    // Литва в тестах закрыта (нет флага предпросмотра), поэтому проверяется
    // открытая страна
    expect(localeFor("LV", "en")).toBe("en-lv");
    expect(localeFor("LV", "lv")).toBe("lv");
    expect(localeFor("LV", "lt")).toBe("lt-lv");
  });

  it("у каждой страны три языка: свой без суффикса, остальные — «язык-страна»", () => {
    expect([languageOf("lt-lv"), countryOf("lt-lv")]).toEqual(["lt", "LV"]);
    expect([languageOf("lv-lt"), countryOf("lv-lt")]).toEqual(["lv", "LT"]);
    expect([languageOf("en-lt"), countryOf("en-lt")]).toEqual(["en", "LT"]);
    expect([languageOf("lt"), countryOf("lt")]).toEqual(["lt", "LT"]);
    // Эстония и эстонский язык (docs/PLAN-ESTONIA.md)
    expect([languageOf("et"), countryOf("et")]).toEqual(["et", "EE"]);
    expect([languageOf("en-ee"), countryOf("en-ee")]).toEqual(["en", "EE"]);
    expect([languageOf("lv-ee"), countryOf("lv-ee")]).toEqual(["lv", "EE"]);
    expect([languageOf("lt-ee"), countryOf("lt-ee")]).toEqual(["lt", "EE"]);
    expect([languageOf("et-lv"), countryOf("et-lv")]).toEqual(["et", "LV"]);
    expect([languageOf("et-lt"), countryOf("et-lt")]).toEqual(["et", "LT"]);
    // Без флага предпросмотра закрыты и страна, и язык: эстонского адреса
    // нет даже у открытой Латвии.
    for (const locale of ["et", "en-ee", "lv-ee", "lt-ee", "et-lv", "et-lt"]) expect(isLocale(locale), locale).toBe(false);
  });

  it("по языку браузера: родной язык ведёт в свою страну, английский — в Латвию", () => {
    expect(localeForBrowser("lv")).toBe("lv");
    expect(localeForBrowser("en")).toBe("en-lv");
    // Литва закрыта флагом — литовский браузер попадает в латвийский
    // каталог на литовском
    expect(localeForBrowser("lt")).toBe("lt-lv");
    expect(localeForBrowser("de")).toBe("lv");
    expect(localeForBrowser("")).toBe("lv");
  });

  it("каждый адрес из списка описан", () => {
    for (const locale of locales) {
      expect(languageOf(locale)).toBeTruthy();
      expect(countryOf(locale)).toBeTruthy();
    }
  });
});
