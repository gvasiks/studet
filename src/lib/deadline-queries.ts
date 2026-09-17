import { cache } from "react";
import { supabase } from "@/lib/supabase";
import type { ApplicationRound } from "@/lib/deadlines";

// Гейт на verified_at в самом запросе — тот же паттерн, что и
// getFormula() в formula-queries.ts. Дублируется RLS-политикой
// application_round_public_read (supabase/migrations/
// 20260917202425_application_rounds.sql), которая и есть настоящая
// граница: anon key публичный, без неё прямой запрос к REST API в обход
// этого файла всё равно вернул бы неподтверждённые даты.
export const getApplicationRounds = cache(async (): Promise<ApplicationRound[]> => {
  const { data, error } = await supabase
    .from("application_round")
    .select("university_id, degree_level, language_of_instruction, label, opens_on, closes_on, note, source_url")
    .not("verified_at", "is", null);

  if (error) throw error;

  return (data ?? []).map((row) => ({
    universityId: row.university_id,
    degreeLevel: row.degree_level,
    languageOfInstruction: row.language_of_instruction,
    label: row.label,
    opensOn: row.opens_on,
    closesOn: row.closes_on,
    note: row.note,
    sourceUrl: row.source_url,
  }));
});
