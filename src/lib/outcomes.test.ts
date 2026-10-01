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

// «Сейчас» для тестов — фиксированный год, чтобы результат не зависел от
// даты запуска.
const NOW = 2026;

describe("pickOutcomes", () => {
  it("берёт только уровни, соответствующие уровню программы", () => {
    const rows = [row({ levelCode: "43", graduates: 50 }), row({ levelCode: "45", graduates: 500 })];
    const result = pickOutcomes(rows, "bachelor", NOW);
    expect(result).toHaveLength(1);
    expect(result[0].graduates).toBe(50);
  });

  it("при нескольких кодах уровня в одном году берёт самую большую ячейку", () => {
    const rows = [row({ levelCode: "42", graduates: 30 }), row({ levelCode: "43", graduates: 80 })];
    expect(pickOutcomes(rows, "bachelor", NOW)[0].graduates).toBe(80);
  });

  it("возвращает самый свежий выпуск и выпуск пятилетней давности", () => {
    const rows = [
      row({ graduationYear: 2023, taxYear: 2024, graduates: 100 }),
      row({ graduationYear: 2021, taxYear: 2024, graduates: 90 }),
      row({ graduationYear: 2019, taxYear: 2024, graduates: 80 }),
    ];
    const result = pickOutcomes(rows, "bachelor", NOW);
    expect(result.map((s) => s.graduationYear)).toEqual([2023, 2019]);
    expect(result.map((s) => s.yearsAfter)).toEqual([1, 5]);
  });

  it("если пятилетнего выпуска нет — только самый свежий", () => {
    expect(pickOutcomes([row({})], "bachelor", NOW)).toHaveLength(1);
  });

  it("пусто для неизвестного уровня и для отсутствия данных", () => {
    expect(pickOutcomes([row({})], "unknown", NOW)).toEqual([]);
    expect(pickOutcomes([], "bachelor", NOW)).toEqual([]);
    expect(pickOutcomes([row({ levelCode: "45" })], "bachelor", NOW)).toEqual([]);
  });

  it("не показывает ничего, если самый свежий выпуск старше пяти лет", () => {
    // 2026 − 2021 = 5 — ещё показываем; 2026 − 2020 = 6 — уже нет
    expect(pickOutcomes([row({ graduationYear: 2021, taxYear: 2022 })], "bachelor", NOW)).toHaveLength(1);
    expect(pickOutcomes([row({ graduationYear: 2020, taxYear: 2021 })], "bachelor", NOW)).toEqual([]);
    // тот же выпуск 2021 года через год становится слишком старым
    expect(pickOutcomes([row({ graduationYear: 2021, taxYear: 2022 })], "bachelor", 2027)).toEqual([]);
  });

  it("старый выпуск для сравнения остаётся рядом со свежим", () => {
    const rows = [
      row({ graduationYear: 2023, taxYear: 2024 }),
      row({ graduationYear: 2019, taxYear: 2024 }),
    ];
    expect(pickOutcomes(rows, "bachelor", NOW).map((s) => s.graduationYear)).toEqual([2023, 2019]);
  });

  it("сохраняет скрытый доход как null, а не как ноль", () => {
    expect(pickOutcomes([row({ medianIncomeEur: null })], "bachelor", NOW)[0].medianIncomeEur).toBeNull();
    expect(pickOutcomes([row({ medianIncomeEur: 21708.86 })], "bachelor", NOW)[0].medianIncomeEur).toBe(21708.86);
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
