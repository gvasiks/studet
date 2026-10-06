import { describe, expect, it } from "vitest";
import { INTEREST_KEYS } from "./fields";
import { ltFieldCodesForInterests, ltInterestOf } from "./lt-fields";

// Все 102 направления из списка общего приёма LAMA BPO на 2026-10-06.
const OFFICIAL_FIELDS = [
  "A01", "A02", "A03", "B01", "B02", "B03", "B04", "C01", "C02", "C03", "C04", "C05",
  "D01", "D02", "D03", "D04", "D05", "D06", "D07",
  "E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12", "E13", "E14",
  "F01", "F02", "F03", "F04", "F05", "F06",
  "G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09", "G10", "H01",
  "I01", "I02", "I03", "I04", "I06",
  "J01", "J02", "J03", "J04", "J06", "J07", "J09", "J10", "J11", "J12", "K01",
  "L01", "L02", "L03", "L04", "L05", "L07", "L08", "M01", "M02",
  "N01", "N03", "N04", "N05", "N06", "N07", "N08", "N09", "N10", "N11", "N12", "N14", "N15",
  "P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10", "R01", "R02", "S01", "S02",
];

describe("литовские направления и категории интересов", () => {
  it("в списке ровно 102 направления", () => {
    expect(new Set(OFFICIAL_FIELDS).size).toBe(102);
  });

  it("у каждого официального направления есть категория — ни одна программа не выпадает из анкеты", () => {
    for (const code of OFFICIAL_FIELDS) expect(ltInterestOf(code), code).not.toBeNull();
  });

  it("категория по группе", () => {
    expect(ltInterestOf("B01")).toBe("it");
    expect(ltInterestOf("E14")).toBe("engineering");
    expect(ltInterestOf("G01")).toBe("health");
    expect(ltInterestOf("K01")).toBe("law");
    expect(ltInterestOf("L02")).toBe("business");
    expect(ltInterestOf("N04")).toBe("humanities");
    expect(ltInterestOf("P02")).toBe("arts");
  });

  it("исключения внутри группы — по смыслу, как у Латвии", () => {
    expect(ltInterestOf("J01")).toBe("business"); // экономика
    expect(ltInterestOf("J04")).toBe("health"); // социальная работа
    expect(ltInterestOf("J07")).toBe("society"); // психология
    expect(ltInterestOf("J10")).toBe("humanities"); // коммуникация
    expect(ltInterestOf("L08")).toBe("services"); // туризм
    expect(ltInterestOf("P09")).toBe("engineering"); // архитектура
  });

  it("не код направления — null", () => {
    for (const bad of ["", "E", "E1", "e14", "311", "EE1", "Z01"]) expect(ltInterestOf(bad), bad).toBeNull();
  });

  it("каждая категория анкеты находит хотя бы одно официальное направление", () => {
    for (const key of INTEREST_KEYS) {
      const codes = new Set(ltFieldCodesForInterests([key]));
      expect(OFFICIAL_FIELDS.some((code) => codes.has(code)), key).toBe(true);
    }
  });

  it("коды для фильтра согласованы с ltInterestOf", () => {
    const business = ltFieldCodesForInterests(["business"]);
    expect(business).toContain("J01");
    expect(business).toContain("L01");
    expect(business).not.toContain("L08");
    expect(business).not.toContain("J07");
    for (const code of business) expect(ltInterestOf(code)).toBe("business");
  });

  it("все категории вместе покрывают все 102 направления; пустой выбор — пустой список", () => {
    const all = new Set(ltFieldCodesForInterests([...INTEREST_KEYS]));
    for (const code of OFFICIAL_FIELDS) expect(all.has(code), code).toBe(true);
    expect(ltFieldCodesForInterests([])).toEqual([]);
  });
});
