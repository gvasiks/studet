import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { enumLabel, listProgrammes, localizedName, type ProgrammeFilters } from "@/lib/catalog";

// Каталог обновляет Python-конвейер напрямую в базе, мимо Next.js —
// без этого страница закаменеет на состоянии последней сборки.
export const dynamic = "force-dynamic";

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function ProgrammesPage({
  params,
  searchParams,
}: PageProps<"/[locale]/programmes">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const sp = await searchParams;
  const cityParam = firstValue(sp.city);
  const languageParam = firstValue(sp.language);
  const modeParam = firstValue(sp.mode);
  const budgetOnly = firstValue(sp.budget) === "1";
  const cities = cityParam ? cityParam.split(",").filter(Boolean) : [];

  const filters: ProgrammeFilters = {
    budgetOnly,
    cities,
    language: languageParam,
    mode: modeParam,
  };
  const hasFilters = budgetOnly || cities.length > 0 || Boolean(languageParam) || Boolean(modeParam);

  const dict = await getDictionary(locale);
  const programmes = await listProgrammes(filters);

  const summaryParts = [
    budgetOnly ? dict.survey.funding.budgetOnly : null,
    ...cities.map((city) => enumLabel(dict.catalog.city, city)),
    languageParam ? enumLabel(dict.catalog.language, languageParam) : null,
    modeParam ? enumLabel(dict.catalog.studyMode, modeParam) : null,
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
