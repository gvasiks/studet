import { cache } from "react";
import { supabase } from "@/lib/supabase";
import { remember } from "@/lib/server-memo";
import type { ExamLevel, FormulaGate, FormulaTerm } from "@/lib/formula";

export type FormulaRecord = {
  id: string;
  variant: string;
  sourceUrl: string | null;
  verifiedAt: string | null;
  terms: FormulaTerm[];
  gates: FormulaGate[];
};

// Гейт на verified_at — на уровне самого запроса, не как правило,
// которое можно забыть соблюсти в UI. Правило 6 CLAUDE.md: формулу
// подтверждает только человек через Supabase Studio; пока этого не
// произошло, калькулятор не должен считать баллы для живых людей,
// сколько бы конвейер ни извлёк за ночь. Дублируется RLS-политикой
// самой таблицы (supabase/migrations/..._gate_unverified_formulas.sql)
// — она и есть настоящая граница: anon key публичный, и без неё
// прямой запрос к Supabase REST API в обход этого файла всё равно
// вернул бы неподтверждённые формулы. Из-за этого локального флага
// "показать неподтверждённые для разработки" здесь нет и быть не
// может — RLS его всё равно проигнорирует; проверить черновую формулу
// локально можно, только временно проставив verified_at в Studio.
//
// Один запрос: слагаемые и пороги приходят вложенными (связь по formula_id),
// а не вторым кругом к базе — карточка и калькулятор ждут на один круг
// меньше (замер 2026-10-17: карточка 230 мс, калькулятор 300 мс).
export const getFormula = cache(async (programmeId: string): Promise<FormulaRecord | null> => {
  const { data: formula, error } = await supabase
    .from("formula")
    .select(
      "id, variant, source_url, verified_at, formula_term(kind, subject, coefficient, optional), formula_gate(subject, min_percent)",
    )
    .eq("programme_id", programmeId)
    .is("valid_to", null)
    .not("verified_at", "is", null)
    .order("valid_from", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw error;
  if (!formula) return null;
  const terms = formula.formula_term;
  const gates = formula.formula_gate;

  return {
    id: formula.id,
    variant: formula.variant,
    sourceUrl: formula.source_url,
    verifiedAt: formula.verified_at,
    terms: (terms ?? []).map((term) => ({
      kind: term.kind as FormulaTerm["kind"],
      subject: term.subject,
      coefficient: Number(term.coefficient),
      optional: term.optional,
    })),
    gates: (gates ?? []).map((gate) => ({
      subject: gate.subject,
      minPercent: Number(gate.min_percent),
    })),
  };
});

// Какие программы можно посчитать — для кнопки калькулятора на карточках
// каталога. Тот же гейт, что в getFormula: только действующая (valid_to
// is null) и подтверждённая человеком формула; RLS таблицы formula
// дублирует это на стороне базы. Один запрос на весь каталог.
export const getProgrammeIdsWithFormula = cache(async (): Promise<Set<string>> => {
  const { data, error } = await supabase
    .from("formula")
    .select("programme_id")
    .is("valid_to", null)
    .not("verified_at", "is", null);

  if (error) throw error;
  return new Set((data ?? []).map((row) => row.programme_id as string));
});

// Для каждого уровня — коэффициент с самым свежим valid_from. Меняются раз
// в год (а то и реже), поэтому живут в памяти сервера пять минут, как
// данные каталога (server-memo.ts): калькулятору и /match не нужен ради них
// отдельный круг к базе. Объект общий для всех запросов — только читать.
export function getLevelCoefficients(): Promise<Record<ExamLevel, number>> {
  return remember("level-coefficients", 5 * 60 * 1000, loadLevelCoefficients);
}

const loadLevelCoefficients = cache(async (): Promise<Record<ExamLevel, number>> => {
  const { data, error } = await supabase
    .from("level_coefficient")
    .select("level, coefficient, valid_from")
    .order("valid_from", { ascending: false });

  if (error) throw error;

  const result = {} as Record<ExamLevel, number>;
  for (const row of data ?? []) {
    const level = row.level as ExamLevel;
    if (!(level in result)) {
      result[level] = Number(row.coefficient);
    }
  }
  return result;
});
