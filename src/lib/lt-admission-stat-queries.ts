import { cache } from "react";
import { supabase } from "@/lib/supabase";
import { latestAdmissionYear, type LtAdmissionStat, type LtAdmissionYear } from "@/lib/lt-admission-stats";

// Цифры прошлого приёма программы из базы (lt_admission_stat). В таблице
// только суммы из открытого набора LAMA BPO; программа, которая с набором не
// сошлась, строк не имеет — блок на карточке тогда не показывается.
export const getLtAdmissionYear = cache(async (programmeId: string): Promise<LtAdmissionYear | null> => {
  const { data, error } = await supabase
    .from("lt_admission_stat")
    .select("admission_year, funding, applications, first_priority, invited, signed, source_url, extracted_at")
    .eq("programme_id", programmeId);

  if (error) throw error;
  const stats: LtAdmissionStat[] = (data ?? []).map((row) => ({
    admissionYear: row.admission_year,
    funding: row.funding,
    applications: row.applications,
    firstPriority: row.first_priority,
    invited: row.invited,
    signed: row.signed,
    sourceUrl: row.source_url,
    extractedAt: row.extracted_at,
  }));
  return latestAdmissionYear(stats);
});
