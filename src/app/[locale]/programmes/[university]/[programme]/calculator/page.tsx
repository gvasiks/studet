import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { getProgramme, localizedName } from "@/lib/catalog";
import { getFormula, getLevelCoefficients } from "@/lib/formula-queries";
import { buildAlternates } from "@/lib/site";
import { CalculatorForm } from "./CalculatorForm";

type Params = PageProps<"/[locale]/programmes/[university]/[programme]/calculator">["params"];

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { locale, university, programme: programmeSlug } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  const record = await getProgramme(university, programmeSlug);
  if (!record) notFound();

  const name = localizedName(record, locale);
  const path = `/programmes/${university}/${programmeSlug}/calculator`;
  return {
    title: { absolute: `${dict.calculator.title} — ${name}` },
    alternates: buildAlternates(path, locale),
  };
}

export default async function CalculatorPage({ params }: { params: Params }) {
  const { locale, university, programme: programmeSlug } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  const record = await getProgramme(university, programmeSlug);
  if (!record) notFound();

  const formula = await getFormula(record.id);
  const levelCoefficients = await getLevelCoefficients();

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <Link
        href={`/${locale}/programmes/${university}/${programmeSlug}`}
        className="text-sm text-zinc-500 hover:underline"
      >
        {dict.programme.backToCatalog}
      </Link>

      <p className="mt-4 text-sm text-zinc-500">{localizedName(record, locale)}</p>
      <h1 className="mt-1 text-2xl font-bold tracking-tighter text-zinc-900">{dict.calculator.title}</h1>

      {!formula ? (
        <p className="mt-8 text-zinc-600">{dict.calculator.notAvailable}</p>
      ) : (
        <CalculatorForm
          dict={dict}
          terms={formula.terms}
          gates={formula.gates}
          levelCoefficients={levelCoefficients}
          sourceUrl={formula.sourceUrl}
          verifiedAt={formula.verifiedAt}
          locale={locale}
        />
      )}
    </main>
  );
}
