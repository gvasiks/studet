import { describe, expect, it } from "vitest";
import { catalogProfile, countryProfile, hasFeature, LEVEL_KEYS, schoolLeaverLevels } from "./country";
import lv from "../i18n/dictionaries/lv.json";
import en from "../i18n/dictionaries/en.json";
import lt from "../i18n/dictionaries/lt.json";

describe("профиль страны", () => {
  it("у Латвии на латышском и английском есть все разделы", () => {
    for (const locale of ["lv", "en-lv"] as const) {
      for (const feature of ["survey", "match", "calculator", "glossary", "rights", "privacy", "favorites"] as const) {
        expect(hasFeature(locale, feature), `${locale}: ${feature}`).toBe(true);
      }
    }
  });

  it("Латвия на литовском: все разделы для посетителя есть, внутренней страницы проверки нет", () => {
    for (const feature of ["survey", "match", "calculator", "favorites", "glossary", "rights", "privacy"] as const) {
      expect(hasFeature("lt-lv", feature), feature).toBe(true);
    }
    expect(hasFeature("lt-lv", "verification")).toBe(false);
  });

  it("у Литвы на любом из трёх языков есть все разделы для посетителя, внутренней страницы проверки нет", () => {
    for (const locale of ["lt", "en-lt", "lv-lt"] as const) {
      for (const feature of ["favorites", "survey", "calculator", "match", "glossary", "rights", "privacy"] as const) {
        expect(hasFeature(locale, feature), `${locale}: ${feature}`).toBe(true);
      }
      expect(hasFeature(locale, "verification"), locale).toBe(false);
    }
  });

  // Анкета отправляет ответы в каталог параметрами фильтров. Если фильтра у
  // страны нет, ответ пропал бы молча — вопрос тогда задавать нельзя.
  it("анкета не спрашивает о том, что каталог страны применить не может", () => {
    for (const country of ["LV", "LT"] as const) {
      const { filters, surveySteps } = countryProfile(country);
      if (surveySteps.includes("interests")) expect(filters, country).toContain("interest");
      if (surveySteps.includes("fundingFee")) {
        expect(filters, country).toContain("fee");
        expect(filters, country).toContain("budget");
      }
      expect(new Set(surveySteps).size, country).toBe(surveySteps.length);
    }
  });

  it("в анкете — только уровни для выпускников школ", () => {
    expect(schoolLeaverLevels("LV")).toEqual(["bachelor", "college"]);
    expect(schoolLeaverLevels("LT")).toEqual(["bachelor", "college", "integrated"]);
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

describe("фильтры общего списка двух стран", () => {
  it("одна страна — её собственные фильтры, уровни и города", () => {
    for (const country of ["LV", "LT", "EE"] as const) {
      const single = catalogProfile([country]);
      const own = countryProfile(country);
      expect(single.filters, country).toEqual(
        ["interest", "fee", "budget", "mode"].filter((f) => (own.filters as readonly string[]).includes(f)),
      );
      expect(single.levels, country).toEqual(LEVEL_KEYS.filter((level) => own.levels.includes(level)));
      expect(single.languages, country).toEqual([...own.languages]);
      expect(single.citiesByCountry, country).toEqual([{ country, cities: own.cities }]);
    }
  });

  // «Только бюджет» и «не дороже» по общему списку молча убрали бы все
  // литовские программы: у них вид финансирования и цена не известны вовсе.
  it("обе страны: остаётся только фильтр, под который данные есть у обеих", () => {
    expect(catalogProfile(["LV", "LT"]).filters).toEqual(["interest", "mode"]);
  });

  // У Эстонии есть направления, но нет формы обучения (государственный
  // портал её не сообщает): в общем списке с ней остаётся только фильтр по
  // интересам, пока не выбрана страна.
  it("с Эстонией в общем списке остаётся только фильтр по интересам", () => {
    expect(countryProfile("EE").filters).toEqual(["interest"]);
    expect(catalogProfile(["LV", "LT", "EE"]).filters).toEqual(["interest"]);
    expect(catalogProfile(["LV", "LT", "EE"]).languages).toEqual(["lv", "en", "lt", "ru", "et"]);
  });

  it("обе страны: уровни и языки объединяются, города остаются по странам в порядке выбора", () => {
    const both = catalogProfile(["LV", "LT"]);
    expect(both.levels).toEqual(["bachelor", "master", "doctoral", "college", "integrated"]);
    expect(both.languages).toEqual(["lv", "en", "lt", "ru"]);
    expect(both.citiesByCountry.map((group) => group.country)).toEqual(["LV", "LT"]);
    expect(catalogProfile(["LT", "LV"]).languages).toEqual(["lt", "en", "ru", "lv"]);
    expect(catalogProfile(["LT", "LV"]).citiesByCountry[0].cities).toContain("vilnius");
  });
});
