import { describe, expect, it } from "vitest";
import type { ProgrammeWithUniversity } from "./catalog";
import { catalogQuery, hasActiveFilters, PAGE_SIZE, parseCatalogState } from "./catalog-query";
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
    expect(view.levelCounts).toEqual({ bachelor: 2, master: 1, doctoral: 1, college: 0 });
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
