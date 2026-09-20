import { describe, expect, it } from "vitest";
import type { ExamLevel, ExamResult } from "./formula";
import { calculateScore } from "./formula";
import { matchFormula, matchProgrammes, type MatchFormula } from "./match";

const LEVELS: Record<ExamLevel, number> = { augstakais: 1, optimalais: 0.75, vispaarigais: 0.5 };

function formula(overrides: Partial<MatchFormula> & Pick<MatchFormula, "programmeName">): MatchFormula {
  return {
    formulaId: overrides.programmeName,
    programmeSlug: overrides.programmeName.toLowerCase(),
    universitySlug: "u1",
    universityName: "Universitāte A",
    verifiedAt: "2026-12-10T10:00:00Z",
    sourceUrl: null,
    terms: [
      { kind: "ce", subject: "mathematics", coefficient: 0.5 },
      { kind: "ce", subject: "english", coefficient: 0.3 },
    ],
    gates: [],
    ...overrides,
  };
}

const MATH_ENGLISH: ExamResult[] = [
  { subject: "mathematics", percent: 80, level: "augstakais" },
  { subject: "english", percent: 60, level: "optimalais" },
];

describe("обратный поиск: matchFormula", () => {
  it("все предметы есть — балл считается тем же вычислителем, что и на сайте", () => {
    const f = formula({ programmeName: "Economics" });
    const item = matchFormula(f, MATH_ENGLISH, LEVELS);
    expect(item.status).toBe("computed");
    expect(item.score?.total).toBe(calculateScore(f.terms, f.gates, MATH_ENGLISH, LEVELS).total);
    // 80*1*0.5 + 60*0.75*0.3 = 40 + 13.5
    expect(item.score?.total).toBeCloseTo(53.5);
  });

  it("не хватает предмета — балла нет вовсе, а не частичный", () => {
    const f = formula({
      programmeName: "Physics",
      terms: [
        { kind: "ce", subject: "mathematics", coefficient: 0.5 },
        { kind: "ce", subject: "physics", coefficient: 0.5 },
      ],
    });
    const item = matchFormula(f, MATH_ENGLISH, LEVELS);
    expect(item.status).toBe("missing_exams");
    expect(item.score).toBeNull();
    expect(item.missingSubjects).toEqual(["physics"]);
  });

  it("предмет из порога (formula_gate) тоже обязателен", () => {
    const f = formula({ programmeName: "Law", gates: [{ subject: "history", minPercent: 30 }] });
    const item = matchFormula(f, MATH_ENGLISH, LEVELS);
    expect(item.status).toBe("missing_exams");
    expect(item.missingSubjects).toEqual(["history"]);
  });

  it("порог не пройден — балл показывается, но группа отдельная", () => {
    const f = formula({ programmeName: "Medicine", gates: [{ subject: "english", minPercent: 70 }] });
    const item = matchFormula(f, MATH_ENGLISH, LEVELS);
    expect(item.status).toBe("gate_failed");
    expect(item.failedGates).toEqual([{ subject: "english", minPercent: 70 }]);
    expect(item.score).not.toBeNull();
  });

  it("вступительное испытание или оценка аттестата — нужен ввод, которого здесь нет", () => {
    const f = formula({
      programmeName: "Design",
      terms: [
        { kind: "ce", subject: "mathematics", coefficient: 0.5 },
        { kind: "entrance_exam", subject: "art_test", coefficient: 0.5 },
      ],
    });
    const item = matchFormula(f, MATH_ENGLISH, LEVELS);
    expect(item.status).toBe("missing_extras");
    expect(item.score).toBeNull();
    expect(item.missingExtras).toHaveLength(1);
  });

  it("недостающий экзамен важнее недостающего испытания", () => {
    const f = formula({
      programmeName: "Both",
      terms: [
        { kind: "ce", subject: "physics", coefficient: 0.5 },
        { kind: "certificate", subject: null, coefficient: 0.5 },
      ],
    });
    expect(matchFormula(f, MATH_ENGLISH, LEVELS).status).toBe("missing_exams");
  });

  it("без единого экзамена формула со средним по CE посчитана быть не может", () => {
    const f = formula({ programmeName: "Average", terms: [{ kind: "ce_average", subject: null, coefficient: 1 }] });
    expect(matchFormula(f, [], LEVELS).status).toBe("missing_exams");
    expect(matchFormula(f, MATH_ENGLISH, LEVELS).status).toBe("computed");
  });

  it("уровень экзамена меняет балл: оптимальный = 0,75 от высшего", () => {
    const f = formula({ programmeName: "Level", terms: [{ kind: "ce", subject: "mathematics", coefficient: 1 }] });
    const high = matchFormula(f, [{ subject: "mathematics", percent: 80, level: "augstakais" }], LEVELS);
    const optimal = matchFormula(f, [{ subject: "mathematics", percent: 80, level: "optimalais" }], LEVELS);
    expect(high.score?.total).toBe(80);
    expect(optimal.score?.total).toBe(60);
  });
});

describe("обратный поиск: matchProgrammes", () => {
  it("раскладывает по группам и сортирует по вузу и названию, а не по баллу", () => {
    const formulas = [
      formula({ programmeName: "Zoology", universityName: "B" }),
      formula({ programmeName: "Algebra", universityName: "B" }),
      formula({ programmeName: "Chemistry", universityName: "A", terms: [{ kind: "ce", subject: "chemistry", coefficient: 1 }] }),
      formula({ programmeName: "Biology", universityName: "A" }),
    ];
    const groups = matchProgrammes(formulas, MATH_ENGLISH, LEVELS);

    expect(groups.computed.map((i) => i.formula.programmeName)).toEqual(["Biology", "Algebra", "Zoology"]);
    expect(groups.missing_exams.map((i) => i.formula.programmeName)).toEqual(["Chemistry"]);
    expect(groups.gate_failed).toEqual([]);
  });

  it("без формул — пустые группы", () => {
    expect(matchProgrammes([], MATH_ENGLISH, LEVELS)).toEqual({
      computed: [],
      missing_exams: [],
      missing_extras: [],
      gate_failed: [],
    });
  });
});
