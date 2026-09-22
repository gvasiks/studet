// ВЫДУМАННЫЕ данные для локальной проверки обратного поиска, пока в базе нет
// ни одной подтверждённой формулы (они подтверждаются в декабре, после
// правил 2027/28 — docs/WORKPLAN.md).
//
// Подключается ТОЛЬКО при `next dev` и MATCH_FIXTURE=1 (см. match-queries.ts):
// в сборке для публики (`next build` / `next start`) условие по NODE_ENV
// никогда не выполняется. Причина осторожности: выдуманная формула с
// выдуманными коэффициентами, показанная живому человеку, — ровно то, чего
// правила проекта не допускают (правило 6 CLAUDE.md). Вручную выставлять
// verified_at в настоящей базе ради проверки нельзя по той же причине.
//
// Названия помечены "[TEST]", чтобы их не спутать с настоящими программами.
import type { ExamLevel } from "./formula";
import type { MatchFormula, MatchRequirement } from "./match";

export const FIXTURE_LEVEL_COEFFICIENTS: Record<ExamLevel, number> = {
  augstakais: 1,
  optimalais: 0.75,
  vispaarigais: 0.5,
};

const VERIFIED = "2026-12-10T10:00:00Z";

function fixture(
  university: string,
  programme: string,
  terms: MatchFormula["terms"],
  gates: MatchFormula["gates"] = [],
): MatchFormula {
  return {
    formulaId: `fixture-${university}-${programme}`,
    programmeSlug: "fixture",
    programmeName: `[TEST] ${programme}`,
    universitySlug: "fixture",
    universityName: `[TEST] ${university}`,
    verifiedAt: VERIFIED,
    sourceUrl: null,
    terms,
    gates,
  };
}

export const FIXTURE_FORMULAS: MatchFormula[] = [
  fixture("Universitāte A", "Economics", [
    { kind: "ce", subject: "mathematics", coefficient: 0.5 },
    { kind: "ce", subject: "english", coefficient: 0.3 },
    { kind: "ce_average", subject: null, coefficient: 0.2 },
  ]),
  fixture("Universitāte A", "Computer Science", [
    { kind: "ce", subject: "mathematics", coefficient: 0.6 },
    { kind: "ce", subject: "physics", coefficient: 0.4 },
  ]),
  fixture("Universitāte A", "Design", [
    { kind: "ce", subject: "english", coefficient: 0.5 },
    { kind: "entrance_exam", subject: "art_test", coefficient: 0.5 },
  ]),
  fixture("Universitāte B", "Chemistry", [
    { kind: "ce", subject: "chemistry", coefficient: 0.7 },
    { kind: "ce", subject: "mathematics", coefficient: 0.3 },
  ]),
  fixture("Universitāte B", "Law", [{ kind: "ce", subject: "history", coefficient: 1 }], [
    { subject: "latvian", minPercent: 30 },
  ]),
  fixture(
    "Universitāte B",
    "Medicine",
    [
      { kind: "ce", subject: "biology", coefficient: 0.5 },
      { kind: "ce", subject: "chemistry", coefficient: 0.5 },
    ],
    [{ subject: "english", minPercent: 70 }],
  ),
  fixture("Universitāte B", "Management", [
    { kind: "ce", subject: "mathematics", coefficient: 0.4 },
    { kind: "ce", subject: "latvian", coefficient: 0.3 },
    { kind: "ce", subject: "english", coefficient: 0.3 },
  ]),
];

// Программы БЕЗ формулы, но с подтверждёнными требованиями (план
// 2026-09-21, пункт 02) — для проверки второй, более бедной ветки
// обратного поиска отдельно от формул.
function requirementFixture(
  university: string,
  programme: string,
  subjectGroups: string[][],
): MatchRequirement {
  return {
    requirementId: `fixture-req-${university}-${programme}`,
    programmeSlug: "fixture",
    programmeName: `[TEST] ${programme}`,
    universitySlug: "fixture",
    universityName: `[TEST] ${university}`,
    verifiedAt: VERIFIED,
    sourceUrl: null,
    subjectGroups,
  };
}

export const FIXTURE_REQUIREMENTS: MatchRequirement[] = [
  requirementFixture("Universitāte C", "Sociology", [["mathematics"], ["english"]]),
  // альтернатива — LU "CE fizikā vai CE ķīmijā, vai CE bioloģijā"
  requirementFixture("Universitāte C", "Nursing", [["mathematics"], ["physics", "chemistry", "biology"]]),
];
