// Подписи предметов и слагаемых формулы — общие для калькулятора программы и
// обратного поиска (раньше жили внутри CalculatorForm.tsx).
import type { Dictionary } from "@/i18n/dictionaries";
import type { FormulaTerm } from "@/lib/formula";

export function subjectLabel(dict: Dictionary, subject: string): string {
  const known = dict.survey.exams.subjects as Record<string, string>;
  return known[subject] ?? subject;
}

export function termLabel(dict: Dictionary, term: FormulaTerm): string {
  if (term.kind === "ce" && term.subject) return subjectLabel(dict, term.subject);
  const known = dict.calculator.termKinds as Record<string, string>;
  // Именованное испытание (RTU Rīgas Biznesa skola: несколько разных
  // entrance_exam в одной формуле) — своя метка по составному ключу;
  // безымянное (Вентспилс) — просто по виду термина.
  if (term.subject) return known[`${term.kind}_${term.subject}`] ?? term.subject;
  return known[term.kind] ?? term.kind;
}
