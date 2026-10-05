import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { countryOf, isLocale, languageOf } from "@/i18n/config";
import { hasFeature } from "@/lib/country";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import { SourceLine } from "@/components/SourceLine";
import { ArrowRightIcon } from "@/components/icons";

// Определения — в словарях (glossary.*); у каждого указан источник (правило 5
// CLAUDE.md: никакого факта без источника). Страница лёгкая: без HeroUI и
// без "use client" (правило 4).
export async function generateMetadata({ params }: PageProps<"/[locale]/glossary">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  if (!hasFeature(countryOf(locale), "glossary")) notFound();

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
  if (!hasFeature(countryOf(locale), "glossary")) notFound();

  const { glossary } = await getDictionary(locale);
  const items = [...glossary.items].sort((a, b) => a.term.localeCompare(b.term, languageOf(locale)));

  // Группировка по первой букве — заголовки-разделители внутри одной
  // карточки. Буквы берутся из самих терминов, поэтому это данные, а не
  // текст интерфейса (правило 1 CLAUDE.md). Отдельного алфавитного
  // указателя нет: владелец убрал его как лишний (2026-09-30).
  const groups: { letter: string; items: typeof items }[] = [];
  for (const item of items) {
    const letter = item.term.charAt(0).toLocaleUpperCase(languageOf(locale));
    const last = groups[groups.length - 1];
    if (last?.letter === letter) last.items.push(item);
    else groups.push({ letter, items: [item] });
  }

  return (
    <main className="page-container py-8 sm:py-12">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">{glossary.title}</h1>
        <p className="mt-3 max-w-[65ch] text-lg leading-relaxed text-zinc-600">{glossary.intro}</p>
        <Link
          href={`/${locale}/rights`}
          className="mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-brand-dark hover:text-brand"
        >
          {glossary.rightsLink}
          <ArrowRightIcon size={14} />
        </Link>
      </header>

      <div className="mt-8 lg:mt-10">
        <div className="surface p-6 sm:p-10">
          {groups.map((group, groupIndex) => (
            <section key={group.letter}>
              <h2
                aria-hidden="true"
                className={`flex items-center gap-3 text-xs font-bold uppercase tracking-[0.2em] text-brand ${
                  groupIndex === 0 ? "" : "mt-10"
                }`}
              >
                {group.letter}
                <span className="h-px flex-1 bg-zinc-100" />
              </h2>
              <dl className="mt-4 divide-y divide-zinc-100">
                {group.items.map((item) => (
                  <div key={item.id} id={item.id} className="scroll-mt-24 py-6 first:pt-0 last:pb-0">
                    {/* Ссылка на сам термин: карточки программ ссылаются сюда
                        по #id, и человеку тоже нужно чем-то поделиться. */}
                    <dt id={`${item.id}-term`} className="group flex items-baseline gap-2">
                      <a
                        href={`#${item.id}`}
                        aria-labelledby={`${item.id}-term`}
                        className="text-lg font-semibold tracking-tight text-zinc-900 hover:text-brand"
                      >
                        {item.term}
                      </a>
                      <span
                        aria-hidden="true"
                        className="text-sm text-zinc-300 opacity-0 transition-opacity group-hover:opacity-100"
                      >
                        #
                      </span>
                    </dt>
                    <dd className="mt-2 max-w-[62ch] leading-relaxed text-zinc-700">{item.definition}</dd>
                    <dd>
                      <SourceLine label={glossary.sourceLabel} value={item.source} />
                    </dd>
                  </div>
                ))}
              </dl>
            </section>
          ))}
        </div>
      </div>
    </main>
  );
}
