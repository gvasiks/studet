import type { Locale } from "@/i18n/config";

// Вынесено из catalog.ts в отдельный модуль без обращения к базе: так
// эти функции (и всё, что на них опирается — вид каталога, поиск,
// сортировка) можно тестировать без клиента Supabase, тот же приём, что
// formula.ts / formula-queries.ts.

// Латышское название приоритетнее (аудитория А — основная), но пока конвейер
// читает только английский раздел сайтов, поэтому падаем на то, что есть.
export function localizedName(
  entity: { name_lv: string | null; name_en: string | null },
  locale: Locale,
): string {
  const primary = locale === "lv" ? entity.name_lv : entity.name_en;
  return primary ?? entity.name_en ?? entity.name_lv ?? "";
}

export function enumLabel(map: Record<string, string>, key: string): string {
  return map[key] ?? key;
}
