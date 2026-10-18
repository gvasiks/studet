import { cache } from "react";
import { supabase } from "@/lib/supabase";
import { remember } from "@/lib/server-memo";
import { latestVuppYear, type VuppStat, type VuppYear } from "@/lib/vupp-stats";

// Прошлогодний конкурс латвийской программы из базы. Связь программы с
// кодом приёма портала (programme_vupp_link) посетителю видна, только если
// её подтвердил владелец (RLS); программа без связи блока не получает.

type ProgrammeCodes = { university: string; codes: string[] };

// Связей немного (127 на 2026-10-18) и меняются они раз в год — живут в
// памяти сервера пять минут, как остальной каталог (server-memo.ts).
// Значение общее для всех запросов: не менять.
function getLinks(): Promise<Map<string, ProgrammeCodes>> {
  return remember("vupp-links", 5 * 60 * 1000, loadLinks);
}

async function loadLinks(): Promise<Map<string, ProgrammeCodes>> {
  const { data, error } = await supabase
    .from("programme_vupp_link")
    .select("programme_id, university_slug, programme_code")
    .not("verified_at", "is", null)
    .order("id")
    // база отдаёт не больше 1000 строк за запрос; связей на порядок меньше
    .range(0, 999);
  if (error) throw error;
  const links = new Map<string, ProgrammeCodes>();
  for (const row of data ?? []) {
    const entry: ProgrammeCodes = links.get(row.programme_id) ?? { university: row.university_slug, codes: [] };
    entry.codes.push(row.programme_code);
    links.set(row.programme_id, entry);
  }
  return links;
}

/** Год последнего приёма на портале для программ со связью: для ссылки
 * «цифры приёма — на странице программы» в /match. Программы без связи
 * в ответ не попадают. */
export async function getVuppYears(programmeIds: string[]): Promise<Map<string, number>> {
  const links = await getLinks();
  const linked = programmeIds.filter((id) => links.has(id));
  const years = new Map<string, number>();
  if (linked.length === 0) return years;
  const codes = [...new Set(linked.flatMap((id) => links.get(id)!.codes))];
  const { data, error } = await supabase
    .from("vupp_admission_stat")
    .select("university_slug, programme_code, admission_year")
    .in("programme_code", codes);
  if (error) throw error;
  for (const id of linked) {
    const link = links.get(id)!;
    for (const row of data ?? []) {
      if (row.university_slug !== link.university || !link.codes.includes(row.programme_code)) continue;
      years.set(id, Math.max(years.get(id) ?? 0, row.admission_year));
    }
  }
  return years;
}

export const getVuppYear = cache(async (programmeId: string): Promise<VuppYear | null> => {
  const link = (await getLinks()).get(programmeId);
  if (!link) return null;
  const { data, error } = await supabase
    .from("vupp_admission_stat")
    .select(
      "admission_year, programme_code, programme_name, study_mode, funding, city, places, places_unlimited, applications, first_priority, passed, stage, portal_updated_on, source_url, extracted_at",
    )
    .eq("university_slug", link.university)
    .in("programme_code", link.codes);
  if (error) throw error;
  const stats: VuppStat[] = (data ?? []).map((row) => ({
    admissionYear: row.admission_year,
    programmeCode: row.programme_code,
    programmeName: row.programme_name,
    studyMode: row.study_mode,
    funding: row.funding,
    city: row.city,
    places: row.places,
    placesUnlimited: row.places_unlimited,
    applications: row.applications,
    firstPriority: row.first_priority,
    passed: row.passed,
    stage: row.stage,
    portalUpdatedOn: row.portal_updated_on,
    sourceUrl: row.source_url,
    extractedAt: row.extracted_at,
  }));
  return latestVuppYear(stats);
});
