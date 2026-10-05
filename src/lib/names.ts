import type { Language } from "@/i18n/config";

// Вынесено из catalog.ts в отдельный модуль без обращения к базе: так
// эти функции (и всё, что на них опирается — вид каталога, поиск,
// сортировка) можно тестировать без клиента Supabase, тот же приём, что
// formula.ts / formula-queries.ts.

// Название на языке страницы, а если его нет — на любом, какой есть.
// У записи заполнено название на языке её страны (name_lv у латвийских,
// name_lt у литовских) и, не у всех, английское. Запасной порядок: сначала
// английское, потом язык страны — так английская страница не показывает
// латышское название там, где есть английское.
export function localizedName(
  entity: { name_lv: string | null; name_en: string | null; name_lt?: string | null },
  language: Language,
): string {
  const byLanguage = { lv: entity.name_lv, en: entity.name_en, lt: entity.name_lt ?? null };
  return byLanguage[language] ?? entity.name_en ?? entity.name_lv ?? entity.name_lt ?? "";
}

export function enumLabel(map: Record<string, string>, key: string): string {
  return map[key] ?? key;
}
