import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { enumLabel, listProgrammes, localizedName } from "@/lib/catalog";

// Каталог обновляет Python-конвейер напрямую в базе, мимо Next.js —
// без этого страница закаменеет на состоянии последней сборки.
export const dynamic = "force-dynamic";

export default async function ProgrammesPage({ params }: PageProps<"/[locale]/programmes">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  const programmes = await listProgrammes();

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">{dict.catalog.title}</h1>
      <p className="mt-2 text-zinc-600">{dict.catalog.subtitle}</p>

      {programmes.length === 0 ? (
        <p className="mt-8 text-zinc-500">{dict.catalog.empty}</p>
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
