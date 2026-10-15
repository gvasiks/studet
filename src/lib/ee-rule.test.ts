import { describe, expect, it } from "vitest";
import { parseRule } from "./ee-rule";

// Образцы — в той форме, в какой их пишет pipeline/src/ee_rules.py.
const informatics = {
  model: "weighted",
  variants: [
    [
      { exam: "estonian", weight: 40 },
      { exam: "math", weight: 60 },
    ],
    [{ other: "Programmeerimise sisseastumiseksam", weight: 100 }],
  ],
  apply_min: 66,
  guarantee_min: 80,
  wide_math_bonus: 16,
  medal_bonus: 3,
  requirements: {},
};

const logistics = {
  model: "thresholds",
  apply: { math: 35, estonian: 35, estonian_second: 45 },
  guarantee: { math: 60, estonian: 50, estonian_second: 60 },
  places: 60,
  ranking: true,
  wide_math: true,
};

describe("правило конкурса эстонской программы", () => {
  it("балл с весами (Тартуский университет)", () => {
    expect(parseRule(informatics)).toEqual({
      model: "weighted",
      variants: informatics.variants,
      applyMin: 66,
      guaranteeMin: 80,
      wideMathBonus: 16,
      medalBonus: 3,
      english: null,
    });
    // порогов со страницы вуза может не быть
    const bare = parseRule({ ...informatics, apply_min: null, guarantee_min: null, wide_math_bonus: null, medal_bonus: null });
    expect(bare).toMatchObject({ applyMin: null, guaranteeMin: null, wideMathBonus: null, medalBonus: null });
    expect(parseRule({ ...informatics, requirements: { english: "B2" } })).toMatchObject({ english: "B2" });
  });

  it("пороги (TalTech)", () => {
    expect(parseRule(logistics)).toEqual({
      model: "thresholds",
      apply: { math: 35, estonian: 35, estonianSecond: 45, english: null },
      guarantee: { math: 60, estonian: 50, estonianSecond: 60, english: null },
      places: 60,
      ranking: true,
    });
    const onlyThreshold = parseRule({ ...logistics, apply: null, places: null, ranking: false });
    expect(onlyThreshold).toMatchObject({ apply: null, places: null, ranking: false });
    const english = parseRule({ ...logistics, guarantee: { ...logistics.guarantee, english: "C1" } });
    expect(english).toMatchObject({ guarantee: { english: "C1" } });
  });

  it("незнакомая или неполная форма — правила нет, а не половина правила", () => {
    expect(parseRule(null)).toBeNull();
    expect(parseRule([])).toBeNull();
    expect(parseRule({ model: "formula" })).toBeNull();
    // доли не дают 100
    expect(parseRule({ ...informatics, variants: [[{ exam: "math", weight: 60 }]] })).toBeNull();
    // незнакомый экзамен
    expect(parseRule({ ...informatics, variants: [[{ exam: "physics", weight: 100 }]] })).toBeNull();
    expect(parseRule({ ...informatics, variants: [] })).toBeNull();
    expect(parseRule({ ...informatics, guarantee_min: 140 })).toBeNull();
    expect(parseRule({ ...informatics, requirements: { english: "A2" } })).toBeNull();
    // с рейтингом нужны порог для подачи и число мест; без рейтинга их быть не должно
    expect(parseRule({ ...logistics, places: null })).toBeNull();
    expect(parseRule({ ...logistics, apply: null })).toBeNull();
    expect(parseRule({ ...logistics, ranking: false })).toBeNull();
    expect(parseRule({ ...logistics, guarantee: { math: 60, estonian: 50 } })).toBeNull();
    expect(parseRule({ ...logistics, places: 0 })).toBeNull();
  });
});
