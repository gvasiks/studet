import { cache } from "react";
import { supabase } from "@/lib/supabase";
import { parseFunding, type EeAdmission } from "@/lib/ee-admission";
import { parseRule, type EeRule } from "@/lib/ee-rule";
import { remember } from "@/lib/server-memo";

// Последний конкурс эстонской программы (таблица ee_admission). Сроки и
// ссылку пишет pipeline/src/ee_load_admissions.py из данных государственного
// портала, условия конкурса — ee_load_admission_details.py со страницы SAIS,
// правило конкурса — ee_load_rules.py.
// Действующий он или прошлый, решает ee-admission.ts по сроку.

export const getEeAdmission = cache(async (programmeId: string): Promise<EeAdmission | null> => {
  const { data, error } = await supabase
    .from("ee_admission")
    .select(
      "sais_url, opens_at, closes_at, source_url, extracted_at, title, study_form, location, starts_on, funding, details_fetched_at, rule, rule_source_url, rule_extracted_at",
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
    rule: parseRule(data.rule),
    ruleSourceUrl: data.rule_source_url,
    ruleExtractedAt: data.rule_extracted_at,
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

// Правило конкурса следующего учебного года из решения вуза (таблица
// ee_next_rule, пишет pipeline/src/ee_load_taltech_conditions.py) — пока у
// TalTech: условия 2027/28 утверждены сенатом осенью, а конкурсы SAIS
// откроются весной. Если правил несколько лет, берётся последний год.
export type EeNextRule = {
  academicYear: string;
  rule: EeRule;
  newCurriculum: boolean;
  sourceUrl: string;
  sourceTitle: string;
  decidedOn: string;
  extractedAt: string;
};

// PGRST205 / 42P01 — таблицы ещё нет: миграция 20261127130000 не применена.
const MISSING_TABLE = new Set(["PGRST205", "42P01"]);

export const getEeNextRule = cache(async (programmeId: string): Promise<EeNextRule | null> => {
  const { data, error } = await supabase
    .from("ee_next_rule")
    .select("academic_year, rule, new_curriculum, source_url, source_title, decided_on, extracted_at")
    .eq("programme_id", programmeId)
    .order("academic_year", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (error && MISSING_TABLE.has(error.code)) return null;
  if (error) throw error;
  if (!data) return null;
  const rule = parseRule(data.rule);
  if (!rule) return null;
  return {
    academicYear: data.academic_year,
    rule,
    newCurriculum: data.new_curriculum,
    sourceUrl: data.source_url,
    sourceTitle: data.source_title,
    decidedOn: data.decided_on,
    extractedAt: data.extracted_at,
  };
});
