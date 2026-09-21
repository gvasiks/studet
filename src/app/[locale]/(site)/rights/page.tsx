import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import { SourceLine } from "@/components/SourceLine";
import { ArrowRightIcon, ClipboardCheckIcon } from "@/components/icons";

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
      {/* Заголовок лежит на сером фоне, а не внутри карточки: тринадцать
          пунктов — длинный документ, и ему нужно вступление, отделённое от
          содержания. */}
      <header className="mx-auto max-w-3xl lg:mx-0 lg:max-w-none">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">{rights.title}</h1>
        <p className="mt-3 max-w-[65ch] text-lg leading-relaxed text-zinc-600">{rights.intro}</p>
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <p className="inline-flex max-w-[60ch] items-start gap-2 rounded-2xl bg-brand-soft px-4 py-2.5 text-xs leading-relaxed text-zinc-700">
            <ClipboardCheckIcon size={14} className="mt-0.5 shrink-0 text-brand" />
            <span>{rights.checkedNote}</span>
          </p>
          <Link
            href={`/${locale}/glossary`}
            className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-dark hover:text-brand"
          >
            {rights.glossaryLink}
            <ArrowRightIcon size={14} />
          </Link>
        </div>
      </header>

      <div className="mt-8 flex flex-col gap-8 lg:mt-10 lg:flex-row lg:items-start lg:gap-10">
        {/* Оглавление: тринадцать пунктов без него — стена, по которой нельзя
            вернуться к нужному. Номера дают пунктам адресуемость. */}
        <nav
          aria-labelledby="rights-heading"
          className="hidden shrink-0 lg:sticky lg:top-24 lg:block lg:w-64"
        >
          <p id="rights-heading" className="sr-only">
            {rights.title}
          </p>
          <ol className="space-y-1">
            {rights.items.map((item, index) => (
              <li key={item.id}>
                <a
                  href={`#${item.id}`}
                  className="flex gap-2.5 rounded-xl px-3 py-2 text-sm leading-snug text-zinc-600 hover:bg-white hover:text-zinc-900"
                >
                  <span className="w-4 shrink-0 text-right text-xs tabular-nums text-zinc-600">{index + 1}</span>
                  <span className="line-clamp-2">{item.title}</span>
                </a>
              </li>
            ))}
          </ol>
        </nav>

        <div className="min-w-0 flex-1">
          <ol className="surface divide-y divide-zinc-100 p-6 sm:p-10">
            {rights.items.map((item, index) => (
              <li key={item.id} id={item.id} className="scroll-mt-24 py-7 first:pt-0 last:pb-0">
                <div className="flex gap-4 sm:gap-5">
                  <span
                    aria-hidden="true"
                    className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand-soft text-xs font-semibold tabular-nums text-brand-dark"
                  >
                    {index + 1}
                  </span>
                  <div className="min-w-0">
                    <h2 className="text-lg font-semibold leading-snug tracking-tight text-zinc-900">{item.title}</h2>
                    <p className="mt-2 max-w-[62ch] leading-relaxed text-zinc-700">{item.text}</p>
                    <SourceLine label={rights.sourceLabel} value={item.source} />
                  </div>
                </div>
              </li>
            ))}
          </ol>

          {/* Список норм — справочный материал, а не содержание: отдельная
              карточка поскромнее, чтобы не конкурировала с пунктами. */}
          <section className="mt-6 rounded-3xl border border-zinc-200 bg-white/60 p-6 sm:p-8">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">{rights.sourcesTitle}</h2>
            <ul className="mt-4 space-y-2.5">
              {rights.sources.map((source) => (
                <li key={source.url}>
                  <a
                    href={source.url}
                    rel="noopener noreferrer"
                    className="inline-flex items-baseline gap-1.5 text-sm text-brand hover:text-brand-dark hover:underline"
                  >
                    {source.label}
                    <ArrowRightIcon size={13} className="shrink-0 -rotate-45 self-center" />
                  </a>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </main>
  );
}
