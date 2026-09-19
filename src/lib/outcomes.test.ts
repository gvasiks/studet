import { describe, expect, it } from "vitest";
import { employmentPercent, interpolate, pickOutcomes, type OutcomeRow } from "./outcomes";

const row = (overrides: Partial<OutcomeRow>): OutcomeRow => ({
  graduationYear: 2023,
  taxYear: 2024,
  levelCode: "43",
  graduates: 100,
  employed: 90,
  medianIncomeEur: null,
  ...overrides,
});

describe("pickOutcomes", () => {
  it("берёт только уровни, соответствующие уровню программы", () => {
    const rows = [row({ levelCode: "43", graduates: 50 }), row({ levelCode: "45", graduates: 500 })];
    const result = pickOutcomes(rows, "bachelor");
    expect(result).toHaveLength(1);
    expect(result[0].graduates).toBe(50);
  });

  it("при нескольких кодах уровня в одном году берёт самую большую ячейку", () => {
    const rows = [row({ levelCode: "42", graduates: 30 }), row({ levelCode: "43", graduates: 80 })];
    expect(pickOutcomes(rows, "bachelor")[0].graduates).toBe(80);
  });

  it("возвращает самый свежий выпуск и выпуск пятилетней давности", () => {
    const rows = [
      row({ graduationYear: 2023, taxYear: 2024, graduates: 100 }),
      row({ graduationYear: 2021, taxYear: 2024, graduates: 90 }),
      row({ graduationYear: 2019, taxYear: 2024, graduates: 80 }),
    ];
    const result = pickOutcomes(rows, "bachelor");
    expect(result.map((s) => s.graduationYear)).toEqual([2023, 2019]);
    expect(result.map((s) => s.yearsAfter)).toEqual([1, 5]);
  });

  it("если пятилетнего выпуска нет — только самый свежий", () => {
    expect(pickOutcomes([row({})], "bachelor")).toHaveLength(1);
  });

  it("пусто для неизвестного уровня и для отсутствия данных", () => {
    expect(pickOutcomes([row({})], "unknown")).toEqual([]);
    expect(pickOutcomes([], "bachelor")).toEqual([]);
    expect(pickOutcomes([row({ levelCode: "45" })], "bachelor")).toEqual([]);
  });

  it("сохраняет скрытый доход как null, а не как ноль", () => {
    expect(pickOutcomes([row({ medianIncomeEur: null })], "bachelor")[0].medianIncomeEur).toBeNull();
    expect(pickOutcomes([row({ medianIncomeEur: 21708.86 })], "bachelor")[0].medianIncomeEur).toBe(21708.86);
  });
});

describe("employmentPercent и interpolate", () => {
  it("считает долю занятых от всех выпускников ячейки", () => {
    expect(employmentPercent({ graduates: 2951, employed: 2574 })).toBe(87);
    expect(employmentPercent({ graduates: 0, employed: 0 })).toBe(0);
  });

  it("подставляет значения и оставляет незнакомые метки как есть", () => {
    expect(interpolate("{a} из {b}, {c}", { a: 2, b: "три" })).toBe("2 из три, {c}");
  });
});
