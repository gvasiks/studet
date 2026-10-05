import { describe, expect, it } from "vitest";
import {
  countryOf,
  defaultLocale,
  isLocale,
  languageOf,
  legacyLocales,
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

  it("литовские адреса не открыты, пока нет литовского словаря", () => {
    expect(isLocale("lt")).toBe(false);
    expect(isLocale("en-lt")).toBe(false);
  });

  it("у страны основной язык стоит первым", () => {
    expect(localesOfCountry("LV")).toEqual(["lv", "en-lv"]);
    expect(nativeLocale("LV")).toBe("lv");
    expect(defaultLocale).toBe("lv");
  });

  it("каждый адрес из списка описан", () => {
    for (const locale of locales) {
      expect(languageOf(locale)).toBeTruthy();
      expect(countryOf(locale)).toBeTruthy();
    }
  });
});
