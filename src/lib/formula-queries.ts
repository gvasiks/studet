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

// Действующая формула — с наибольшим valid_from среди тех, что ещё не
// закрыты (valid_to пуст). История прошлых лет остаётся в базе, но сюда
// не попадает — калькулятор всегда считает по актуальным коэффициентам.
export const getFormula = cache(async (programmeId: string): Promise<FormulaRecord | null> => {
  const { data: formula, error } = await supabase
    .from("formula")
    .select("id, variant, source_url, verified_at")
    .eq("programme_id", programmeId)
    .is("valid_to", null)
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
