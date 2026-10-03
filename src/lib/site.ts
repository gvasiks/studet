import { defaultLocale, locales, type Locale } from "@/i18n/config";

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

// path — без локали, начинается с "/" или пустой для главной, например
// "/programmes" или "/programmes/lu/economics". Canonical — на текущую
// локаль; x-default — на defaultLocale (lv), это latvija-аудитория
// (правило 4 CLAUDE.md), не английская.
export function buildAlternates(path: string, currentLocale: Locale) {
  const languages: Record<string, string> = {};
  for (const locale of locales) {
    languages[locale] = `${SITE_URL}/${locale}${path}`;
  }
  languages["x-default"] = `${SITE_URL}/${defaultLocale}${path}`;

  return {
    canonical: `${SITE_URL}/${currentLocale}${path}`,
    languages,
  };
}
