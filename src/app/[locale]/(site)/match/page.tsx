import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { getMatchData } from "@/lib/match-queries";
import { buildAlternates } from "@/lib/site";
import { MatchForm } from "./MatchForm";

// Данные — подтверждённые формулы: их подтверждают людьми уже после сборки
// (как и /programmes, страница не может закаменеть на состоянии билда)
export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: PageProps<"/[locale]/match">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  return {
    title: dict.match.title,
    description: dict.match.intro,
    alternates: buildAlternates("/match", locale),
  };
}

export default async function MatchPage({ params }: PageProps<"/[locale]/match">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  const { formulas, levelCoefficients, isFixture } = await getMatchData(locale);

  return (
    <main className="page-container py-8 sm:py-12">
      <div className="surface mx-auto max-w-3xl p-6 sm:p-10">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900">{dict.match.title}</h1>
        <p className="mt-2 max-w-2xl text-zinc-600">{dict.match.intro}</p>

        {formulas.length === 0 ? (
          <>
            <p className="mt-8 text-zinc-700">{dict.match.emptyNoFormulas}</p>
            <Link
              href={`/${locale}/programmes`}
              className="mt-4 inline-block text-brand underline"
            >
              {dict.nav.catalog}
            </Link>
          </>
        ) : (
          <MatchForm
            dict={dict}
            locale={locale}
            formulas={formulas}
            levelCoefficients={levelCoefficients}
            isFixture={isFixture}
          />
        )}
      </div>
    </main>
  );
}
