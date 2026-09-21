import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { getMatchData } from "@/lib/match-queries";
import { buildAlternates } from "@/lib/site";
import { ArrowRightIcon } from "@/components/icons";
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
      {/* Заголовок на сером фоне: ввод и результаты — два разных блока, и
          общая карточка вокруг них склеивала бы вопрос с ответом. */}
      <header className="mx-auto max-w-5xl">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">{dict.match.title}</h1>
        <p className="mt-3 max-w-[65ch] text-lg leading-relaxed text-zinc-600">{dict.match.intro}</p>
      </header>

      <div className="mx-auto mt-8 max-w-5xl">
        {formulas.length === 0 ? (
          <div className="surface p-6 sm:p-10">
            <p className="text-zinc-700">{dict.match.emptyNoFormulas}</p>
            <Link
              href={`/${locale}/programmes`}
              className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-brand hover:text-brand-dark"
            >
              {dict.nav.catalog}
              <ArrowRightIcon size={14} />
            </Link>
          </div>
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
