// «Куда можно поступить» в Эстонии — чистая логика, без обращения к базе
// (данные — ee-match-queries.ts). Пока только TalTech: правила 2027/28 по
// порогам госэкзаменов (ee_next_rule, модель thresholds, решение сената
// 24.11.2026 № 40). Тартуский университет добавится, когда выйдут его условия
// 2027 года (обещаны к концу декабря): считать по правилам лета 2026 нельзя.
//
// Что разрешено говорить (решение владельца 2026-10-25, CLAUDE.md):
//   - «порог для подачи пройден / не пройден»;
//   - «гарантирующий порог по правилу вуза пройден»;
//   - ниже гарантирующего — только факт «остальные места по рейтингу».
// Ни процентов, ни позиции, ни «скорее всего пройдёте». Твёрдое «нет» —
// только по опубликованному правилу: порог не пройден или нет широкой
// математики, которую правило требует.

import type { EeEnglishLevel, EeThresholdRule, EeThresholdSet } from "@/lib/ee-rule";

export type EeMathKind = "wide" | "narrow";
export type EeEstonianKind = "native" | "second";
/** Уровень английского по госэкзамену; "none" — ниже B1 или экзамена нет. */
export type EeEnglishInput = "none" | "B1" | EeEnglishLevel;

export type EeExams = {
  math?: { score: number; kind: EeMathKind };
  estonian?: { score: number; kind: EeEstonianKind };
  english?: EeEnglishInput;
};

export type EeMissing = "math" | "estonian" | "english";

export type EeMatchStatus =
  /** Гарантирующий порог по правилу вуза пройден. */
  | "guaranteed"
  /** Порог для подачи пройден, гарантирующий — нет: места по рейтингу. */
  | "applyPassed"
  /** Порог для подачи не пройден. */
  | "applyFailed"
  /** Приём только по порогу (без рейтинга), порог не пройден. */
  | "thresholdFailed"
  /** Правило требует широкую математику, введена узкая. */
  | "wideMathRequired"
  /** Не хватает экзаменов, чтобы сравнить. */
  | "incomplete";

export type EeMatchResult = { status: EeMatchStatus; missing: EeMissing[] };

const ENGLISH_ORDER: Record<EeEnglishInput, number> = { none: 0, B1: 1, B2: 2, C1: 3 };

function needsEnglish(rule: EeThresholdRule): boolean {
  return Boolean(rule.guarantee.english || rule.apply?.english);
}

function passes(set: EeThresholdSet, exams: Required<Pick<EeExams, "math" | "estonian">> & Pick<EeExams, "english">): boolean {
  const estonianMin = exams.estonian.kind === "second" ? set.estonianSecond : set.estonian;
  if (exams.math.score < set.math || exams.estonian.score < estonianMin) return false;
  if (set.english) return ENGLISH_ORDER[exams.english ?? "none"] >= ENGLISH_ORDER[set.english];
  return true;
}

export function eeMatch(rule: EeThresholdRule, exams: EeExams): EeMatchResult {
  const missing: EeMissing[] = [];
  if (!exams.math) missing.push("math");
  if (!exams.estonian) missing.push("estonian");
  if (needsEnglish(rule) && exams.english === undefined) missing.push("english");
  // Узкая математика у TalTech не засчитывается — это видно и без остальных
  // экзаменов, поэтому сообщается раньше, чем «не хватает».
  if (exams.math?.kind === "narrow") return { status: "wideMathRequired", missing: [] };
  if (missing.length > 0 || !exams.math || !exams.estonian) return { status: "incomplete", missing };

  const filled = { math: exams.math, estonian: exams.estonian, english: exams.english };
  if (passes(rule.guarantee, filled)) return { status: "guaranteed", missing: [] };
  if (rule.apply) return { status: passes(rule.apply, filled) ? "applyPassed" : "applyFailed", missing: [] };
  return { status: "thresholdFailed", missing: [] };
}

/** Порядок групп на странице: сначала то, что проходит. */
export const STATUS_ORDER: readonly EeMatchStatus[] = [
  "guaranteed",
  "applyPassed",
  "incomplete",
  "applyFailed",
  "thresholdFailed",
  "wideMathRequired",
];
