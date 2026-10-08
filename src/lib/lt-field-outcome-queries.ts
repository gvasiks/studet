import { cache } from "react";
import { supabase } from "@/lib/supabase";

// Что стало с выпускниками литовского направления (таблица
// lt_field_outcome, её пишет pipeline/src/lt_load_field_outcomes.py).
// Показатели — по направлению и ступени по всей стране: источник не делит
// их ни по вузам, ни по программам, и на карточке об этом сказано.

export type LtFieldOutcome = {
  fieldName: string;
  cohortFrom: number;
  cohortTo: number;
  employedPercent: number;
  qualifiedPercent: number;
  incomePercent: number;
  levelAverageIncomeEur: number;
  sourceUrl: string;
  publishedOn: string;
};

/** Самые свежие показатели направления на этой ступени; null — в источнике их нет. */
export const getLtFieldOutcome = cache(async (degreeLevel: string, fieldCode: string): Promise<LtFieldOutcome | null> => {
  const { data, error } = await supabase
    .from("lt_field_outcome")
    .select(
      "field_name, cohort_from, cohort_to, employed_percent, qualified_percent, income_percent, level_average_income_eur, source_url, published_on",
    )
    .eq("degree_level", degreeLevel)
    .eq("field_code", fieldCode)
    .order("cohort_to", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw error;
  if (!data) return null;
  return {
    fieldName: data.field_name,
    cohortFrom: data.cohort_from,
    cohortTo: data.cohort_to,
    // numeric приходит из PostgREST строкой или числом — приводим к числу
    employedPercent: Number(data.employed_percent),
    qualifiedPercent: Number(data.qualified_percent),
    incomePercent: Number(data.income_percent),
    levelAverageIncomeEur: data.level_average_income_eur,
    sourceUrl: data.source_url,
    publishedOn: data.published_on,
  };
});
