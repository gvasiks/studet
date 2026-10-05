import type { MetadataRoute } from "next";
import { countries, locales, localesOfCountry, type Locale } from "@/i18n/config";
import { listProgrammes } from "@/lib/catalog";
import { buildAlternates, SITE_URL } from "@/lib/site";

// Каталог обновляет Python-конвейер напрямую в базе — карта сайта должна
// это видеть без пересборки Next.js, тот же принцип, что и на
// /programmes (dynamic = "force-dynamic").
export const dynamic = "force-dynamic";

// Общие страницы есть под каждым адресом из locales; карточка программы —
// только под адресами своей страны.
function entry(path: string, locale: Locale) {
  return {
    url: `${SITE_URL}/${locale}${path}`,
    alternates: { languages: buildAlternates(path, locale).languages },
  };
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticPaths = ["", "/programmes", "/survey"];
  const staticEntries: MetadataRoute.Sitemap = staticPaths.flatMap((path) =>
    locales.map((locale) => entry(path, locale)),
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
