import { cache } from "react";
import { supabase } from "@/lib/supabase";
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
export const getFormula = cache(async (programmeId: string): Promise<FormulaRecord | null> => {
  const { data: formula, error } = await supabase
    .from("formula")
    .select("id, variant, source_url, verified_at")
    .eq("programme_id", programmeId)
    .is("valid_to", null)
    .not("verified_at", "is", null)
    .order("valid_from", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw error;
  if (!formula) return null;

  const [{ data: terms, error: termsError }, { data: gates, error: gatesError }] = await Promise.all([
    supabase.from("formula_term").select("kind, subject, coefficient").eq("formula_id", formula.id),
    supabase.from("formula_gate").select("subject, min_percent").eq("formula_id", formula.id),
  ]);

  if (termsError) throw termsError;
  if (gatesError) throw gatesError;

  return {
    id: formula.id,
    variant: formula.variant,
    sourceUrl: formula.source_url,
    verifiedAt: formula.verified_at,
    terms: (terms ?? []).map((term) => ({
      kind: term.kind as FormulaTerm["kind"],
      subject: term.subject,
      coefficient: Number(term.coefficient),
    })),
    gates: (gates ?? []).map((gate) => ({
      subject: gate.subject,
      minPercent: Number(gate.min_percent),
    })),
  };
});

// Для каждого уровня — коэффициент с самым свежим valid_from.
export const getLevelCoefficients = cache(async (): Promise<Record<ExamLevel, number>> => {
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
