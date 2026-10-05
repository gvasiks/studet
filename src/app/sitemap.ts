import type { MetadataRoute } from "next";
import { locales, type Locale } from "@/i18n/config";
import { listProgrammes } from "@/lib/catalog";
import { buildAlternates, SITE_URL } from "@/lib/site";

// Каталог обновляет Python-конвейер напрямую в базе — карта сайта должна
// это видеть без пересборки Next.js, тот же принцип, что и на
// /programmes (dynamic = "force-dynamic").
export const dynamic = "force-dynamic";

// Пока страна одна, каждая страница существует под всеми адресами из
// locales. Когда появится Литва, список программ здесь надо будет делить
// по стране вуза (фаза 2 литовского плана).
function entry(path: string, locale: Locale) {
  return {
    url: `${SITE_URL}/${locale}${path}`,
    alternates: { languages: buildAlternates(path, locale).languages },
  };
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const programmes = await listProgrammes();

  const staticPaths = ["", "/programmes", "/survey"];
  const staticEntries: MetadataRoute.Sitemap = staticPaths.flatMap((path) =>
    locales.map((locale) => entry(path, locale)),
  );

  // Только карточки программ — калькулятор оставляем не в карте сайта:
  // это вторичная, условная страница (видна только при подтверждённой
  // формуле, правило 6 CLAUDE.md), а не самостоятельная точка входа для
  // поиска. /favorites тоже нет — она noindex (у каждого посетителя своя).
  const programmeEntries: MetadataRoute.Sitemap = programmes.flatMap((programme) => {
    const path = `/programmes/${programme.university.slug}/${programme.slug}`;
    return locales.map((locale) => entry(path, locale));
  });

  return [...staticEntries, ...programmeEntries];
}
