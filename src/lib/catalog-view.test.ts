import { describe, expect, it } from "vitest";
import type { ProgrammeWithUniversity } from "./catalog";
import { catalogQuery, hasActiveFilters, onlySupported, PAGE_SIZE, parseCatalogState } from "./catalog-query";
import { buildCatalogView, matchesQuery, normalize } from "./catalog-view";

const programme = (
  name_en: string,
  degree_level: string,
  university: { name_lv: string; name_en: string },
  name_lv: string | null = null,
): ProgrammeWithUniversity =>
  ({
    id: name_en,
    name_en,
    name_lv,
    degree_level,
    university: { slug: "x", city: "riga", ...university },
  }) as unknown as ProgrammeWithUniversity;

const LU = { name_lv: "Latvijas Universitāte", name_en: "University of Latvia" };
const RTU = { name_lv: "Rīgas Tehniskā universitāte", name_en: "Riga Technical University" };

const CATALOG = [
  programme("Economics", "bachelor", LU),
  programme("Economics", "master", LU),
  programme("Architecture", "bachelor", RTU, "Arhitektūra"),
  programme("Physics", "doctoral", LU),
];

describe("поиск", () => {
  it("не различает регистр и диакритику", () => {
    expect(normalize("Rīgas Tehniskā")).toBe("rigas tehniska");
  });

  it("находит по названию вуза без диакритики", () => {
    expect(matchesQuery(CATALOG[2], "riga")).toBe(true);
    expect(matchesQuery(CATALOG[0], "riga")).toBe(false);
  });

  it("требует все слова запроса, в любом порядке, и ищет в обоих языках", () => {
    expect(matchesQuery(CATALOG[2], "arhitektura tehniska")).toBe(true);
    expect(matchesQuery(CATALOG[2], "architecture technical")).toBe(true);
    expect(matchesQuery(CATALOG[2], "architecture latvijas")).toBe(false);
  });

  it("пустой запрос подходит всему", () => {
    expect(matchesQuery(CATALOG[0], "  ")).toBe(true);
  });
});

describe("вид каталога", () => {
  const state = parseCatalogState({});

  it("считает табы по набору до выбора уровня — иначе остальные табы показывали бы нули", () => {
    const view = buildCatalogView(CATALOG, { ...state, level: "master" }, "en");
    expect(view.levelCounts).toEqual({ bachelor: 2, master: 1, doctoral: 1, college: 0, integrated: 0 });
    expect(view.total).toBe(1);
    expect(view.matched).toBe(4);
  });

  it("сортирует по названию с учётом языка и по вузу", () => {
    const byName = buildCatalogView(CATALOG, state, "en").visible.map((p) => p.name_en);
    expect(byName).toEqual(["Architecture", "Economics", "Economics", "Physics"]);
    const desc = buildCatalogView(CATALOG, { ...state, sort: "name_desc" }, "en").visible.map((p) => p.name_en);
    expect(desc[0]).toBe("Physics");
    const byUniversity = buildCatalogView(CATALOG, { ...state, sort: "university" }, "en").visible;
    expect(byUniversity[0].university.name_en).toBe("Riga Technical University");
  });

  it("отдаёт только limit карточек, но total — все подошедшие", () => {
    const many = Array.from({ length: 30 }, (_, i) => programme(`P${String(i).padStart(2, "0")}`, "bachelor", LU));
    const view = buildCatalogView(many, state, "en");
    expect(view.visible).toHaveLength(PAGE_SIZE);
    expect(view.total).toBe(30);
    expect(buildCatalogView(many, { ...state, limit: 24 }, "en").visible).toHaveLength(24);
  });
});

describe("адрес каталога", () => {
  it("значения по умолчанию в ссылку не попадают", () => {
    expect(catalogQuery(parseCatalogState({}))).toBe("");
  });

  it("разбор и сборка взаимно обратны", () => {
    const state = parseCatalogState({
      q: "ekonomika",
      sort: "university",
      level: "master",
      limit: "24",
      city: ["riga", "jelgava"],
      interest: "it,law",
      budget: "1",
    });
    expect(parseCatalogState(Object.fromEntries(new URLSearchParams(catalogQuery(state).slice(1))))).toMatchObject({
      q: "ekonomika",
      sort: "university",
      level: "master",
      limit: 24,
      budgetOnly: true,
    });
    expect(catalogQuery(state)).toContain("city=riga&city=jelgava");
    expect(state.interests).toEqual(["it", "law"]);
  });

  it("отбрасывает мусорные значения: неизвестную сортировку, уровень и огромный limit", () => {
    const state = parseCatalogState({ sort: "hack", level: "phd", limit: "999999" });
    expect(state.sort).toBe("name");
    expect(state.level).toBeNull();
    expect(state.limit).toBe(600);
  });

  it("сортировка и число карточек — не фильтры", () => {
    expect(hasActiveFilters(parseCatalogState({ sort: "name_desc", limit: "24" }))).toBe(false);
    expect(hasActiveFilters(parseCatalogState({ q: "x" }))).toBe(true);
  });
});

describe("длительность и плата", () => {
  const withFacts = (name: string, duration_years: number | null, tuition_fee_amount: number | null) =>
    ({ ...programme(name, "bachelor", LU), duration_years, tuition_fee_amount }) as ProgrammeWithUniversity;

  const FACTS = [
    withFacts("Short cheap", 3, 2500),
    withFacts("Four years", 4, 3500),
    withFacts("Long expensive", 5.5, 6000),
    withFacts("Unknown", null, null),
  ];
  const names = (sp: Record<string, string>) =>
    buildCatalogView(FACTS, parseCatalogState(sp), "en").visible.map((p) => p.name_en);

  it("порог длительности включает программы ровно на границе", () => {
    expect(names({ years: "3" })).toEqual(["Short cheap", "Unknown"]);
    expect(names({ years: "4" })).toEqual(["Four years", "Short cheap", "Unknown"]);
  });

  it("порог платы работает так же", () => {
    expect(names({ fee: "3000" })).toEqual(["Short cheap", "Unknown"]);
    expect(names({ fee: "4000" })).toEqual(["Four years", "Short cheap", "Unknown"]);
  });

  it("программа без длительности или платы остаётся в списке — пробел в данных не считается «долго» или «дорого»", () => {
    expect(names({ years: "3", fee: "3000" })).toContain("Unknown");
  });

  it("оба порога действуют вместе, счётчики табов считаются уже после них", () => {
    const view = buildCatalogView(FACTS, parseCatalogState({ years: "4", fee: "3000" }), "en");
    expect(view.visible.map((p) => p.name_en)).toEqual(["Short cheap", "Unknown"]);
    expect(view.levelCounts.bachelor).toBe(2);
  });

  it("принимает только известные пороги; остальное — «без ограничения»", () => {
    expect(parseCatalogState({ years: "7", fee: "abc" })).toMatchObject({ maxYears: null, maxFee: null });
    expect(parseCatalogState({ years: "3", fee: "4000" })).toMatchObject({ maxYears: 3, maxFee: 4000 });
  });

  it("пороги попадают в адрес и считаются фильтрами", () => {
    const state = parseCatalogState({ years: "4", fee: "3000" });
    expect(catalogQuery(state)).toBe("?years=4&fee=3000");
    expect(hasActiveFilters(state)).toBe(true);
  });
});

describe("государственный или частный вуз", () => {
  it("принимает только public и private", () => {
    expect(parseCatalogState({ kind: "private" }).kind).toBe("private");
    expect(parseCatalogState({ kind: "public" }).kind).toBe("public");
    expect(parseCatalogState({ kind: "secret" }).kind).toBeNull();
    expect(parseCatalogState({}).kind).toBeNull();
  });

  it("попадает в адрес и считается фильтром", () => {
    const state = parseCatalogState({ kind: "private" });
    expect(catalogQuery(state)).toBe("?kind=private");
    expect(hasActiveFilters(state)).toBe(true);
  });
});

describe("фильтры, под которые у страны нет данных", () => {
  const state = parseCatalogState({ budget: "1", fee: "3000", interest: "it,law", city: "vilnius", q: "teise" });

  it("страна со всеми фильтрами — состояние не меняется", () => {
    expect(onlySupported(state, ["interest", "fee", "budget"])).toEqual(state);
  });

  it("страна без фильтров — плата, бюджет и интересы сброшены, остальное на месте", () => {
    const limited = onlySupported(state, []);
    expect(limited).toMatchObject({ budgetOnly: false, maxFee: null, interests: [], cities: ["vilnius"], q: "teise" });
    // В ссылках «показать ещё» и сортировки сброшенных фильтров тоже нет.
    expect(catalogQuery(limited)).toBe("?q=teise&city=vilnius");
  });

  it("каждый фильтр сбрасывается отдельно", () => {
    expect(onlySupported(state, ["interest"])).toMatchObject({ budgetOnly: false, maxFee: null, interests: ["it", "law"] });
    expect(onlySupported(state, ["fee"])).toMatchObject({ budgetOnly: false, maxFee: 3000, interests: [] });
    expect(onlySupported(state, ["budget"])).toMatchObject({ budgetOnly: true, maxFee: null, interests: [] });
  });
});
