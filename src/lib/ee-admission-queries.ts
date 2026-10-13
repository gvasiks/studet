import { cache } from "react";
import { supabase } from "@/lib/supabase";
import { parseFunding, type EeAdmission } from "@/lib/ee-admission";
import { remember } from "@/lib/server-memo";

// Последний конкурс эстонской программы (таблица ee_admission). Сроки и
// ссылку пишет pipeline/src/ee_load_admissions.py из данных государственного
// портала, условия конкурса — ee_load_admission_details.py со страницы SAIS.
// Действующий он или прошлый, решает ee-admission.ts по сроку.

export const getEeAdmission = cache(async (programmeId: string): Promise<EeAdmission | null> => {
  const { data, error } = await supabase
    .from("ee_admission")
    .select(
      "sais_url, opens_at, closes_at, source_url, extracted_at, title, study_form, location, starts_on, funding, details_fetched_at",
    )
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
    title: data.title,
    studyForm: data.study_form,
    location: data.location,
    startsOn: data.starts_on,
    funding: parseFunding(data.funding),
    detailsFetchedAt: data.details_fetched_at,
  };
});

// Сколько строк читается за один запрос: PostgREST отдаёт не больше тысячи.
const PAGE_ROWS = 1000;

// Действующие сроки подачи для карточек каталога и списка сохранённых:
// id программы -> конец подачи. Только конкурсы, срок которых ещё не прошёл
// (в межсезонье их десятки, в сезон приёма — сотни). Из памяти сервера, как
// остальные данные каталога (server-memo.ts): карточке срок нужен при каждом
// показе списка. Объект общий для всех запросов — только читать.
export function getEeOpenDeadlines(): Promise<Record<string, string>> {
  return remember("ee-open-deadlines", 5 * 60 * 1000, async () => {
    const deadlines: Record<string, string> = {};
    const now = new Date().toISOString();
    for (let from = 0; ; from += PAGE_ROWS) {
      const { data, error } = await supabase
        .from("ee_admission")
        .select("programme_id, closes_at")
        .gte("closes_at", now)
        .order("programme_id")
        .range(from, from + PAGE_ROWS - 1);
      if (error) throw error;
      for (const row of data) deadlines[row.programme_id as string] = row.closes_at as string;
      if (data.length < PAGE_ROWS) break;
    }
    return deadlines;
  });
}
