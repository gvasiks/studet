import { cache } from "react";
import type { Country } from "@/i18n/config";
import { supabase } from "@/lib/supabase";
import { remember } from "@/lib/server-memo";
import {
  COUNTRY_COST_CODES,
  FEE_KINDS,
  type AppliesTo,
  type CountryCost,
  type CountryCostCode,
  type FeeKind,
  type ProgrammeFee,
} from "@/lib/foreign-costs";

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

export const getProgrammeFees = cache(async (programmeId: string): Promise<ProgrammeFee[]> => {
  const { data, error } = await supabase
    .from("programme_fee")
    .select("kind, applies_to, amount, currency, period, academic_year, source_url, verified_at")
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
    }));
});
