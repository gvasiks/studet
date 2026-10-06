import { cache } from "react";
import { supabase } from "@/lib/supabase";
import type { LtComponent } from "@/lib/lt-score";

// Литовские формулы балла из базы. Формула записана у строки общего приёма
// (lt_admission_unit), а не у программы: строк приёма у программы может
// быть несколько (расписания, специализации). Расчёт показывается, только
// когда все строки программы идут по одной формуле и эта формула сверена
// с официальным калькулятором. Несверенную формулу анонимный ключ не
// получает вовсе — так устроена политика доступа таблицы lt_formula;
// проверка «formula есть» ниже видит её как отсутствующую.

export type LtProgrammeFormula = {
  number: string;
  admissionYear: number;
  components: LtComponent[];
  sourceUrl: string;
  checkedAt: string;
};

type UnitRow = {
  programme_id: string;
  formula_id: string;
  lt_formula: {
    number: string;
    admission_year: number;
    source_url: string;
    checked_at: string;
    lt_formula_component: { position: number; weight: number | string; mode: "one_of" | "average"; subjects: string[] }[];
  } | null;
};

export const getLtFormula = cache(async (programmeId: string): Promise<LtProgrammeFormula | null> => {
  const { data, error } = await supabase
    .from("lt_admission_unit")
    .select(
      "programme_id, formula_id, lt_formula(number, admission_year, source_url, checked_at, lt_formula_component(position, weight, mode, subjects))",
    )
    .eq("programme_id", programmeId);

  if (error) throw error;
  const rows = (data ?? []) as unknown as UnitRow[];
  if (rows.length === 0) return null;

  // Одна формула на все строки приёма, и она видна (сверена).
  const formulaIds = new Set(rows.map((row) => row.formula_id));
  const formula = rows[0].lt_formula;
  if (formulaIds.size !== 1 || !formula) return null;

  return {
    number: formula.number,
    admissionYear: formula.admission_year,
    sourceUrl: formula.source_url,
    checkedAt: formula.checked_at,
    components: [...formula.lt_formula_component]
      .sort((a, b) => a.position - b.position)
      .map((component) => ({
        position: component.position,
        weight: Number(component.weight),
        mode: component.mode,
        subjects: component.subjects,
      })),
  };
});

// PostgREST отдаёт не больше 1000 строк за запрос; строк приёма больше.
const PAGE_ROWS = 1000;

// Какие программы можно посчитать — для кнопки на карточках каталога. То же
// правило, что в getLtFormula: одна формула на программу, и она видна.
export const getLtProgrammeIdsWithFormula = cache(async (): Promise<Set<string>> => {
  const formulasByProgramme = new Map<string, Set<string>>();
  const visible = new Set<string>();

  for (let from = 0; ; from += PAGE_ROWS) {
    const { data, error } = await supabase
      .from("lt_admission_unit")
      .select("id, programme_id, formula_id, lt_formula(id)")
      .order("id")
      .range(from, from + PAGE_ROWS - 1);

    if (error) throw error;
    const rows = (data ?? []) as unknown as { programme_id: string; formula_id: string; lt_formula: { id: string } | null }[];
    for (const row of rows) {
      if (!formulasByProgramme.has(row.programme_id)) formulasByProgramme.set(row.programme_id, new Set());
      formulasByProgramme.get(row.programme_id)!.add(row.formula_id);
      if (row.lt_formula) visible.add(row.formula_id);
    }
    if (rows.length < PAGE_ROWS) break;
  }

  const result = new Set<string>();
  for (const [programmeId, formulaIds] of formulasByProgramme) {
    const [only] = formulaIds;
    if (formulaIds.size === 1 && visible.has(only)) result.add(programmeId);
  }
  return result;
});
