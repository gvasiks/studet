import { countryOf, languageOf, localesOfCountry, nativeLocale, type Locale } from "@/i18n/config";

// Название продукта — имя собственное, одинаковое на всех языках, поэтому
// живёт здесь, а не в словарях локалей. Решение владельца 2026-10-03
// (docs/NAMING-2026-10.md); до этого проект назывался Studet — это имя
// осталось только во внутренних идентификаторах (репозиторий, имя пакета,
// ключ localStorage), которые пользователь не видит.
export const SITE_NAME = "StudyPick";

// Адрес сайта — для hreflang/canonical/sitemap. Значение по умолчанию —
// выбранный домен; на проде задаётся переменной окружения
// NEXT_PUBLIC_SITE_URL (см. .env.local.example).
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://studypick.eu";

// Закрытая выкладка: сайт уже стоит на настоящем домене, но до запуска
// поисковикам его показывать рано (данные не все подтверждены, тексты не
// вычитаны). SITE_CLOSED=1 в настройках сервера запрещает обход в
// robots.txt и ставит noindex на каждую страницу; в день запуска
// переменная убирается, сайт пересобирается. Читается и при сборке, и при
// работе — на сервере у них один файл настроек (deploy/README.md).
export function isSiteClosed(env: Record<string, string | undefined> = process.env): boolean {
  return env.SITE_CLOSED === "1";
}

// path — без первого сегмента, начинается с "/" или пустой для главной,
// например "/programmes" или "/programmes/lu/economics".
//
// Переводами друг друга считаются только адреса одной страны: у латвийской
// программы нет литовской версии. Ключ hreflang — язык без страны ("en", а
// не "en-LV"): английская версия адресована иностранным абитуриентам
// откуда угодно, а не англоязычным жителям Латвии.
//
// Canonical — на текущий адрес; x-default — на основной язык страны.
export function buildAlternates(path: string, currentLocale: Locale) {
  const country = countryOf(currentLocale);
  const languages: Record<string, string> = {};
  for (const locale of localesOfCountry(country)) {
    languages[languageOf(locale)] = `${SITE_URL}/${locale}${path}`;
  }
  languages["x-default"] = `${SITE_URL}/${nativeLocale(country)}${path}`;

  return {
    canonical: `${SITE_URL}/${currentLocale}${path}`,
    languages,
  };
}
