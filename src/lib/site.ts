import { defaultLocale, locales, type Locale } from "@/i18n/config";

// Домен ещё не решён (ревью 2026-09, пункт 07) — заглушка, чтобы
// hreflang/canonical/sitemap не падали без него уже сейчас. Как только
// домен определится, поменять один раз здесь: .env.local.example и
// переменную окружения NEXT_PUBLIC_SITE_URL на проде.
export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://studet.lv";

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
