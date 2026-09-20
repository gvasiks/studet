import { cache } from "react";
import type { Locale } from "@/i18n/config";
import { supabase } from "@/lib/supabase";
import { localizedName } from "@/lib/names";
import { getLevelCoefficients } from "@/lib/formula-queries";
import type { ExamLevel, FormulaGate, FormulaTerm } from "@/lib/formula";
import { FIXTURE_FORMULAS, FIXTURE_LEVEL_COEFFICIENTS } from "@/lib/match-fixture";
import type { MatchFormula } from "@/lib/match";

export type MatchData = {
  formulas: MatchFormula[];
  levelCoefficients: Record<ExamLevel, number>;
  // true — показаны выдуманные данные из match-fixture.ts (только `next dev`)
  isFixture: boolean;
};

// Выдуманные формулы — только локально: `next dev` с MATCH_FIXTURE=1.
// Условие по NODE_ENV намеренно жёсткое: в `next build` / `next start` его не
// обойти переменной окружения, иначе одна лишняя строка в настройках хостинга
// показала бы живым людям несуществующие программы с несуществующими
// коэффициентами.
function fixtureEnabled(): boolean {
  return process.env.NODE_ENV === "development" && process.env.MATCH_FIXTURE === "1";
}

// Только подтверждённые формулы: их отдаёт сама RLS-политика таблицы formula
// (анонимный ключ неподтверждённых не видит), .not("verified_at", ...) ниже
// — не защита, а пояснение того же условия. Программы, пропавшие с сайта
// вуза (missed_runs >= 2), скрыты политикой таблицы programme. Только
// вариант "ce": варианты для льготников и иностранцев — отдельная задача.
export const getMatchData = cache(async (locale: Locale): Promise<MatchData> => {
  if (fixtureEnabled()) {
    return { formulas: FIXTURE_FORMULAS, levelCoefficients: FIXTURE_LEVEL_COEFFICIENTS, isFixture: true };
  }

  const { data: rows, error } = await supabase
    .from("formula")
    .select(
      "id, programme_id, valid_from, source_url, verified_at, programme!inner(slug, name_lv, name_en, university!inner(slug, name_lv, name_en))",
    )
    .eq("variant", "ce")
    .is("valid_to", null)
    .not("verified_at", "is", null)
    .order("valid_from", { ascending: false });

  if (error) throw error;
  if (!rows || rows.length === 0) {
    return { formulas: [], levelCoefficients: await getLevelCoefficients(), isFixture: false };
  }

  // На программу — самая свежая формула (rows уже по убыванию valid_from)
  const latestByProgramme = new Map<string, (typeof rows)[number]>();
  for (const row of rows) if (!latestByProgramme.has(row.programme_id)) latestByProgramme.set(row.programme_id, row);
  const chosen = [...latestByProgramme.values()];
  const ids = chosen.map((row) => row.id);

  const [termsResult, gatesResult, levelCoefficients] = await Promise.all([
    supabase.from("formula_term").select("formula_id, kind, subject, coefficient").in("formula_id", ids),
    supabase.from("formula_gate").select("formula_id, subject, min_percent").in("formula_id", ids),
    getLevelCoefficients(),
  ]);
  if (termsResult.error) throw termsResult.error;
  if (gatesResult.error) throw gatesResult.error;

  const termsByFormula = new Map<string, FormulaTerm[]>();
  for (const term of termsResult.data ?? []) {
    const list = termsByFormula.get(term.formula_id) ?? [];
    list.push({ kind: term.kind as FormulaTerm["kind"], subject: term.subject, coefficient: Number(term.coefficient) });
    termsByFormula.set(term.formula_id, list);
  }
  const gatesByFormula = new Map<string, FormulaGate[]>();
  for (const gate of gatesResult.data ?? []) {
    const list = gatesByFormula.get(gate.formula_id) ?? [];
    list.push({ subject: gate.subject, minPercent: Number(gate.min_percent) });
    gatesByFormula.set(gate.formula_id, list);
  }

  const formulas: MatchFormula[] = chosen.map((row) => {
    const programme = row.programme as unknown as {
      slug: string;
      name_lv: string | null;
      name_en: string | null;
      university: { slug: string; name_lv: string; name_en: string | null };
    };
    return {
      formulaId: row.id,
      programmeSlug: programme.slug,
      programmeName: localizedName(programme, locale),
      universitySlug: programme.university.slug,
      universityName: localizedName(programme.university, locale),
      verifiedAt: row.verified_at as string,
      sourceUrl: row.source_url,
      terms: termsByFormula.get(row.id) ?? [],
      gates: gatesByFormula.get(row.id) ?? [],
    };
  });

  return { formulas, levelCoefficients, isFixture: false };
});
