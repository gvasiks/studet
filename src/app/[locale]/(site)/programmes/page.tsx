import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { countryOf, isLocale, languageOf } from "@/i18n/config";
import { hasFeature } from "@/lib/country";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import { getApplicationRounds } from "@/lib/deadline-queries";
import { getCalculatorProgrammeIds } from "@/lib/calculator-ids";
import { matchRounds } from "@/lib/deadlines";
import { listProgrammes, listUniversities } from "@/lib/catalog";
import { hasActiveFilters, parseCatalogState } from "@/lib/catalog-query";
import { buildCatalogView } from "@/lib/catalog-view";
import { CatalogForm } from "./CatalogForm";
import { ProgrammeCard } from "@/components/ProgrammeCard";
import { FilterSidebar, LevelTabs, LoadMore, SearchAndSort, SurveyCard } from "./CatalogControls";

// Каталог обновляет Python-конвейер напрямую в базе, мимо Next.js —
// без этого страница закаменеет на состоянии последней сборки.
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

  const state = parseCatalogState(await searchParams);
  const dict = await getDictionary(locale);

  // В базе — только то, что нельзя сделать быстрее в памяти: город, язык,
  // направление... Поиск, уровень, сортировка и "показать ещё" считаются
  // по уже выбранному набору (каталог — сотни строк, не миллионы), иначе
  // счётчики табов пришлось бы получать отдельными запросами.
  const [programmes, universities, applicationRounds, calculatorIds] = await Promise.all([
    listProgrammes(countryOf(locale), {
      budgetOnly: state.budgetOnly,
      cities: state.cities,
      interests: state.interests,
      language: state.language,
      mode: state.mode,
      university: state.university,
      kind: state.kind ?? undefined,
    }),
    listUniversities(countryOf(locale)),
    getApplicationRounds(),
    getCalculatorProgrammeIds(countryOf(locale)),
  ]);
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
          <FilterSidebar locale={locale} dict={dict} state={state} universities={universities} />
        </div>

        <div className="min-w-0 space-y-5">
          <SearchAndSort locale={locale} dict={dict} state={state} />
          <LevelTabs locale={locale} dict={dict} state={state} view={view} />

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
