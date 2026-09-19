import { cache } from "react";
import { supabase } from "@/lib/supabase";
import type { OutcomeRow } from "@/lib/outcomes";

export type ProgrammeOutcome = {
  fieldCode: string;
  rows: OutcomeRow[];
};

// Гейт — на подтверждённом направлении, а не на самих данных о
// выпускниках: сами цифры — официальная открытая статистика (ИЗМ/ЦСУ),
// а вот привязка "эта программа = эта группа программ" — наша
// черновая разметка по названию (pipeline/src/seed_programme_fields.py).
// Неверно подобранная группа подставила бы программе чужие зарплаты, и
// человек, выбирающий будущее, увидел бы их как факт — поэтому пока
// programme_field.verified_at пуст, блок не показывается вовсе.
// Проверка здесь, в приложении, а не в RLS: сам код направления
// безобиден и открыт для фильтра в анкете (пункт 16), вредно только
// показывать под ним доходы.
export const getProgrammeOutcome = cache(
  async (programmeId: string, universityId: string): Promise<ProgrammeOutcome | null> => {
    const { data: field, error } = await supabase
      .from("programme_field")
      .select("field_code")
      .eq("programme_id", programmeId)
      .not("verified_at", "is", null)
      .maybeSingle();

    if (error) throw error;
    if (!field) return null;

    const { data, error: outcomeError } = await supabase
      .from("graduate_outcome")
      .select("graduation_year, tax_year, level_code, graduates, employed, median_income_eur")
      .eq("university_id", universityId)
      .eq("programme_group", field.field_code);

    if (outcomeError) throw outcomeError;

    return {
      fieldCode: field.field_code,
      rows: (data ?? []).map((row) => ({
        graduationYear: row.graduation_year,
        taxYear: row.tax_year,
        levelCode: row.level_code,
        graduates: row.graduates,
        employed: row.employed,
        medianIncomeEur: row.median_income_eur === null ? null : Number(row.median_income_eur),
      })),
    };
  },
);
