import { describe, expect, it } from "vitest";
import { fieldCodesForInterests, interestOf, INTEREST_KEYS } from "./fields";

// Коды, реально присвоенные каталогу на 2026-09-19
// (pipeline/src/seed_programme_fields.py). Если правила разметки начнут
// выдавать код, который ни одна категория не покрывает, программа
// станет недостижимой из анкеты — то самое, что ревью назвало
// "бессмысленными фильтрами" — и этот тест это покажет.
const CODES_IN_CATALOG = [
  "141", "142", "211", "212", "213", "214", "221", "222", "223", "224", "226", "227",
  "310", "311", "312", "313", "314", "321", "322", "341", "342", "343", "344", "345",
  "380", "420", "421", "441", "442", "443", "460", "481", "484", "521", "522", "523",
  "524", "525", "526", "529", "541", "542", "581", "582", "621", "721", "722", "723",
  "724", "725", "726", "727", "762", "811", "812", "813", "815", "840", "850", "861",
  "862", "863",
];

describe("категории интересов анкеты", () => {
  it("каждый код направления из каталога попадает хотя бы в одну категорию", () => {
    const orphans = CODES_IN_CATALOG.filter((code) => interestOf(code) === null);
    expect(orphans).toEqual([]);
  });

  it("категории не пересекаются: код принадлежит ровно одной", () => {
    for (const code of CODES_IN_CATALOG) {
      const owners = INTEREST_KEYS.filter((key) => fieldCodesForInterests([key]).includes(code));
      expect(owners, `код ${code}`).toHaveLength(1);
    }
  });

  it("экономика (311) — в бизнесе, остальная область 31 — в обществе", () => {
    expect(interestOf("311")).toBe("business");
    expect(interestOf("313")).toBe("society");
    expect(interestOf("314")).toBe("society");
  });

  it("префикс из двух цифр разворачивается в десять кодов", () => {
    expect(fieldCodesForInterests(["it"])).toHaveLength(10);
    expect(fieldCodesForInterests(["it"])).toContain("481");
  });
});
