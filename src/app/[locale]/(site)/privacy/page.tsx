import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import { fillPlaceholders, getPrivacyContact, groupBody } from "@/lib/privacy";

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
      <div className="surface mx-auto max-w-3xl p-6 sm:p-10">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900">{privacy.title}</h1>
        <p className="mt-2 max-w-2xl text-zinc-600">{privacy.intro}</p>
        <p className="mt-2 text-sm text-zinc-600">{privacy.updated}</p>

        {privacy.sections.map((section) => (
          <section key={section.id} id={section.id} className="mt-8 scroll-mt-24">
            <h2 className="text-lg font-semibold text-zinc-900">{section.title}</h2>
            {groupBody(section.body).map((block, index) =>
              block.type === "ul" ? (
                <ul key={index} className="mt-2 list-disc space-y-1 pl-5 text-zinc-700">
                  {block.items.map((item) => (
                    <li key={item}>{fillPlaceholders(item, contact)}</li>
                  ))}
                </ul>
              ) : (
                <p key={index} className="mt-2 text-zinc-700">
                  {fillPlaceholders(block.text, contact)}
                </p>
              ),
            )}
          </section>
        ))}

        <p className="mt-8">
          <a href={privacy.authorityUrl} className="text-brand underline" rel="noopener noreferrer">
            {privacy.authorityLabel}
          </a>
        </p>
      </div>
    </main>
  );
}
