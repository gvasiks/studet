// Стоимость года для иностранных абитуриентов — чистая логика, без базы
// (docs/PLAN-FOREIGNERS.md, шаг 1; миграция 20261108120000_foreign_costs.sql).
// Сюда приходят только подтверждённые человеком строки: неподтверждённые
// отсекает политика доступа в базе (правило 6).

export const COUNTRY_COST_CODES = [
  "residence_permit_review",
  "residence_permit_registration",
  "long_stay_visa",
  "means_per_month",
] as const;
export type CountryCostCode = (typeof COUNTRY_COST_CODES)[number];

export const FEE_KINDS = ["tuition", "application_fee", "enrolment_fee"] as const;
export type FeeKind = (typeof FEE_KINDS)[number];

/** eu — граждане ЕС, ЕЭЗ и Швейцарии; non_eu — все остальные. */
export type AppliesTo = "eu" | "non_eu";

export type CountryCost = {
  code: CountryCostCode;
  appliesTo: AppliesTo;
  amount: number;
  currency: string;
  period: "once" | "month";
  validFrom: string;
  validTo: string | null;
  sourceTitle: string;
  sourceUrl: string;
  verifiedAt: string;
};

export type ProgrammeFee = {
  kind: FeeKind;
  appliesTo: AppliesTo;
  amount: number;
  currency: string;
  period: "year" | "once";
  academicYear: string;
  sourceUrl: string;
  verifiedAt: string;
  /** null — цена eu для ЕС, ЕЭЗ и Швейцарии; eu_efta_candidates — вуз даёт её
   * и гражданам ЕАСТ и стран-кандидатов в ЕС (миграция 20261108130000). */
  euScope: "eu_efta_candidates" | null;
};

/** Вуз даёт цену eu и гражданам стран-кандидатов — нужна пометка под ценами. */
export function euPriceIncludesCandidates(fees: ProgrammeFee[]): boolean {
  return fees.some((fee) => fee.euScope === "eu_efta_candidates");
}

// Даты сравниваются строками «ГГГГ-ММ-ДД»: так не нужно думать о часовых поясах.
function isoDay(date: Date): string {
  return date.toISOString().slice(0, 10);
}

/** Суммы, действующие на дату: по одной на код и группу — с самой поздней датой начала. */
export function currentCountryCosts(costs: CountryCost[], today: Date): CountryCost[] {
  const day = isoDay(today);
  const best = new Map<string, CountryCost>();
  for (const cost of costs) {
    if (cost.validFrom > day) continue;
    if (cost.validTo !== null && cost.validTo <= day) continue;
    const key = `${cost.code}:${cost.appliesTo}`;
    const prior = best.get(key);
    if (!prior || cost.validFrom > prior.validFrom) best.set(key, cost);
  }
  return [...best.values()];
}

/** Платы программы для группы: по одной на вид — за самый поздний учебный год. */
export function feesFor(fees: ProgrammeFee[], appliesTo: AppliesTo): Partial<Record<FeeKind, ProgrammeFee>> {
  const result: Partial<Record<FeeKind, ProgrammeFee>> = {};
  for (const fee of fees) {
    if (fee.appliesTo !== appliesTo) continue;
    const prior = result[fee.kind];
    if (!prior || fee.academicYear > prior.academicYear) result[fee.kind] = fee;
  }
  return result;
}

export function costFor(costs: CountryCost[], code: CountryCostCode, appliesTo: AppliesTo): CountryCost | null {
  return costs.find((cost) => cost.code === code && cost.appliesTo === appliesTo) ?? null;
}

/**
 * Обязательные платежи первого года для группы: плата за год, разовые взносы
 * вуза, пошлины за ВНЖ (рассмотрение и регистрация). Виза в сумму не входит —
 * она нужна не всем; подтверждение средств — не расход, а сумма, которую
 * нужно показать. null — без платы за обучение итог не считается вовсе:
 * сумма одних пошлин выглядела бы ценой года.
 */
export function firstYearTotal(
  fees: Partial<Record<FeeKind, ProgrammeFee>>,
  costs: CountryCost[],
  appliesTo: AppliesTo,
): { amount: number; currency: string } | null {
  const tuition = fees.tuition;
  if (!tuition || tuition.period !== "year") return null;
  const parts: { amount: number; currency: string }[] = [tuition];
  if (fees.application_fee) parts.push(fees.application_fee);
  if (fees.enrolment_fee) parts.push(fees.enrolment_fee);
  for (const code of ["residence_permit_review", "residence_permit_registration"] as const) {
    const cost = costFor(costs, code, appliesTo);
    if (cost) parts.push(cost);
  }
  // Разные валюты не складываем: итог был бы бессмыслицей.
  if (parts.some((part) => part.currency !== tuition.currency)) return null;
  return { amount: parts.reduce((sum, part) => sum + part.amount, 0), currency: tuition.currency };
}

/** «1 234 €» / «€1,234» — по языку; копейки — только если они есть. */
export function formatMoney(amount: number, currency: string, language: string): string {
  const whole = Number.isInteger(amount);
  return new Intl.NumberFormat(language, {
    style: "currency",
    currency,
    minimumFractionDigits: whole ? 0 : 2,
    maximumFractionDigits: whole ? 0 : 2,
  }).format(amount);
}
