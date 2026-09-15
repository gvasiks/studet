import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import {
  CITY_KEYS,
  enumLabel,
  listProgrammes,
  listUniversities,
  localizedName,
  type ProgrammeFilters,
} from "@/lib/catalog";

// Каталог обновляет Python-конвейер напрямую в базе, мимо Next.js —
// без этого страница закаменеет на состоянии последней сборки.
export const dynamic = "force-dynamic";

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

// Города приходят в двух форматах: одной строкой через запятую (ссылка
// из анкеты, SurveyWizard.tsx) или несколькими одноимёнными параметрами
// (форма фильтра ниже — несколько чекбоксов с name="city" в GET-запросе
// дают city=riga&city=jelgava, а не одну строку).
function cityValues(value: string | string[] | undefined): string[] {
  if (!value) return [];
  const parts = Array.isArray(value) ? value : [value];
  return parts.flatMap((part) => part.split(",")).filter(Boolean);
}

export default async function ProgrammesPage({
  params,
  searchParams,
}: PageProps<"/[locale]/programmes">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const sp = await searchParams;
  const cities = cityValues(sp.city);
  const languageParam = firstValue(sp.language);
  const modeParam = firstValue(sp.mode);
  const universityParam = firstValue(sp.university);
  const budgetOnly = firstValue(sp.budget) === "1";

  const filters: ProgrammeFilters = {
    budgetOnly,
    cities,
    language: languageParam,
    mode: modeParam,
    university: universityParam,
  };
  const hasFilters =
    budgetOnly || cities.length > 0 || Boolean(languageParam) || Boolean(modeParam) || Boolean(universityParam);

  const dict = await getDictionary(locale);
  const [programmes, universities] = await Promise.all([listProgrammes(filters), listUniversities()]);
  const selectedUniversity = universities.find((u) => u.slug === universityParam);

  const summaryParts = [
    budgetOnly ? dict.survey.funding.budgetOnly : null,
    ...cities.map((city) => enumLabel(dict.catalog.city, city)),
    languageParam ? enumLabel(dict.catalog.language, languageParam) : null,
    modeParam ? enumLabel(dict.catalog.studyMode, modeParam) : null,
    selectedUniversity ? localizedName(selectedUniversity, locale) : null,
  ].filter((part): part is string => part !== null);

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tighter text-zinc-900">{dict.catalog.title}</h1>
          <p className="mt-2 text-zinc-600">{dict.catalog.subtitle}</p>
        </div>
        <Link
          href={`/${locale}/survey`}
          className="shrink-0 rounded-full border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50"
        >
          {dict.catalog.surveyTeaser} {dict.catalog.surveyCta}
        </Link>
      </div>

      {/* Обычная GET-форма, без клиентского JS — правило 4 CLAUDE.md
          (публичные страницы остаются серверными и лёгкими, HeroUI только
          там, где есть интерактив вроде анкеты). Перезагрузка страницы
          при отправке — приемлемая цена за нулевой JS на странице каталога. */}
      <form className="mt-6 flex flex-wrap items-end gap-x-5 gap-y-4 rounded-xl border border-zinc-200 p-4">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-zinc-600">{dict.catalog.filters.university}</span>
          <select
            name="university"
            defaultValue={universityParam ?? ""}
            className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-900"
          >
            <option value="">{dict.catalog.filters.anyUniversity}</option>
            {universities.map((university) => (
              <option key={university.slug} value={university.slug}>
                {localizedName(university, locale)}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm">
          <span className="text-zinc-600">{dict.catalog.filters.language}</span>
          <select
            name="language"
            defaultValue={languageParam ?? ""}
            className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-900"
          >
            <option value="">{dict.catalog.filters.anyLanguage}</option>
            <option value="lv">{dict.catalog.language.lv}</option>
            <option value="en">{dict.catalog.language.en}</option>
          </select>
        </label>

        <label className="flex flex-col gap-1 text-sm">
          <span className="text-zinc-600">{dict.catalog.filters.mode}</span>
          <select
            name="mode"
            defaultValue={modeParam ?? ""}
            className="rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-900"
          >
            <option value="">{dict.catalog.filters.anyMode}</option>
            <option value="full_time">{dict.catalog.studyMode.full_time}</option>
            <option value="part_time">{dict.catalog.studyMode.part_time}</option>
            <option value="distance">{dict.catalog.studyMode.distance}</option>
          </select>
        </label>

        <fieldset className="flex flex-col gap-1 text-sm">
          <legend className="text-zinc-600">{dict.catalog.filters.city}</legend>
          <div className="flex max-w-xs flex-wrap gap-x-3 gap-y-1">
            {CITY_KEYS.map((city) => (
              <label key={city} className="flex items-center gap-1.5 text-zinc-800">
                <input
                  type="checkbox"
                  name="city"
                  value={city}
                  defaultChecked={cities.includes(city)}
                  className="rounded border-zinc-300 text-brand focus:ring-brand"
                />
                {enumLabel(dict.catalog.city, city)}
              </label>
            ))}
          </div>
        </fieldset>

        <label className="flex items-center gap-1.5 pb-1.5 text-sm text-zinc-800">
          <input
            type="checkbox"
            name="budget"
            value="1"
            defaultChecked={budgetOnly}
            className="rounded border-zinc-300 text-brand focus:ring-brand"
          />
          {dict.catalog.filters.budgetOnly}
        </label>

        <button
          type="submit"
          className="rounded-full bg-brand px-5 py-2 text-sm font-medium text-white hover:bg-brand-dark"
        >
          {dict.catalog.filters.apply}
        </button>
      </form>

      {hasFilters && (
        <p className="mt-6 text-sm text-zinc-600">
          {dict.catalog.filtersSummary} {summaryParts.join(", ")}
          {" — "}
          <Link href={`/${locale}/programmes`} className="underline">
            {dict.catalog.clearFilters}
          </Link>
        </p>
      )}

      {programmes.length === 0 ? (
        <p className="mt-8 text-zinc-500">
          {hasFilters ? dict.catalog.emptyFiltered : dict.catalog.empty}
        </p>
      ) : (
        <ul className="mt-8 divide-y divide-zinc-200">
          {programmes.map((programme) => (
            <li key={programme.id} className="py-5">
              <Link
                href={`/${locale}/programmes/${programme.university.slug}/${programme.slug}`}
                className="text-lg font-medium text-zinc-900 hover:underline"
              >
                {localizedName(programme, locale)}
              </Link>
              <p className="mt-1 text-sm text-zinc-600">
                {localizedName(programme.university, locale)}
                {" · "}
                {enumLabel(dict.catalog.degreeLevel, programme.degree_level)}
                {" · "}
                {enumLabel(dict.catalog.language, programme.language_of_instruction)}
                {programme.duration_years !== null
                  ? ` · ${programme.duration_years} ${dict.catalog.years}`
                  : ""}
              </p>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
