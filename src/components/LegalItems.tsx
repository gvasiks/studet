import { SourceLine } from "@/components/SourceLine";
import { ArrowRightIcon } from "@/components/icons";

// Пронумерованные пункты с нормой под каждым, оглавление сбоку и список
// актов внизу. Общий для /rights и /student-permit: обе страницы — длинный
// документ, где у каждого факта своя норма (правило 5 CLAUDE.md). Серверный,
// без "use client" (правило 4).

type Item = { id: string; title: string; text: string; source: string };
type Source = { label: string; url: string };

export function LegalItems({
  headingId,
  title,
  items,
  sourceLabel,
  sourcesTitle,
  sources,
}: {
  /** id скрытого заголовка оглавления — свой у каждой страницы */
  headingId: string;
  title: string;
  items: readonly Item[];
  sourceLabel: string;
  sourcesTitle: string;
  sources: readonly Source[];
}) {
  return (
    <div className="mt-8 flex flex-col gap-8 lg:mt-10 lg:flex-row lg:items-start lg:gap-10">
      {/* Оглавление: длинный список пунктов без него — стена, по которой
          нельзя вернуться к нужному. Номера дают пунктам адресуемость. */}
      <nav aria-labelledby={headingId} className="hidden shrink-0 lg:sticky lg:top-24 lg:block lg:w-64">
        <p id={headingId} className="sr-only">
          {title}
        </p>
        <ol className="space-y-1">
          {items.map((item, index) => (
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
          {items.map((item, index) => (
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
                  <SourceLine label={sourceLabel} value={item.source} />
                </div>
              </div>
            </li>
          ))}
        </ol>

        {/* Список норм — справочный материал, а не содержание: отдельная
            карточка поскромнее, чтобы не конкурировала с пунктами. */}
        <section className="mt-6 rounded-3xl border border-zinc-200 bg-white/60 p-6 sm:p-8">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-500">{sourcesTitle}</h2>
          <ul className="mt-4 space-y-2.5">
            {sources.map((source) => (
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
  );
}
