import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import { fillPlaceholders, getPrivacyContact, groupBody } from "@/lib/privacy";
import { ArrowRightIcon, CalendarIcon } from "@/components/icons";

// Текст политики — в словарях (privacy.*); что она обещает и что должно быть
// правдой к публикации — docs/PRIVACY-CHECKLIST.md. Страница лёгкая: без
// HeroUI и без "use client" (правило 4 CLAUDE.md).
export async function generateMetadata({ params }: PageProps<"/[locale]/privacy">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  return {
    title: dict.privacy.title,
    description: dict.privacy.intro,
    alternates: buildAlternates("/privacy", locale),
  };
}

export default async function PrivacyPage({ params }: PageProps<"/[locale]/privacy">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const { privacy } = await getDictionary(locale);
  const contact = getPrivacyContact();

  return (
    <main className="page-container py-8 sm:py-12">
      <header className="mx-auto max-w-3xl lg:mx-0 lg:max-w-none">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">{privacy.title}</h1>
        <p className="mt-3 max-w-[65ch] text-lg leading-relaxed text-zinc-600">{privacy.intro}</p>
        {/* Дата редакции — не сноска, а часть удостоверения документа:
            у политики это первое, что проверяют. */}
        <p className="mt-5 inline-flex items-center gap-2 rounded-full bg-white px-3.5 py-1.5 text-xs font-medium text-zinc-600 shadow-pill">
          <CalendarIcon size={13} className="text-zinc-500" />
          {privacy.updated}
        </p>
      </header>

      <div className="mt-8 flex flex-col gap-8 lg:mt-10 lg:flex-row lg:items-start lg:gap-10">
        {/* Тринадцать разделов: без оглавления найти нужный пункт нельзя,
            а именно за конкретным пунктом сюда и приходят. */}
        <nav
          aria-labelledby="privacy-toc"
          className="hidden shrink-0 lg:sticky lg:top-24 lg:block lg:w-64"
        >
          <p id="privacy-toc" className="sr-only">
            {privacy.title}
          </p>
          <ol className="space-y-1">
            {privacy.sections.map((section, index) => (
              <li key={section.id}>
                <a
                  href={`#${section.id}`}
                  className="flex gap-2.5 rounded-xl px-3 py-2 text-sm leading-snug text-zinc-600 hover:bg-white hover:text-zinc-900"
                >
                  <span className="w-4 shrink-0 text-right text-xs tabular-nums text-zinc-600">{index + 1}</span>
                  <span className="line-clamp-2">{section.title}</span>
                </a>
              </li>
            ))}
          </ol>
        </nav>

        <div className="min-w-0 flex-1">
          <div className="surface divide-y divide-zinc-100 p-6 sm:p-10">
            {privacy.sections.map((section, index) => (
              <section key={section.id} id={section.id} className="scroll-mt-24 py-7 first:pt-0 last:pb-0">
                <h2 className="flex gap-3 text-lg font-semibold leading-snug tracking-tight text-zinc-900">
                  <span aria-hidden="true" className="w-5 shrink-0 text-right text-sm tabular-nums text-zinc-500">
                    {index + 1}
                  </span>
                  {section.title}
                </h2>
                <div className="mt-3 max-w-[62ch] space-y-3 pl-0 sm:pl-8">
                  {groupBody(section.body).map((block, blockIndex) =>
                    block.type === "ul" ? (
                      <ul key={blockIndex} className="space-y-2">
                        {block.items.map((item) => (
                          <li key={item} className="flex gap-2.5 leading-relaxed text-zinc-700">
                            <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand/40" />
                            <span>{fillPlaceholders(item, contact)}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p key={blockIndex} className="leading-relaxed text-zinc-700">
                        {fillPlaceholders(block.text, contact)}
                      </p>
                    ),
                  )}
                </div>
              </section>
            ))}
          </div>

          {/* Куда жаловаться — не ссылка в конце текста, а отдельный выход:
              человек, который сюда дошёл, уже чем-то недоволен. */}
          <a
            href={privacy.authorityUrl}
            rel="noopener noreferrer"
            className="mt-6 flex items-center justify-between gap-4 rounded-3xl border border-zinc-200 bg-white/60 p-6 text-sm font-medium text-zinc-900 hover:border-brand hover:text-brand sm:p-8"
          >
            {privacy.authorityLabel}
            <ArrowRightIcon size={16} className="shrink-0" />
          </a>
        </div>
      </div>
    </main>
  );
}
