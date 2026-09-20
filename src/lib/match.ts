// Обратный поиск (позиция 07): человек вводит результаты экзаменов — видит,
// по каким программам ему уже можно посчитать конкурсный балл, а по каким
// чего-то не хватает.
//
// Чистая логика без обращений к базе (тот же приём, что formula.ts /
// formula-queries.ts) — чтобы тестировать без клиента Supabase и считать
// в браузере: результаты экзаменов несовершеннолетних на сервер не уходят
// (правило "без регистрации и без сохранения" из CLAUDE.md).
//
// Чего эта функция НЕ делает намеренно:
// - не сортирует по баллу и не говорит "проходишь / не проходишь": шкалы у
//   вузов разные (ЛУ — 1000, Вентспилс — около 100), балл несравним между
//   вузами, а проходных баллов нет (правило 2 и раздел "Чего в проекте нет");
// - не отбрасывает программы по формальным требованиям кроме порогов
//   formula_gate: требований к экзаменам (programme_requirement) в базе нет,
//   известны только предметы из самой формулы;
// - не угадывает недостающие данные: без слагаемого "вступительное
//   испытание" или "оценка аттестата" балл не считается вовсе.
import {
  calculateScore,
  type ExamLevel,
  type ExamResult,
  type FormulaGate,
  type FormulaTerm,
  type ScoreResult,
} from "./formula";

export type MatchFormula = {
  formulaId: string;
  programmeSlug: string;
  programmeName: string;
  universitySlug: string;
  universityName: string;
  verifiedAt: string;
  sourceUrl: string | null;
  terms: FormulaTerm[];
  gates: FormulaGate[];
};

export type MatchStatus = "computed" | "missing_exams" | "missing_extras" | "gate_failed";

export type MatchItem = {
  formula: MatchFormula;
  status: MatchStatus;
  // Только у computed и gate_failed: у missing_* балла нет, чтобы не
  // показывать частичное число, которое читается как настоящее.
  score: ScoreResult | null;
  missingSubjects: string[];
  // Слагаемые, для которых нужен ввод, которого в этой форме нет
  // (вступительное испытание, оценка аттестата): считать такие программы
  // надо в калькуляторе самой программы.
  missingExtras: FormulaTerm[];
  failedGates: FormulaGate[];
};

export type MatchGroups = Record<MatchStatus, MatchItem[]>;

function requiredSubjects(formula: MatchFormula): string[] {
  const subjects = new Set<string>();
  for (const term of formula.terms) {
    if (term.kind === "ce" && term.subject) subjects.add(term.subject);
  }
  for (const gate of formula.gates) subjects.add(gate.subject);
  return [...subjects];
}

export function matchFormula(
  formula: MatchFormula,
  exams: ExamResult[],
  levelCoefficients: Record<ExamLevel, number>,
): MatchItem {
  const taken = new Set(exams.map((exam) => exam.subject));
  const missingSubjects = requiredSubjects(formula).filter((subject) => !taken.has(subject));
  // "ce_average" считается по СДАННЫМ экзаменам, поэтому без единого
  // экзамена посчитать нельзя
  const needsAnyExam = formula.terms.some((term) => term.kind === "ce_average") && exams.length === 0;
  const missingExtras = formula.terms.filter((term) => term.kind === "certificate" || term.kind === "entrance_exam");

  const base = { formula, missingSubjects, missingExtras: [] as FormulaTerm[], failedGates: [] as FormulaGate[] };

  if (missingSubjects.length > 0 || needsAnyExam) {
    return { ...base, status: "missing_exams", score: null };
  }
  if (missingExtras.length > 0) {
    return { ...base, status: "missing_extras", score: null, missingExtras };
  }

  const score = calculateScore(formula.terms, formula.gates, exams, levelCoefficients);
  if (score.failedGates.length > 0) {
    return { ...base, status: "gate_failed", score, failedGates: score.failedGates };
  }
  return { ...base, status: "computed", score };
}

// Внутри группы — по вузу, затем по названию программы. НЕ по баллу: см.
// комментарий вверху файла.
function byUniversityThenProgramme(a: MatchItem, b: MatchItem): number {
  return (
    a.formula.universityName.localeCompare(b.formula.universityName) ||
    a.formula.programmeName.localeCompare(b.formula.programmeName)
  );
}

export function matchProgrammes(
  formulas: MatchFormula[],
  exams: ExamResult[],
  levelCoefficients: Record<ExamLevel, number>,
): MatchGroups {
  const groups: MatchGroups = { computed: [], missing_exams: [], missing_extras: [], gate_failed: [] };
  for (const formula of formulas) {
    const item = matchFormula(formula, exams, levelCoefficients);
    groups[item.status].push(item);
  }
  for (const status of Object.keys(groups) as MatchStatus[]) groups[status].sort(byUniversityThenProgramme);
  return groups;
}
