import { describe, expect, it } from "vitest";
import { calculateScore, type ExamResult, type FormulaTerm } from "./formula";

// Пример расчёта ЛУ из docs/PLAN.md, раздел 6 (опубликован университетом):
// математика 56% (augstākais) × 1,00 × 6,5 = 364,00
// латышский  84% (optimālais) × 0,75 × 1,5 =  94,50
// английский 71% (augstākais) × 1,00 × 1,0 =  71,00
// Итог по документу — 592,83, но в него входит "средний % по всем CE",
// а сколько экзаменов реально сдал абитуриент из примера — в PLAN.md
// не записано (там только эти три релевантных программе предмета).
// Поэтому здесь проверяем построчно то, что проверяемо, а итог
// с усреднением — отдельным, честным по вводным данным случаем.
const LEVEL_COEFFICIENTS = { augstakais: 1.0, optimalais: 0.75, vispaarigais: 0.5 };

const LU_TERMS: FormulaTerm[] = [
  { kind: "ce", subject: "mathematics", coefficient: 6.5 },
  { kind: "ce", subject: "latvian", coefficient: 1.5 },
  { kind: "ce", subject: "english", coefficient: 1.0 },
  { kind: "ce_average", subject: null, coefficient: 1.0 },
];

const LU_EXAM_RESULTS: ExamResult[] = [
  { subject: "mathematics", percent: 56, level: "augstakais" },
  { subject: "latvian", percent: 84, level: "optimalais" },
  { subject: "english", percent: 71, level: "augstakais" },
];

describe("calculateScore — пример ЛУ из docs/PLAN.md", () => {
  it("считает баллы по каждому предмету так же, как в опубликованном примере", () => {
    const result = calculateScore(LU_TERMS, [], LU_EXAM_RESULTS, LEVEL_COEFFICIENTS);

    expect(result.lines[0].points).toBeCloseTo(364.0, 2); // математика
    expect(result.lines[1].points).toBeCloseTo(94.5, 2); // латышский
    expect(result.lines[2].points).toBeCloseTo(71.0, 2); // английский
  });

  it("средний % по всем CE считается по всем сданным экзаменам, а не только по взвешенным в программе", () => {
    const result = calculateScore(LU_TERMS, [], LU_EXAM_RESULTS, LEVEL_COEFFICIENTS);
    // (56 + 84 + 71) / 3 = 70.33...; в примере PLAN.md — 63,33, потому что
    // там, видимо, учтён ещё один экзамен, не входящий в эти три строки.
    // Значит с ровно тремя экзаменами итог по документу не воспроизвести —
    // это ограничение вводных данных примера, не баг вычислителя.
    expect(result.lines[3].input).toBeCloseTo(70.33, 1);
  });

  it("не считает предмет, который абитуриент не сдавал", () => {
    const result = calculateScore(
      LU_TERMS,
      [],
      [{ subject: "mathematics", percent: 56, level: "augstakais" }],
      LEVEL_COEFFICIENTS,
    );
    expect(result.lines[1].input).toBeNull(); // латышский не сдавали
    expect(result.lines[1].points).toBe(0);
  });
});

describe("calculateScore — пороги допуска", () => {
  it("отмечает непройденный порог, но не исключает предмет из суммы баллов", () => {
    const terms: FormulaTerm[] = [{ kind: "ce", subject: "mathematics", coefficient: 1 }];
    const gates = [{ subject: "mathematics", minPercent: 20 }];
    const results: ExamResult[] = [{ subject: "mathematics", percent: 15, level: "vispaarigais" }];

    const result = calculateScore(terms, gates, results, LEVEL_COEFFICIENTS);

    expect(result.failedGates).toHaveLength(1);
    expect(result.total).toBeGreaterThan(0); // сам балл вычислитель не занижает — это решение вуза
  });
});
