// Первый сегмент адреса — не просто язык, а пара «язык интерфейса + страна
// каталога» (решение 2026-10-05, docs/PLAN-LITHUANIA-2027.md):
//
//   /lv/…     латышский, каталог Латвии
//   /en-lv/…  английский, каталог Латвии
//   /lt/…     литовский, каталог Литвы      — включается в фазе 2
//   /en-lt/…  английский, каталог Литвы     — включается в фазе 2
//
// Литовские варианты добавляются сюда вместе со словарём lt.json: открывать
// адрес без переведённого интерфейса нельзя.
//
// В коде сегмент по-прежнему называется locale (так называется папка
// маршрутов). Когда нужен язык или страна — спрашивай languageOf() и
// countryOf(), а не сравнивай сегмент со строкой.
export const locales = ["lv", "en-lv"] as const;

export type Locale = (typeof locales)[number];

export type Language = "lv" | "en";

// ISO 3166-1 alpha-2, как в university.country.
export type Country = "LV";

const variants: Record<Locale, { language: Language; country: Country }> = {
  lv: { language: "lv", country: "LV" },
  "en-lv": { language: "en", country: "LV" },
};

export const defaultLocale: Locale = "lv";

export function isLocale(value: string): value is Locale {
  return (locales as readonly string[]).includes(value);
}

export function languageOf(locale: Locale): Language {
  return variants[locale].language;
}

export function countryOf(locale: Locale): Country {
  return variants[locale].country;
}

// Все адреса одной страны — между ними работает переключатель языка, и
// только они ссылаются друг на друга как переводы (hreflang).
export function localesOfCountry(country: Country): Locale[] {
  return locales.filter((locale) => variants[locale].country === country);
}

// Адрес страны на её основном языке: первый в списке locales.
export function nativeLocale(country: Country): Locale {
  return localesOfCountry(country)[0];
}

// До 2026-10 английская версия жила на /en. Старые ссылки (закладки,
// разосланные тестировщикам адреса) переадресуются, см. src/proxy.ts.
export const legacyLocales: Record<string, Locale> = { en: "en-lv" };
