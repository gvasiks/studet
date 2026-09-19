// Направление программы = код группы программ из классификатора
// образования (3 цифры; первые две — тематическая область), тот же, по
// которому ИЗМ публикует мониторинг выпускников. Ревью 2026-09, пункты
// 14 и 16 (см. supabase/migrations/..._programme_field_and_graduate_outcomes.sql).

// Категории интересов в анкете (шаг 2) — не абстрактные "типы
// личности" (CLAUDE.md: такие рекомендации обосновать нельзя), а
// группировка того, что реально есть в каталоге. Прежние шесть
// категорий оставляли 50 из 339 программ (15%) недостижимыми ни одной
// галочкой: образование, искусство и дизайн, психология/социология/
// политология, туризм и спорт, транспорт, безопасность — второй шаг
// анкеты, по словам ревью, "выдаёт бессмысленные фильтры".
export const INTEREST_KEYS = [
  "business",
  "it",
  "law",
  "health",
  "engineering",
  "science",
  "humanities",
  "arts",
  "society",
  "services",
] as const;

export type InterestKey = (typeof INTEREST_KEYS)[number];

// Префиксы кода направления: 2 цифры — вся область, 3 цифры — одна
// группа (так экономика 311 отделена от остальной области 31, где
// психология, социология и политология — это "society").
const INTEREST_PREFIXES: Record<InterestKey, string[]> = {
  business: ["34", "311"],
  it: ["48"],
  law: ["38", "86"],
  health: ["72", "76"],
  engineering: ["52", "54", "58", "84"],
  science: ["42", "44", "46", "62", "64", "85"],
  humanities: ["22", "32"],
  arts: ["21"],
  society: ["14", "310", "312", "313", "314"],
  services: ["81"],
};

export function isInterestKey(value: string): value is InterestKey {
  return (INTEREST_KEYS as readonly string[]).includes(value);
}

export function interestOf(fieldCode: string): InterestKey | null {
  for (const key of INTEREST_KEYS) {
    if (INTEREST_PREFIXES[key].some((prefix) => fieldCode.startsWith(prefix))) return key;
  }
  return null;
}

// Все 3-значные коды, входящие в выбранные категории — для фильтра
// `field_code in (...)`. Префикс из двух цифр разворачивается в 10 кодов.
export function fieldCodesForInterests(keys: InterestKey[]): string[] {
  const codes = new Set<string>();
  for (const key of keys) {
    for (const prefix of INTEREST_PREFIXES[key]) {
      if (prefix.length === 3) {
        codes.add(prefix);
      } else {
        for (let digit = 0; digit <= 9; digit += 1) codes.add(`${prefix}${digit}`);
      }
    }
  }
  return [...codes];
}

export function areaCode(fieldCode: string): string {
  return fieldCode.slice(0, 2);
}
