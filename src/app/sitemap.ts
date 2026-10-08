import type { MetadataRoute } from "next";
import { countries, locales, localesOfCountry, type Locale } from "@/i18n/config";
import { listProgrammes } from "@/lib/catalog";
import { hasFeature, type Feature } from "@/lib/country";
import { buildAlternates, SITE_URL } from "@/lib/site";

// Каталог обновляет Python-конвейер напрямую в базе — карта сайта должна
// это видеть без пересборки Next.js, тот же принцип, что и на
// /programmes (dynamic = "force-dynamic").
export const dynamic = "force-dynamic";

// Главная и каталог есть под каждым адресом из locales; остальные разделы —
// только там, где они открыты у страны и написаны на языке адреса
// (hasFeature): иначе карта сайта звала бы поисковик на страницу «не
// найдено». Карточка программы — только под адресами своей страны.
// Политики конфиденциальности здесь нет намеренно: ссылка на неё в подвале
// и строка в карте сайта добавляются при публикации, когда владелец
// утвердит текст и задаст оператора данных (docs/PRIVACY-CHECKLIST.md,
// раздел 4).
const SECTIONS: { path: string; feature?: Feature }[] = [
  { path: "" },
  { path: "/programmes" },
  { path: "/survey", feature: "survey" },
  { path: "/match", feature: "match" },
  { path: "/glossary", feature: "glossary" },
  { path: "/rights", feature: "rights" },
];

function entry(path: string, locale: Locale) {
  return {
    url: `${SITE_URL}/${locale}${path}`,
    alternates: { languages: buildAlternates(path, locale).languages },
  };
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticEntries: MetadataRoute.Sitemap = SECTIONS.flatMap(({ path, feature }) =>
    locales.filter((locale) => !feature || hasFeature(locale, feature)).map((locale) => entry(path, locale)),
  );

  // Только карточки программ — калькулятор оставляем не в карте сайта:
  // это вторичная, условная страница (видна только при подтверждённой
  // формуле, правило 6 CLAUDE.md), а не самостоятельная точка входа для
  // поиска. /favorites тоже нет — она noindex (у каждого посетителя своя).
  const programmeEntries: MetadataRoute.Sitemap = [];
  for (const country of countries) {
    const programmes = await listProgrammes(country);
    for (const programme of programmes) {
      const path = `/programmes/${programme.university.slug}/${programme.slug}`;
      for (const locale of localesOfCountry(country)) programmeEntries.push(entry(path, locale));
    }
  }

  return [...staticEntries, ...programmeEntries];
}
