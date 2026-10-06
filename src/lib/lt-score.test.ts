import { describe, expect, it } from "vitest";
import { examValue, ltScore, type LtFormula } from "./lt-score";

// Формулы — как в открытом файле официального калькулятора (2026 год).
const ANY_THIRD = [
  "biology", "chemistry", "physics", "geography", "informatics", "history", "mathematics",
  "foreign_language", "minority_language", "economics", "philosophy", "engineering",
];

// Политические науки (J02): история 0,4.
const POLITICS: LtFormula = [
  { position: 1, weight: 0.4, mode: "one_of", subjects: ["history"] },
  { position: 2, weight: 0.2, mode: "one_of", subjects: ["mathematics", "informatics", "geography", "foreign_language", "economics"] },
  { position: 3, weight: 0.2, mode: "one_of", subjects: ANY_THIRD.filter((subject) => subject !== "history") },
  { position: 4, weight: 0.2, mode: "one_of", subjects: ["lithuanian"] },
];

// Экономика, управление (J01, L01–L06): математика 0,4.
const BUSINESS: LtFormula = [
  { position: 1, weight: 0.4, mode: "one_of", subjects: ["mathematics"] },
  { position: 2, weight: 0.2, mode: "one_of", subjects: ["history", "informatics", "geography", "foreign_language", "economics"] },
  { position: 3, weight: 0.2, mode: "one_of", subjects: ANY_THIRD.filter((subject) => subject !== "mathematics") },
  { position: 4, weight: 0.2, mode: "one_of", subjects: ["lithuanian"] },
];

// Психология (J07): математика 0,4, биология 0,2.
const PSYCHOLOGY: LtFormula = [
  { position: 1, weight: 0.4, mode: "one_of", subjects: ["mathematics"] },
  { position: 2, weight: 0.2, mode: "one_of", subjects: ["biology"] },
  { position: 3, weight: 0.2, mode: "one_of", subjects: ANY_THIRD.filter((subject) => !["mathematics", "biology"].includes(subject)) },
  { position: 4, weight: 0.2, mode: "one_of", subjects: ["lithuanian"] },
];

// Медицина (G01): второе — среднее химии и математики.
const MEDICINE: LtFormula = [
  { position: 1, weight: 0.4, mode: "one_of", subjects: ["biology"] },
  { position: 2, weight: 0.2, mode: "average", subjects: ["chemistry", "mathematics"] },
  { position: 3, weight: 0.2, mode: "one_of", subjects: ANY_THIRD.filter((subject) => subject !== "biology") },
  { position: 4, weight: 0.2, mode: "one_of", subjects: ["lithuanian"] },
];

// Филология (N01…): литовский 0,4, иностранный — четвёртым.
const PHILOLOGY: LtFormula = [
  { position: 1, weight: 0.4, mode: "one_of", subjects: ["lithuanian"] },
  { position: 2, weight: 0.2, mode: "one_of", subjects: ["history", "geography", "mathematics", "informatics", "second_foreign_language"] },
  { position: 3, weight: 0.2, mode: "one_of", subjects: ANY_THIRD.map((subject) => (subject === "foreign_language" ? "second_foreign_language" : subject)) },
  { position: 4, weight: 0.2, mode: "one_of", subjects: ["foreign_language"] },
];

describe("examValue", () => {
  it("делит оценку экзамена на десять", () => {
    expect(examValue("history", { score: 50 })).toBe(5);
    expect(examValue("history", { score: 100 })).toBe(10);
    expect(examValue("history", { score: 30 })).toBe(3);
  });

  it("общий курс (B) литовского и математики — с коэффициентом 0,7", () => {
    expect(examValue("mathematics", { score: 50, course: "B" })).toBeCloseTo(3.5);
    expect(examValue("lithuanian", { score: 70, course: "B" })).toBeCloseTo(4.9);
    expect(examValue("mathematics", { score: 50, course: "A" })).toBe(5);
    expect(examValue("mathematics", { score: 50 })).toBe(5);
  });

  it("у остальных предметов курса нет — пометка B ничего не меняет", () => {
    expect(examValue("history", { score: 50, course: "B" })).toBe(5);
  });

  it("оценка ниже 30, выше 100 или не число — не засчитывается", () => {
    expect(examValue("history", { score: 29 })).toBeNull();
    expect(examValue("history", { score: 101 })).toBeNull();
    expect(examValue("history", { score: Number.NaN })).toBeNull();
    expect(examValue("history", undefined)).toBeNull();
  });
});

// Примеры с готовым ответом из материалов приёмной службы («Studentų
// priėmimo aktualijos 2026 m.», слайды «Konkursinio balo formavimas»).
// Запись на слайде «VBE1 = 50 (Mat. B) = 35» значит: экзамен 50, по общему
// курсу, в расчёт идёт 35, то есть 3,5 по шкале до 10.
describe("ltScore — опубликованные примеры", () => {
  it("нет первого предмета: математика B 50, иностранный 50, литовский A 50 -> 2,7", () => {
    const score = ltScore(POLITICS, {
      mathematics: { score: 50, course: "B" },
      foreign_language: { score: 50 },
      lithuanian: { score: 50, course: "A" },
    });
    expect(score.total).toBe(2.7);
    expect(score.items[0]).toMatchObject({ position: 1, value: null, contribution: 0 });
  });

  it("математика B 50 первой, иностранный 50, литовский A 50 -> 3,40", () => {
    const score = ltScore(BUSINESS, {
      mathematics: { score: 50, course: "B" },
      foreign_language: { score: 50 },
      lithuanian: { score: 50, course: "A" },
    });
    expect(score.total).toBe(3.4);
  });

  it("политические науки: история, иностранный, география, литовский по 50 -> 5,00; математика B 40 не нужна", () => {
    const score = ltScore(POLITICS, {
      history: { score: 50 },
      foreign_language: { score: 50 },
      geography: { score: 50 },
      lithuanian: { score: 50, course: "A" },
      mathematics: { score: 40, course: "B" },
    });
    expect(score.total).toBe(5);
    expect(score.items.flatMap((item) => item.used)).not.toContain("mathematics");
  });

  it("математика B 70 первой, биология 70, иностранный 70, литовский A 70 -> 6,16", () => {
    const score = ltScore(PSYCHOLOGY, {
      mathematics: { score: 70, course: "B" },
      biology: { score: 70 },
      foreign_language: { score: 70 },
      lithuanian: { score: 70, course: "A" },
    });
    expect(score.total).toBe(6.16);
    expect(score.items[0]).toMatchObject({ used: ["mathematics"], value: 4.9, contribution: 1.96 });
  });

  it("то же с математикой A -> 7,00", () => {
    const score = ltScore(PSYCHOLOGY, {
      mathematics: { score: 70, course: "A" },
      biology: { score: 70 },
      foreign_language: { score: 70 },
      lithuanian: { score: 70, course: "A" },
    });
    expect(score.total).toBe(7);
  });
});

describe("ltScore — выбор предметов", () => {
  it("в составляющую идёт предмет, выгодный поступающему", () => {
    const score = ltScore(BUSINESS, {
      mathematics: { score: 80 },
      history: { score: 40 },
      geography: { score: 90 },
      lithuanian: { score: 60 },
    });
    // 8×0,4 + 9×0,2 + 4×0,2 + 6×0,2
    expect(score.total).toBe(7);
    // у второй и третьей составляющих вес одинаковый, поэтому важно только,
    // что использованы оба предмета, а не кто из них куда попал
    expect([...score.items[1].used, ...score.items[2].used].sort()).toEqual(["geography", "history"]);
  });

  it("один предмет не считается дважды", () => {
    const score = ltScore(BUSINESS, {
      mathematics: { score: 80 },
      geography: { score: 90 },
      lithuanian: { score: 60 },
    });
    // география подходит и второй, и третьей, но идёт только в одну
    expect(score.total).toBe(6.2);
    expect(score.items.filter((item) => item.used.includes("geography"))).toHaveLength(1);
  });

  it("предмет не из списка программы не засчитывается", () => {
    const score = ltScore(PSYCHOLOGY, { mathematics: { score: 80 }, lithuanian: { score: 60 }, chemistry: { score: 100 } });
    // химия не идёт второй (там только биология), но идёт третьей
    expect(score.items[1]).toMatchObject({ used: [], value: null });
    expect(score.items[2].used).toEqual(["chemistry"]);
    expect(score.total).toBe(6.4);
  });

  it("медицина: второе — среднее химии и математики", () => {
    const score = ltScore(MEDICINE, {
      biology: { score: 90 },
      chemistry: { score: 80 },
      mathematics: { score: 60 },
      physics: { score: 70 },
      lithuanian: { score: 50 },
    });
    // 9×0,4 + 7×0,2 + 7×0,2 + 5×0,2
    expect(score.total).toBe(7.4);
    expect(score.items[1]).toMatchObject({ used: ["chemistry", "mathematics"], value: 7 });
  });

  it("среднее не считается, если одного из двух предметов нет", () => {
    const score = ltScore(MEDICINE, { biology: { score: 90 }, chemistry: { score: 80 }, lithuanian: { score: 50 } });
    expect(score.items[1]).toMatchObject({ used: [], value: null });
    // химия при этом идёт третьей
    expect(score.total).toBe(6.2);
  });

  it("один иностранный язык: идёт четвёртым и больше нигде", () => {
    const score = ltScore(PHILOLOGY, { lithuanian: { score: 80 }, foreign_language: { score: 90 }, history: { score: 50 } });
    // 8×0,4 + 5×0,2 + 0 + 9×0,2
    expect(score.total).toBe(6);
    expect(score.items[3].used).toEqual(["foreign_language"]);
  });

  it("два иностранных языка: каждый считается один раз", () => {
    const score = ltScore(PHILOLOGY, {
      lithuanian: { score: 80 },
      foreign_language: { score: 60 },
      second_foreign_language: { score: 90 },
    });
    // 8×0,4 + 9×0,2 + 6×0,2: оба языка использованы, по разу
    expect(score.total).toBe(6.2);
    expect(score.items.flatMap((item) => item.used).sort()).toEqual(["foreign_language", "lithuanian", "second_foreign_language"]);
  });

  it("без оценок балл ноль, все четыре составляющие пусты", () => {
    const score = ltScore(POLITICS, {});
    expect(score.total).toBe(0);
    expect(score.items.map((item) => item.value)).toEqual([null, null, null, null]);
  });

  it("искусство: балл целиком — вступительный экзамен", () => {
    const arts: LtFormula = [{ position: 1, weight: 1, mode: "one_of", subjects: ["entrance_exam"] }];
    expect(ltScore(arts, { entrance_exam: { score: 85 }, lithuanian: { score: 100 } }).total).toBe(8.5);
  });
});
