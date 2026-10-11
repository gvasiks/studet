import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { countries, countryOf, isLocale, languageOf } from "@/i18n/config";
import { catalogProfile, countryProfile, hasFeature } from "@/lib/country";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import { getApplicationRoundsForCards } from "@/lib/deadline-queries";
import { getCalculatorProgrammeIds } from "@/lib/calculator-ids";
import { matchRounds } from "@/lib/deadlines";
import { listProgrammes, listUniversities } from "@/lib/catalog";
import { countriesShown, hasActiveFilters, onlySupported, parseCatalogState } from "@/lib/catalog-query";
import { buildCatalogView } from "@/lib/catalog-view";
import { CatalogForm } from "./CatalogForm";
import { ProgrammeCard } from "@/components/ProgrammeCard";
import { FilterSidebar, LevelTabs, LoadMore, SearchAndSort, SurveyCard } from "./CatalogControls";

// Каталог обновляет Python-конвейер напрямую в базе, мимо Next.js —
// без этого страница закаменеет на состоянии последней сборки. Сами данные
// при этом берутся из памяти сервера и обновляются раз в пять минут
// (src/lib/server-memo.ts): страница собирается на каждый запрос, но базу
// на каждый щелчок по фильтру не трогает.
export const dynamic = "force-dynamic";

// canonical — всегда на страницу без параметров фильтра, независимо от
// того, что нафильтровал пользователь: иначе каждая комбинация фильтров
// (а их сотни) — отдельный "дублирующийся" для поисковика документ.
export async function generateMetadata({ params }: PageProps<"/[locale]/programmes">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  return {
    title: dict.catalog.title,
    description: dict.catalog.subtitle,
    alternates: buildAlternates("/programmes", locale),
  };
}

export default async function ProgrammesPage({
  params,
  searchParams,
}: PageProps<"/[locale]/programmes">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  // Фильтр «Страна»: по умолчанию каталог показывает общий список всех
  // открытых стран, можно выбрать одну (решения владельца 2026-10-10).
  // Разделы сайта при этом остаются по странам: карточка ведёт на страницу
  // программы в разделе её страны.
  const own = countryOf(locale);
  const parsed = parseCatalogState(await searchParams);
  const shown = countriesShown(parsed, own);
  const profile = catalogProfile(shown);
  const state = onlySupported(parsed, profile.filters);
  // У какой-то из открытых стран есть фильтры (плата, только бюджет),
  // которых в этом списке нет, — об этом говорит строка под фильтром
  // «Страна»: чтобы ими пользоваться, нужно выбрать эту страну.
  const filtersDropped = countries.some((country) =>
    countryProfile(country).filters.some((filter) => !profile.filters.includes(filter)),
  );
  const dict = await getDictionary(locale);

  // Все фильтры считаются в памяти по списку программ страны, который
  // сервер держит у себя (listProgrammes в src/lib/catalog.ts): каталог —
  // тысячи строк, не миллионы, а счётчики вкладок получаются тем же проходом.
  // Запросы идут по каждой стране отдельно и одновременно: у стран разные
  // таблицы направлений и формул, а фильтр по городу или вузу одной страны у
  // другой просто ничего не находит.
  const filters = {
    budgetOnly: state.budgetOnly,
    cities: state.cities,
    interests: state.interests,
    language: state.language,
    mode: state.mode,
    university: state.university,
    kind: state.kind ?? undefined,
  };
  const [programmeLists, universityLists, applicationRounds, calculatorIdSets] = await Promise.all([
    Promise.all(shown.map((country) => listProgrammes(country, filters))),
    Promise.all(shown.map((country) => listUniversities(country))),
    getApplicationRoundsForCards(),
    Promise.all(shown.map((country) => getCalculatorProgrammeIds(country))),
  ]);
  const programmes = programmeLists.flat();
  const universityGroups = shown.map((country, index) => ({ country, universities: universityLists[index] }));
  const calculatorIds = new Set(calculatorIdSets.flatMap((ids) => [...ids]));
  const view = buildCatalogView(programmes, state, languageOf(locale));

  return (
    <main className="page-container pb-16">
      <section className="flex flex-col gap-6 pb-8 pt-8 sm:pt-12 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <h1 className="text-4xl font-bold leading-[1.1] tracking-[-0.025em] text-zinc-900 lg:text-[44px]">
            {dict.catalog.title}
          </h1>
          <p className="mt-2.5 text-[17px] leading-relaxed text-zinc-600">{dict.catalog.subtitle}</p>
        </div>
        {hasFeature(locale, "survey") && <SurveyCard locale={locale} dict={dict} />}
      </section>

      {/* Одна GET-форма на весь каталог (поиск + фильтры). Поля и карточки
          рисует сервер; CatalogForm — тонкая клиентская обёртка, которая
          применяет фильтр сразу при изменении. Сортировка, табы и "показать
          ещё" — обычные ссылки на тот же адрес с другими параметрами. */}
      <CatalogForm
        action={`/${locale}/programmes`}
        className="grid gap-4 lg:grid-cols-[300px_minmax(0,1fr)] lg:gap-8"
      >
        <div className="space-y-4 lg:space-y-0">
          <FilterSidebar
            locale={locale}
            dict={dict}
            state={state}
            profile={profile}
            universityGroups={universityGroups}
            filtersDropped={filtersDropped}
          />
        </div>

        <div className="min-w-0 space-y-5">
          <SearchAndSort locale={locale} dict={dict} state={state} />
          <LevelTabs locale={locale} dict={dict} state={state} view={view} levels={profile.levels} />

          {view.visible.length === 0 ? (
            <div className="surface p-10 text-center">
              <p className="text-zinc-700">
                {hasActiveFilters(state) ? dict.catalog.emptyFiltered : dict.catalog.empty}
              </p>
              {hasActiveFilters(state) && (
                <Link
                  href={`/${locale}/programmes`}
                  className="mt-4 inline-flex h-10 items-center rounded-full bg-zinc-200 px-5 text-sm font-medium text-zinc-900 hover:bg-zinc-300"
                >
                  {dict.catalog.clearFilters}
                </Link>
              )}
            </div>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {view.visible.map((programme) => {
                  // Только ближайший подходящий раунд с известной датой закрытия —
                  // полный перечень окон уместнее на странице самой программы.
                  const nextRound = matchRounds(
                    applicationRounds,
                    programme.university_id,
                    programme.degree_level,
                    programme.language_of_instruction,
                  ).find((round) => round.closesOn !== null);

                  return (
                    <ProgrammeCard
                      key={programme.id}
                      locale={locale}
                      dict={dict}
                      programme={programme}
                      showCountry={shown.length > 1}
                      hasCalculator={calculatorIds.has(programme.id)}
                      deadline={
                        nextRound
                          ? `${dict.programme.deadlinesCloses} ${new Date(nextRound.closesOn!).toLocaleDateString(languageOf(locale))}`
                          : null
                      }
                    />
                  );
                })}
              </div>
              <LoadMore locale={locale} dict={dict} state={state} view={view} />
            </>
          )}
        </div>
      </CatalogForm>
    </main>
  );
}
