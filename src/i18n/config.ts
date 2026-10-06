// Первый сегмент адреса — пара «язык интерфейса + страна каталога».
// Каталог каждой страны открывается на любом из трёх языков (решения
// 2026-10-05 и 2026-10-06, docs/PLAN-LITHUANIA-2027.md):
//
//   /lv/…     латышский, каталог Латвии        /lt/…     литовский, каталог Литвы
//   /en-lv/…  английский, каталог Латвии       /en-lt/…  английский, каталог Литвы
//   /lt-lv/…  литовский, каталог Латвии        /lv-lt/…  латышский, каталог Литвы
//
// Правило записи: «язык-страна»; у языка самой страны суффикса нет.
//
// В коде сегмент по-прежнему называется locale (так называется папка
// маршрутов). Когда нужен язык или страна — спрашивай languageOf() и
// countryOf(), а не сравнивай сегмент со строкой.
//
// Порядок важен: первым у страны стоит адрес на её языке (nativeLocale).
const allLocales = ["lv", "en-lv", "lt-lv", "lt", "en-lt", "lv-lt"] as const;

export type Locale = (typeof allLocales)[number];

// В этом порядке языки стоят в переключателе в шапке — одинаково на всех
// страницах.
export const languages = ["lv", "lt", "en"] as const;

export type Language = (typeof languages)[number];

// ISO 3166-1 alpha-2, как в university.country.
export type Country = "LV" | "LT";

const variants: Record<Locale, { language: Language; country: Country }> = {
  lv: { language: "lv", country: "LV" },
  "en-lv": { language: "en", country: "LV" },
  "lt-lv": { language: "lt", country: "LV" },
  lt: { language: "lt", country: "LT" },
  "en-lt": { language: "en", country: "LT" },
  "lv-lt": { language: "lv", country: "LT" },
};

// Страны, которые ещё строятся. Их адреса (у Литвы — /lt, /en-lt, /lv-lt) не
// существуют (404), их нет в карте сайта, в переключателе страны и в
// переадресации по языку браузера — пока в окружении не задано
// NEXT_PUBLIC_PREVIEW_COUNTRIES=1. Так недостроенный каталог не выйдет
// наружу вместе с латвийским выпуском; локально флаг стоит в .env.local.
// Перед запуском страны она убирается из этого списка.
//
// Закрывается именно страна, а не язык: латвийский каталог на литовском
// (/lt-lv) открыт всегда — решение владельца 2026-10-06.
const previewCountries: Country[] = ["LT"];

function isOpen(locale: Locale): boolean {
  return !previewCountries.includes(variants[locale].country) || process.env.NEXT_PUBLIC_PREVIEW_COUNTRIES === "1";
}

// Адреса, которые существуют для посетителя.
export const locales: readonly Locale[] = allLocales.filter(isOpen);

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

// Страны, у которых есть хотя бы один адрес.
export const countries: Country[] = [...new Set(locales.map((locale) => variants[locale].country))];

// Все адреса одной страны — между ними работает переключатель языка, и
// только они ссылаются друг на друга как переводы (hreflang).
export function localesOfCountry(country: Country): Locale[] {
  return locales.filter((locale) => variants[locale].country === country);
}

// Адрес страны на её основном языке: первый в списке locales.
export function nativeLocale(country: Country): Locale {
  return localesOfCountry(country)[0];
}

// Адрес страны на языке language; если такого адреса нет — на её основном
// языке.
export function localeFor(country: Country, language: Language): Locale {
  return localesOfCountry(country).find((locale) => variants[locale].language === language) ?? nativeLocale(country);
}

// Куда отправить посетителя без сегмента в адресе по языку его браузера.
// Язык, родной для какой-то открытой страны, ведёт в неё; остальные — в
// первый адрес на этом языке, то есть в Латвию. Литовский браузер поэтому
// попадает в /lt-lv, пока Литва закрыта, и в /lt, когда она откроется.
export function localeForBrowser(language: string): Locale {
  const native = countries.map(nativeLocale).find((locale) => variants[locale].language === language);
  return native ?? locales.find((locale) => variants[locale].language === language) ?? defaultLocale;
}

// До 2026-10 английская версия жила на /en. Старые ссылки (закладки,
// разосланные тестировщикам адреса) переадресуются, см. src/proxy.ts.
export const legacyLocales: Record<string, Locale> = { en: "en-lv" };
