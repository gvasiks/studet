import { describe, expect, it } from "vitest";
import {
  countries,
  countryOf,
  defaultLocale,
  isLocale,
  languageOf,
  legacyLocales,
  localeFor,
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

  it("старый /en больше не адрес сайта, но известен как переименованный", () => {
    expect(isLocale("en")).toBe(false);
    expect(isLocale("en-lv")).toBe(true);
    expect(legacyLocales.en).toBe("en-lv");
  });

  it("литовские адреса закрыты, пока не задан флаг предпросмотра", () => {
    expect(isLocale("lt")).toBe(false);
    expect(isLocale("en-lt")).toBe(false);
  });

  it("у страны основной язык стоит первым", () => {
    expect(localesOfCountry("LV")).toEqual(["lv", "en-lv"]);
    expect(nativeLocale("LV")).toBe("lv");
    expect(defaultLocale).toBe("lv");
  });

  it("список стран собирается из адресов", () => {
    expect(countries).toEqual(["LV"]);
  });

  it("в другую страну посетитель попадает на своём языке, если он там есть", () => {
    // литовские адреса в тестах закрыты (нет флага предпросмотра), поэтому
    // проверяется открытая страна: английский остаётся английским
    expect(localeFor("LV", "en")).toBe("en-lv");
    expect(localeFor("LV", "lv")).toBe("lv");
    // литовского в Латвии нет — открывается её основной язык
    expect(localeFor("LV", "lt")).toBe("lv");
  });

  it("каждый адрес из списка описан", () => {
    for (const locale of locales) {
      expect(languageOf(locale)).toBeTruthy();
      expect(countryOf(locale)).toBeTruthy();
    }
  });
});
