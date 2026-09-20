import { describe, expect, it } from "vitest";
import { calculateScore, extraKey, type ExamResult, type FormulaTerm } from "./formula";

// Ревью 2026-09, пункт 02: "ежегодная сверка коэффициентов идёт без
// страховки — поехавшую цифру заметят пользователи, а не тест". У РТУ
// и Вентспилса, в отличие от ЛУ, не нашлось опубликованного вузом
// числового примера (только формулы-коэффициенты, без разбора
// "вход → результат") — проверено вручную на обеих страницах перед
// тем, как писать эти тесты, а не принято на слово из отчёта.
//
// Вместо этого — прямая регрессия на сами коэффициенты, которые
// pipeline/src/seed_formulas.py кладёт в базу: по одному кейсу на
// КАЖДЫЙ различающийся набор коэффициентов среди всех 35 засеянных
// формул (программы с одинаковым набором — как datorzinatnes-bakalaurs
// и biznesa-vadiba-bakalaurs у Вентспилса — по построению посчитают
// одинаково, поэтому достаточно проверить один раз на группу).
// "Ekonomika" ЛУ сюда не входит — она уже покрыта formula.test.ts как
// единственный настоящий опубликованный вузом пример.
//
// Вход везде один и тот же: 100% на каждый CE-предмет формулы на
// augstākā līmenī (коэффициент уровня 1,0) и 100 на каждое именованное
// entrance_exam/certificate слагаемое. При таком вводе среднее по всем
// CE тоже равно 100, и итог — просто (сумма коэффициентов формулы) × 100:
// сверить ожидаемое число можно глазами по самим коэффициентам, без
// калькулятора. Так и держим протокол этого файла: если через год
// seed_formulas.py поправят, а этот файл — забудут, тест покраснеет.
const LEVEL_COEFFICIENTS = { augstakais: 1.0, optimalais: 0.75, vispaarigais: 0.5 };

function scoreAllTermsAt100(terms: FormulaTerm[]) {
  const ceSubjects = terms.filter((t) => t.kind === "ce" && t.subject).map((t) => t.subject as string);
  const examResults: ExamResult[] = ceSubjects.map((subject) => ({ subject, percent: 100, level: "augstakais" }));

  const extraTerms = terms.filter((t) => t.kind === "certificate" || t.kind === "entrance_exam");
  const extras = Object.fromEntries(extraTerms.map((term) => [extraKey(term), 100]));

  return calculateScore(terms, [], examResults, LEVEL_COEFFICIENTS, extras).total;
}

type Case = { label: string; terms: FormulaTerm[]; expectedTotal: number };

const cases: Case[] = [
  {
    // Ventspils: programmesanas-specialists, datorzinatnes-bakalaurs, biznesa-vadiba-bakalaurs
    label: "Ventspils — math0.6/en0.2/lv0.1/avg0.1 (3 программы)",
    terms: [
      { kind: "ce", subject: "mathematics", coefficient: 0.6 },
      { kind: "ce", subject: "english", coefficient: 0.2 },
      { kind: "ce", subject: "latvian", coefficient: 0.1 },
      { kind: "ce_average", subject: null, coefficient: 0.1 },
    ],
    expectedTotal: 100, // (0.6+0.2+0.1+0.1) × 100
  },
  {
    label: "Ventspils — jaunuznemumu-vadiba (entrance_exam безымянный)",
    terms: [
      { kind: "ce", subject: "mathematics", coefficient: 0.15 },
      { kind: "ce", subject: "english", coefficient: 0.15 },
      { kind: "entrance_exam", subject: null, coefficient: 0.6 },
      { kind: "ce_average", subject: null, coefficient: 0.1 },
    ],
    expectedTotal: 100,
  },
  {
    // Ventspils: vadibzinatne-lv-distance, vadibzinatne-en-full_time
    label: "Ventspils — math0.4/en0.4/lv0.1/avg0.1 (2 программы)",
    terms: [
      { kind: "ce", subject: "mathematics", coefficient: 0.4 },
      { kind: "ce", subject: "english", coefficient: 0.4 },
      { kind: "ce", subject: "latvian", coefficient: 0.1 },
      { kind: "ce_average", subject: null, coefficient: 0.1 },
    ],
    expectedTotal: 100,
  },
  {
    // Ventspils: elektronika-bakalaurs. Физика — необязательное слагаемое
    // (optional в базе): при 100% по физике итог 110, без неё был бы 100.
    label: "Ventspils — elektronika-bakalaurs (CE физика сверху)",
    terms: [
      { kind: "ce", subject: "mathematics", coefficient: 0.6 },
      { kind: "ce", subject: "english", coefficient: 0.2 },
      { kind: "ce", subject: "latvian", coefficient: 0.1 },
      { kind: "ce", subject: "physics", coefficient: 0.1, optional: true },
      { kind: "ce_average", subject: null, coefficient: 0.1 },
    ],
    expectedTotal: 110,
  },
  {
    label: "Ventspils — valodas-sazina-un-kulturvide",
    terms: [
      { kind: "ce", subject: "english", coefficient: 0.4 },
      { kind: "ce", subject: "latvian", coefficient: 0.4 },
      { kind: "ce", subject: "mathematics", coefficient: 0.1 },
      { kind: "ce_average", subject: null, coefficient: 0.1 },
    ],
    expectedTotal: 100,
  },
  {
    // LU: business-administration-lv, e-business-management, financial-management,
    // accounting-analysis-and-audit, occupational-health-and-safety-at-work
    // (economics — тот же набор, но покрыт отдельно в formula.test.ts)
    label: "LU — lv1.5/en1/math6.5/avg1 (5 программ + economics)",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 1.5 },
      { kind: "ce", subject: "english", coefficient: 1.0 },
      { kind: "ce", subject: "mathematics", coefficient: 6.5 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
    ],
    expectedTotal: 1000,
  },
  {
    // LU: business-administration-en, international-economics-and-commercial-diplomacy-en
    label: "LU — lv1/en3.5/math4.5/avg1 (2 программы)",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 1.0 },
      { kind: "ce", subject: "english", coefficient: 3.5 },
      { kind: "ce", subject: "mathematics", coefficient: 4.5 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
    ],
    expectedTotal: 1000,
  },
  {
    // LU: information-management, communication-science, cultural-and-social-anthropology,
    // political-science, social-work-in-riga-and-ul-branches, sociology
    label: "LU — lv3.5/en3.5/math2/avg1/socialstudies1 (6 программ)",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 3.5 },
      { kind: "ce", subject: "english", coefficient: 3.5 },
      { kind: "ce", subject: "mathematics", coefficient: 2.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
      { kind: "ce", subject: "socialstudies", coefficient: 1.0 },
    ],
    expectedTotal: 1100,
  },
  {
    label: "LU — cultural-and-social-anthropology-en",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 1.0 },
      { kind: "ce", subject: "english", coefficient: 6.0 },
      { kind: "ce", subject: "mathematics", coefficient: 2.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
      { kind: "ce", subject: "socialstudies", coefficient: 1.0 },
    ],
    expectedTotal: 1100,
  },
  {
    label: "LU — international-economics-and-commercial-diplomacy-lv",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 2.5 },
      { kind: "ce", subject: "english", coefficient: 2.5 },
      { kind: "ce", subject: "mathematics", coefficient: 4.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
    ],
    expectedTotal: 1000,
  },
  {
    label: "LU — english-european-languages-and-business-studies",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 2.0 },
      { kind: "ce", subject: "english", coefficient: 4.5 },
      { kind: "ce", subject: "mathematics", coefficient: 2.5 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
    ],
    expectedTotal: 1000,
  },
  {
    label: "LU — philosophy",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 3.0 },
      { kind: "ce", subject: "english", coefficient: 5.0 },
      { kind: "ce", subject: "mathematics", coefficient: 1.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
    ],
    expectedTotal: 1000,
  },
  {
    label: "LU — latvian-studies",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 6.0 },
      { kind: "ce", subject: "english", coefficient: 2.0 },
      { kind: "ce", subject: "mathematics", coefficient: 1.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
    ],
    expectedTotal: 1000,
  },
  {
    label: "LU — history-and-archeology",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 3.5 },
      { kind: "ce", subject: "english", coefficient: 3.5 },
      { kind: "ce", subject: "mathematics", coefficient: 2.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
      { kind: "ce", subject: "history", coefficient: 1.0 },
    ],
    expectedTotal: 1100,
  },
  {
    label: "LU — asian-and-intercultural-studies",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 2.0 },
      { kind: "ce", subject: "english", coefficient: 6.0 },
      { kind: "ce", subject: "mathematics", coefficient: 1.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
    ],
    expectedTotal: 1000,
  },
  {
    label: "LU — art-1 (entrance_exam с меткой art_test)",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 2.5 },
      { kind: "ce", subject: "english", coefficient: 1.5 },
      { kind: "ce", subject: "mathematics", coefficient: 1.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
      { kind: "entrance_exam", subject: "art_test", coefficient: 0.4 },
    ],
    expectedTotal: 640,
  },
  {
    label: "LU — psychology-1",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 2.5 },
      { kind: "ce", subject: "english", coefficient: 4.0 },
      { kind: "ce", subject: "mathematics", coefficient: 2.5 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
    ],
    expectedTotal: 1000,
  },
  {
    label: "LU — primary-education-teacher (entrance_exam с меткой interview)",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 2.0 },
      { kind: "ce", subject: "english", coefficient: 1.0 },
      { kind: "ce", subject: "mathematics", coefficient: 1.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
      { kind: "entrance_exam", subject: "interview", coefficient: 5.0 },
    ],
    expectedTotal: 1000,
  },
  {
    label: "LU — sports-technology-and-public-health",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 4.0 },
      { kind: "ce", subject: "english", coefficient: 4.0 },
      { kind: "ce", subject: "mathematics", coefficient: 1.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
    ],
    expectedTotal: 1000,
  },
  {
    label: "LU — biology (выделенный предмет biology помимо lv/en/math)",
    terms: [
      { kind: "ce", subject: "latvian", coefficient: 1.5 },
      { kind: "ce", subject: "english", coefficient: 1.0 },
      { kind: "ce", subject: "mathematics", coefficient: 2.5 },
      { kind: "ce", subject: "biology", coefficient: 4.0 },
      { kind: "ce_average", subject: null, coefficient: 1.0 },
    ],
    expectedTotal: 1000,
  },
  {
    // RTU Rīgas Biznesa skola: ibx-02c60, dbt-02c60 — три именованных
    // entrance_exam в одной формуле (english_test/interview/math_test)
    label: "RTU RBS — три именованных entrance_exam (2 программы)",
    terms: [
      { kind: "ce", subject: "mathematics", coefficient: 0.25 },
      { kind: "ce", subject: "latvian", coefficient: 0.25 },
      { kind: "ce", subject: "english", coefficient: 1.0 },
      { kind: "entrance_exam", subject: "english_test", coefficient: 0.25 },
      { kind: "entrance_exam", subject: "interview", coefficient: 0.25 },
      { kind: "entrance_exam", subject: "math_test", coefficient: 0.25 },
      { kind: "ce_average", subject: null, coefficient: 0.5 },
    ],
    expectedTotal: 275,
  },
];

describe("calculateScore — регрессия по всем засеянным формулам (pipeline/src/seed_formulas.py)", () => {
  it.each(cases)("$label → $expectedTotal", ({ terms, expectedTotal }) => {
    expect(scoreAllTermsAt100(terms)).toBeCloseTo(expectedTotal, 2);
  });
});
