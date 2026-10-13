import { cache } from "react";
import { supabase } from "@/lib/supabase";
import type { EeAdmission } from "@/lib/ee-admission";

// Последний конкурс эстонской программы (таблица ee_admission, её пишет
// pipeline/src/ee_load_admissions.py из данных государственного портала).
// Действующий он или прошлый, решает ee-admission.ts по сроку.

export const getEeAdmission = cache(async (programmeId: string): Promise<EeAdmission | null> => {
  const { data, error } = await supabase
    .from("ee_admission")
    .select("sais_url, opens_at, closes_at, source_url, extracted_at")
    .eq("programme_id", programmeId)
    .maybeSingle();

  if (error) throw error;
  if (!data) return null;
  return {
    saisUrl: data.sais_url,
    opensAt: data.opens_at,
    closesAt: data.closes_at,
    sourceUrl: data.source_url,
    extractedAt: data.extracted_at,
  };
});
