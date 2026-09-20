import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";

// Тексты — в словарях (rights.*), у каждого пункта указан пункт нормы; сверка
// с дословным текстом норм — docs/checks/RIGHTS-PAGE-SOURCES.md. Страница
// статическая и лёгкая: ни HeroUI, ни "use client" (правило 4 CLAUDE.md).
export async function generateMetadata({ params }: PageProps<"/[locale]/rights">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  return {
    title: dict.rights.title,
    description: dict.rights.intro,
    alternates: buildAlternates("/rights", locale),
  };
}

export default async function RightsPage({ params }: PageProps<"/[locale]/rights">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const { rights } = await getDictionary(locale);

  return (
    <main className="page-container py-8 sm:py-12">
      <div className="surface mx-auto max-w-3xl p-6 sm:p-10">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900">{rights.title}</h1>
        <p className="mt-2 max-w-2xl text-zinc-600">{rights.intro}</p>
        <p className="mt-4 text-sm text-zinc-600">{rights.checkedNote}</p>
        <p className="mt-3">
          <Link href={`/${locale}/glossary`} className="text-brand underline">
            {rights.glossaryLink}
          </Link>
        </p>

        <ol className="mt-8 divide-y divide-zinc-200">
          {rights.items.map((item) => (
            <li key={item.id} className="py-5">
              <h2 className="text-lg font-semibold text-zinc-900">{item.title}</h2>
              <p className="mt-1 text-zinc-700">{item.text}</p>
              <p className="mt-2 text-sm text-zinc-600">
                {rights.sourceLabel}: {item.source}
              </p>
            </li>
          ))}
        </ol>

        <h2 className="mt-8 text-lg font-semibold text-zinc-900">{rights.sourcesTitle}</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          {rights.sources.map((source) => (
            <li key={source.url}>
              <a href={source.url} className="text-brand underline" rel="noopener noreferrer">
                {source.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
