import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { countries, isLocale } from "@/i18n/config";
import { hasFeature } from "@/lib/country";
import { getDictionary } from "@/i18n/dictionaries";
import { getApplicationRoundsForCards } from "@/lib/deadline-queries";
import type { ApplicationRound } from "@/lib/deadlines";
import { getCalculatorProgrammeIds } from "@/lib/calculator-ids";
import { getEeOpenDeadlines } from "@/lib/ee-admission-queries";
import { FavoritesList } from "./FavoritesList";

// noindex — страница у каждого посетителя своя (localStorage конкретного
// браузера), у неё нет содержимого, общего для двух разных людей, а
// значит и смысла попадать в выдачу (ревью 2026-09, пункт 08).
export async function generateMetadata({ params }: PageProps<"/[locale]/favorites">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  if (!hasFeature(locale, "favorites")) notFound();

  const dict = await getDictionary(locale);
  return {
    title: dict.favorites.title,
    robots: { index: false, follow: true },
  };
}

// Сам список — в браузере посетителя, но кнопке калькулятора и чипу со
// сроком на карточках нужны общие для всех данные. Их отдаёт сервер и
// обновляет раз в час, как главная.
export const revalidate = 3600;

// Сбой базы не должен ронять страницу: карточки просто останутся без
// кнопки калькулятора и без срока подачи.
async function loadCardData(): Promise<{
  calculatorIds: string[];
  applicationRounds: ApplicationRound[];
  eeDeadlines: Record<string, string>;
}> {
  try {
    // Список общий для всех открытых стран — и кнопка расчёта нужна программам каждой.
    const [idSets, applicationRounds, eeDeadlines] = await Promise.all([
      Promise.all(countries.map((country) => getCalculatorProgrammeIds(country))),
      getApplicationRoundsForCards(),
      // Действующие сроки подачи эстонских программ (id программы -> конец подачи).
      countries.includes("EE") ? getEeOpenDeadlines() : {},
    ]);
    return { calculatorIds: idSets.flatMap((ids) => [...ids]), applicationRounds, eeDeadlines };
  } catch {
    return { calculatorIds: [], applicationRounds: [], eeDeadlines: {} };
  }
}

export default async function FavoritesPage({ params }: PageProps<"/[locale]/favorites">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  if (!hasFeature(locale, "favorites")) notFound();

  const dict = await getDictionary(locale);
  const { calculatorIds, applicationRounds, eeDeadlines } = await loadCardData();

  return (
    // Заголовок — на сером фоне, как на /rights, /glossary и /survey;
    // раньше он лежал внутри карточки, из-за чего страница выглядела иначе,
    // чем остальные. Карточки и таблицу сравнения заводит сам список.
    <main className="page-container py-8 sm:py-12">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">{dict.favorites.title}</h1>
        <p className="mt-3 max-w-[65ch] text-lg leading-relaxed text-zinc-600">{dict.favorites.subtitle}</p>
      </header>
      <FavoritesList
        locale={locale}
        dict={dict}
        calculatorIds={calculatorIds}
        applicationRounds={applicationRounds}
        eeDeadlines={eeDeadlines}
      />
    </main>
  );
}
