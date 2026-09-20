import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";

// Определения — в словарях (glossary.*); у каждого указан источник (правило 5
// CLAUDE.md: никакого факта без источника). Страница лёгкая: без HeroUI и
// без "use client" (правило 4).
export async function generateMetadata({ params }: PageProps<"/[locale]/glossary">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  return {
    title: dict.glossary.title,
    description: dict.glossary.intro,
    alternates: buildAlternates("/glossary", locale),
  };
}

export default async function GlossaryPage({ params }: PageProps<"/[locale]/glossary">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const { glossary } = await getDictionary(locale);
  const items = [...glossary.items].sort((a, b) => a.term.localeCompare(b.term, locale));

  return (
    <main className="page-container py-8 sm:py-12">
      <div className="surface mx-auto max-w-3xl p-6 sm:p-10">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900">{glossary.title}</h1>
        <p className="mt-2 max-w-2xl text-zinc-600">{glossary.intro}</p>
        <p className="mt-3">
          <Link href={`/${locale}/rights`} className="text-brand underline">
            {glossary.rightsLink}
          </Link>
        </p>

        <dl className="mt-8 divide-y divide-zinc-200">
          {items.map((item) => (
            <div key={item.id} id={item.id} className="scroll-mt-24 py-5">
              <dt className="text-lg font-semibold text-zinc-900">{item.term}</dt>
              <dd className="mt-1 text-zinc-700">{item.definition}</dd>
              <dd className="mt-2 text-sm text-zinc-600">
                {glossary.sourceLabel}: {item.source}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </main>
  );
}
