// Первый сегмент адреса — пара «язык интерфейса + страна каталога».
// Каталог каждой страны открывается на любом из языков интерфейса (решения
// 2026-10-05 и 2026-10-06, docs/PLAN-LITHUANIA-2027.md; эстонский и Эстония
// — 2026-10-11, docs/PLAN-ESTONIA.md):
//
//   Латвия   /lv      /lt-lv   /et-lv   /en-lv
//   Литва    /lv-lt   /lt      /et-lt   /en-lt
//   Эстония  /lv-ee   /lt-ee   /et      /en-ee
//
// Правило записи: «язык-страна»; у языка самой страны суффикса нет.
//
// В коде сегмент по-прежнему называется locale (так называется папка
// маршрутов). Когда нужен язык или страна — спрашивай languageOf() и
// countryOf(), а не сравнивай сегмент со строкой.
//
// Порядок важен: первым у страны стоит адрес на её языке (nativeLocale).
const allLocales = [
  "lv", "en-lv", "lt-lv", "et-lv",
  "lt", "en-lt", "lv-lt", "et-lt",
  "et", "en-ee", "lv-ee", "lt-ee",
] as const;

export type Locale = (typeof allLocales)[number];

// В этом порядке языки стоят в переключателе в шапке — одинаково на всех
// страницах.
export const languages = ["lv", "lt", "et", "en"] as const;

export type Language = (typeof languages)[number];

// Язык, на котором написаны названия и описания программ. Сейчас совпадает
// с языками интерфейса; отдельное имя — на случай страны, чьи программы
// названы на языке, которого в интерфейсе нет.
export type ContentLanguage = Language;

// ISO 3166-1 alpha-2, как в university.country.
export type Country = "LV" | "LT" | "EE";

const variants: Record<Locale, { language: Language; country: Country }> = {
  lv: { language: "lv", country: "LV" },
  "en-lv": { language: "en", country: "LV" },
  "lt-lv": { language: "lt", country: "LV" },
  lt: { language: "lt", country: "LT" },
  "en-lt": { language: "en", country: "LT" },
  "lv-lt": { language: "lv", country: "LT" },
  "et-lv": { language: "et", country: "LV" },
  "et-lt": { language: "et", country: "LT" },
  et: { language: "et", country: "EE" },
  "en-ee": { language: "en", country: "EE" },
  "lv-ee": { language: "lv", country: "EE" },
  "lt-ee": { language: "lt", country: "EE" },
};

// Страны, которые ещё строятся. Их адреса (у Литвы — /lt, /en-lt, /lv-lt) не
// существуют (404), их нет в карте сайта, в переключателе страны и в
// переадресации по языку браузера — пока в окружении не задано
// NEXT_PUBLIC_PREVIEW_COUNTRIES=1. Так недостроенный каталог не выйдет
// наружу вместе с латвийским выпуском; локально флаг стоит в .env.local.
// На рабочем сервере флаг допустим только на закрытой выкладке (за паролем,
// SITE_CLOSED=1): сборку открытого сайта с ним останавливает
// scripts/check-privacy-env.mjs. Перед запуском страны она убирается из
// этого списка.
//
// Закрывается именно страна, а не язык: латвийский каталог на литовском
// (/lt-lv) открыт всегда — решение владельца 2026-10-06.
const previewCountries: Country[] = ["LT", "EE"];

// Языки интерфейса, которые ещё строятся: тем же флагом закрыты все адреса
// на этом языке, у любой страны. Эстонский (с 2026-10-12) — пока не
// переведены словарь терминов, права и политика и пока владелец не решил,
// выходит ли /et-lv вместе с латвийским запуском, как /lt-lv.
const previewLanguages: Language[] = ["et"];

function isOpen(locale: Locale): boolean {
  const { country, language } = variants[locale];
  const preview = previewCountries.includes(country) || previewLanguages.includes(language);
  return !preview || process.env.NEXT_PUBLIC_PREVIEW_COUNTRIES === "1";
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
