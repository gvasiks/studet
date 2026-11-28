import { describe, expect, it } from "vitest";
import { eeMatch } from "./ee-match";
import type { EeThresholdRule } from "./ee-rule";

// Informaatika ja tehisintellekt (IAIB), TalTech 2027/28: подача 65 · 55 · 65,
// гарантия 75 · 60 · 70, 150 мест.
const iaib: EeThresholdRule = {
  model: "thresholds",
  apply: { math: 65, estonian: 55, estonianSecond: 65, english: null },
  guarantee: { math: 75, estonian: 60, estonianSecond: 70, english: null },
  places: 150,
  ranking: true,
};

// Rakenduslik majandusteadus: только порог, без рейтинга, нужен английский B2.
const economics: EeThresholdRule = {
  model: "thresholds",
  apply: null,
  guarantee: { math: 70, estonian: 55, estonianSecond: 75, english: "B2" },
  places: null,
  ranking: false,
};

const wide = (score: number) => ({ score, kind: "wide" as const });
const native = (score: number) => ({ score, kind: "native" as const });
const second = (score: number) => ({ score, kind: "second" as const });

describe("«куда можно поступить» в Эстонии по порогам", () => {
  it("гарантирующий порог пройден", () => {
    expect(eeMatch(iaib, { math: wide(80), estonian: native(60) })).toEqual({ status: "guaranteed", missing: [] });
  });

  it("порог для подачи пройден, гарантирующий нет", () => {
    expect(eeMatch(iaib, { math: wide(70), estonian: native(60) }).status).toBe("applyPassed");
    // ровно на пороге — пройден («не меньше»)
    expect(eeMatch(iaib, { math: wide(65), estonian: native(55) }).status).toBe("applyPassed");
  });

  it("порог для подачи не пройден", () => {
    expect(eeMatch(iaib, { math: wide(64), estonian: native(90) }).status).toBe("applyFailed");
  });

  it("эстонский как второй сравнивается со своим порогом", () => {
    // 60 по эстонскому как второму ниже 65 — подача не пройдена
    expect(eeMatch(iaib, { math: wide(90), estonian: second(60) }).status).toBe("applyFailed");
    expect(eeMatch(iaib, { math: wide(90), estonian: second(70) }).status).toBe("guaranteed");
  });

  it("узкая математика — правило требует широкую", () => {
    expect(eeMatch(iaib, { math: { score: 95, kind: "narrow" } })).toEqual({ status: "wideMathRequired", missing: [] });
  });

  it("не хватает экзаменов", () => {
    expect(eeMatch(iaib, { math: wide(80) })).toEqual({ status: "incomplete", missing: ["estonian"] });
    expect(eeMatch(economics, { math: wide(80), estonian: native(60) })).toEqual({ status: "incomplete", missing: ["english"] });
  });

  it("приём только по порогу: пройден или нет, английский учитывается", () => {
    expect(eeMatch(economics, { math: wide(70), estonian: native(55), english: "B2" }).status).toBe("guaranteed");
    expect(eeMatch(economics, { math: wide(70), estonian: native(55), english: "C1" }).status).toBe("guaranteed");
    expect(eeMatch(economics, { math: wide(70), estonian: native(55), english: "B1" }).status).toBe("thresholdFailed");
    expect(eeMatch(economics, { math: wide(69), estonian: native(80), english: "C1" }).status).toBe("thresholdFailed");
  });
});
