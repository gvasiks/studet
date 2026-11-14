import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { hasFeature } from "@/lib/country";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import { LegalItems } from "@/components/LegalItems";
import { ArrowRightIcon, ClipboardCheckIcon } from "@/components/icons";

// Тексты — в словарях (rights.*), у каждого пункта указан пункт нормы; сверка
// с дословным текстом норм — docs/checks/RIGHTS-PAGE-SOURCES.md. Страница
// статическая и лёгкая: ни HeroUI, ни "use client" (правило 4 CLAUDE.md).
export async function generateMetadata({ params }: PageProps<"/[locale]/rights">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  if (!hasFeature(locale, "rights")) notFound();

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
  if (!hasFeature(locale, "rights")) notFound();

  const { rights } = await getDictionary(locale);

  return (
    <main className="page-container py-8 sm:py-12">
      {/* Заголовок лежит на сером фоне, а не внутри карточки: тринадцать
          пунктов — длинный документ, и ему нужно вступление, отделённое от
          содержания. */}
      <header className="mx-auto max-w-3xl lg:mx-0 lg:max-w-none">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">{rights.title}</h1>
        {/* Вступление и плашка — на всю ширину, ссылка на словарь под ними
            (правка владельца 2026-09-30). */}
        <p className="mt-3 text-lg leading-relaxed text-zinc-600">{rights.intro}</p>
        <p className="mt-5 flex items-start gap-2 rounded-2xl bg-brand-soft px-4 py-2.5 text-xs leading-relaxed text-zinc-700">
          <ClipboardCheckIcon size={14} className="mt-0.5 shrink-0 text-brand" />
          <span>{rights.checkedNote}</span>
        </p>
        <Link
          href={`/${locale}/glossary`}
          className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-brand-dark hover:text-brand"
        >
          {rights.glossaryLink}
          <ArrowRightIcon size={14} />
        </Link>
      </header>

      <LegalItems
        headingId="rights-heading"
        title={rights.title}
        items={rights.items}
        sourceLabel={rights.sourceLabel}
        sourcesTitle={rights.sourcesTitle}
        sources={rights.sources}
      />
    </main>
  );
}
