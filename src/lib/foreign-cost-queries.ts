import { cache } from "react";
import type { Country } from "@/i18n/config";
import { supabase } from "@/lib/supabase";
import { remember } from "@/lib/server-memo";
import {
  COUNTRY_COST_CODES,
  EU_SCOPES,
  FEE_KINDS,
  type AppliesTo,
  type CountryCost,
  type CountryCostCode,
  type EuScope,
  type HousingCost,
  type FeeKind,
  type ProgrammeFee,
} from "@/lib/foreign-costs";
import { parseRequirements, type DocumentRequirement } from "@/lib/foreign-documents";
import { parseEnglishRequirements, type EnglishRequirement } from "@/lib/english-requirement";

// Общие суммы страны меняются раз в год — живут в памяти сервера пять минут,
// как каталог (server-memo.ts). Подтверждение в Studio видно с той же задержкой.
const COUNTRY_COSTS_MEMORY_MS = 5 * 60 * 1000;

const isAppliesTo = (value: string): value is AppliesTo => value === "eu" || value === "non_eu";

// Только подтверждённые: гейт стоит и здесь, и в политике доступа таблицы
// (она и есть граница — anon-ключ публичный). Ошибка — пустой список, а не
// упавшая карточка: блок стоимости — дополнение, и так страница переживает
// промежуток между выкладкой кода и применением миграции.
export async function getCountryCosts(country: Country): Promise<CountryCost[]> {
  return remember(`country-costs:${country}`, COUNTRY_COSTS_MEMORY_MS, async () => {
    const { data, error } = await supabase
      .from("country_cost")
      .select("code, applies_to, amount, currency, period, valid_from, valid_to, source_title, source_url, verified_at")
      .eq("country", country)
      .not("verified_at", "is", null);
    if (error) return [];
    return (data ?? [])
      .filter(
        (row) =>
          (COUNTRY_COST_CODES as readonly string[]).includes(row.code) &&
          isAppliesTo(row.applies_to) &&
          (row.period === "once" || row.period === "month"),
      )
      .map((row) => ({
        code: row.code as CountryCostCode,
        appliesTo: row.applies_to as AppliesTo,
        amount: Number(row.amount),
        currency: row.currency,
        period: row.period as "once" | "month",
        validFrom: row.valid_from,
        validTo: row.valid_to,
        sourceTitle: row.source_title,
        sourceUrl: row.source_url,
        verifiedAt: row.verified_at,
      }));
  });
}

// Цены общежитий вуза — подтверждённые строки, все даты (действующую выбирает
// currentHousingCost). В памяти пять минут, как общие суммы страны.
export async function getHousingCosts(universityId: string): Promise<HousingCost[]> {
  return remember(`housing-costs:${universityId}`, COUNTRY_COSTS_MEMORY_MS, async () => {
    const { data, error } = await supabase
      .from("housing_cost")
      .select("amount_min, amount_max, currency, valid_from, source_title, source_url, verified_at")
      .eq("university_id", universityId)
      .not("verified_at", "is", null);
    if (error) return [];
    return (data ?? []).map((row) => ({
      amountMin: Number(row.amount_min),
      amountMax: Number(row.amount_max),
      currency: row.currency,
      validFrom: row.valid_from,
      sourceTitle: row.source_title,
      sourceUrl: row.source_url,
      verifiedAt: row.verified_at,
    }));
  });
}

export const getProgrammeFees = cache(async (programmeId: string): Promise<ProgrammeFee[]> => {
  const { data, error } = await supabase
    .from("programme_fee")
    .select("kind, applies_to, amount, currency, period, academic_year, source_url, verified_at, eu_scope")
    .eq("programme_id", programmeId)
    .not("verified_at", "is", null);
  if (error) return [];
  return (data ?? [])
    .filter(
      (row) =>
        (FEE_KINDS as readonly string[]).includes(row.kind) &&
        isAppliesTo(row.applies_to) &&
        (row.period === "year" || row.period === "once"),
    )
    .map((row) => ({
      kind: row.kind as FeeKind,
      appliesTo: row.applies_to as AppliesTo,
      amount: Number(row.amount),
      currency: row.currency,
      period: row.period as "year" | "once",
      academicYear: row.academic_year,
      sourceUrl: row.source_url,
      verifiedAt: row.verified_at,
      euScope: (EU_SCOPES as readonly string[]).includes(row.eu_scope) ? (row.eu_scope as EuScope) : null,
    }));
});

// Чек-лист документов вуза на уровне программы (шаг 3) — подтверждённые строки.
// В памяти пять минут, как цены общежитий; ошибка — пустой список.
export async function getDocumentRequirements(universityId: string, degreeLevel: string): Promise<DocumentRequirement[]> {
  return remember(`documents:${universityId}:${degreeLevel}`, COUNTRY_COSTS_MEMORY_MS, async () => {
    const { data, error } = await supabase
      .from("foreign_document_requirement")
      .select("document, applies_to, stage, note, sort_order, source_url, verified_at")
      .eq("university_id", universityId)
      .eq("degree_level", degreeLevel)
      .not("verified_at", "is", null);
    if (error) return [];
    return parseRequirements(data ?? []);
  });
}

// Требования к английскому вуза на уровне программы (шаг 4): строки вуза и
// строки отдельных программ этого уровня; выбирает pickEnglishRequirement.
export async function getEnglishRequirements(universityId: string, degreeLevel: string): Promise<EnglishRequirement[]> {
  return remember(`english:${universityId}:${degreeLevel}`, COUNTRY_COSTS_MEMORY_MS, async () => {
    const { data, error } = await supabase
      .from("english_requirement")
      .select("programme_id, ielts_min, toefl_ibt_min, toefl_ibt_band, note, source_url, verified_at")
      .eq("university_id", universityId)
      .eq("degree_level", degreeLevel)
      .not("verified_at", "is", null);
    if (error) return [];
    return parseEnglishRequirements(data ?? []);
  });
}

export type UniversityDocumentList = {
  university: { slug: string; name_lv: string | null; name_en: string | null; name_lt: string | null; name_et: string | null };
  degreeLevel: string;
  items: DocumentRequirement[];
  /** Требование к английскому на весь уровень вуза (programme_id пустой). */
  english: EnglishRequirement | null;
  /** У вуза на этом уровне требования к английскому заданы по программам (как у ЛУ). */
  englishByProgramme: boolean;
};

// Все подтверждённые списки документов страны — для страницы /student-documents.
// Порядок: вузы по названию на латышском, внутри — бакалавриат, магистратура.
const LEVEL_ORDER = ["college", "bachelor", "master", "doctoral"];

export async function getCountryDocumentLists(country: Country): Promise<UniversityDocumentList[]> {
  return remember(`document-lists:${country}`, COUNTRY_COSTS_MEMORY_MS, async () => {
    const [documents, english] = await Promise.all([
      supabase
        .from("foreign_document_requirement")
        .select(
          "university_id, degree_level, document, applies_to, stage, note, sort_order, source_url, verified_at, " +
            "university!inner(slug, name_lv, name_en, name_lt, name_et, country)",
        )
        .eq("university.country", country)
        .not("verified_at", "is", null),
      supabase
        .from("english_requirement")
        .select("university_id, degree_level, programme_id, ielts_min, toefl_ibt_min, toefl_ibt_band, note, source_url, verified_at")
        .not("verified_at", "is", null),
    ]);
    if (documents.error) return [];
    const englishRows = english.error ? [] : (english.data ?? []);

    type DocumentRow = Parameters<typeof parseRequirements>[0][number] & {
      university_id: string;
      degree_level: string;
      university: UniversityDocumentList["university"];
    };
    const groups = new Map<string, { university: UniversityDocumentList["university"]; universityId: string; level: string; rows: DocumentRow[] }>();
    for (const row of (documents.data ?? []) as unknown as DocumentRow[]) {
      const key = `${row.university_id}:${row.degree_level}`;
      const group = groups.get(key) ?? { university: row.university, universityId: row.university_id, level: row.degree_level, rows: [] };
      group.rows.push(row);
      groups.set(key, group);
    }

    return [...groups.values()]
      .map((group) => {
        const own = englishRows.filter((row) => row.university_id === group.universityId && row.degree_level === group.level);
        const universityWide = parseEnglishRequirements(own.filter((row) => row.programme_id === null));
        return {
          university: group.university,
          degreeLevel: group.level,
          items: parseRequirements(group.rows),
          english: universityWide[0] ?? null,
          englishByProgramme: own.some((row) => row.programme_id !== null),
        };
      })
      .sort(
        (a, b) =>
          (a.university.name_lv ?? "").localeCompare(b.university.name_lv ?? "", "lv") ||
          LEVEL_ORDER.indexOf(a.degreeLevel) - LEVEL_ORDER.indexOf(b.degreeLevel),
      );
  });
}
