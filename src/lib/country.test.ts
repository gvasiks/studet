import { describe, expect, it } from "vitest";
import { countryProfile, hasFeature, LEVEL_KEYS } from "./country";
import lv from "../i18n/dictionaries/lv.json";
import en from "../i18n/dictionaries/en.json";
import lt from "../i18n/dictionaries/lt.json";

describe("профиль страны", () => {
  it("у Латвии есть все разделы", () => {
    for (const feature of ["survey", "match", "calculator", "glossary", "rights", "privacy", "favorites"] as const) {
      expect(hasFeature("LV", feature)).toBe(true);
    }
  });

  it("у Литвы на фазе 2 — только каталог и список; расчёта балла и права нет", () => {
    expect(hasFeature("LT", "favorites")).toBe(true);
    for (const feature of ["survey", "match", "calculator", "glossary", "rights", "privacy", "verification"] as const) {
      expect(hasFeature("LT", feature)).toBe(false);
    }
  });

  it("вкладки уровня страны — из общего списка уровней", () => {
    for (const country of ["LV", "LT"] as const) {
      for (const level of countryProfile(country).levels) expect(LEVEL_KEYS).toContain(level);
    }
  });

  // Ключ без подписи показался бы посетителю как "vilnius" или "integrated".
  it("у каждого города, языка и уровня есть подпись во всех словарях", () => {
    for (const [name, dict] of Object.entries({ lv, en, lt })) {
      for (const country of ["LV", "LT"] as const) {
        const profile = countryProfile(country);
        for (const city of profile.cities) expect(dict.catalog.city, `${name}: город ${city}`).toHaveProperty(city);
        for (const language of profile.languages) expect(dict.catalog.language, `${name}: язык ${language}`).toHaveProperty(language);
        for (const level of profile.levels) {
          expect(dict.catalog.tabs, `${name}: вкладка ${level}`).toHaveProperty(level);
          expect(dict.catalog.degreeLevel, `${name}: уровень ${level}`).toHaveProperty(level);
        }
      }
    }
  });
});
