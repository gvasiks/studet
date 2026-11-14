import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { countryOf, isLocale, languageOf } from "@/i18n/config";
import { hasFeature } from "@/lib/country";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import { localizedName } from "@/lib/names";
import { getCountryDocumentLists } from "@/lib/foreign-cost-queries";
import { ForeignDocuments } from "@/components/ForeignDocuments";
import { ClipboardCheckIcon } from "@/components/icons";

// Списки документов всех вузов на одной странице (docs/PLAN-FOREIGNERS.md,
// шаг 3, второй выпуск). Только Латвия (раздел "studentDocuments" есть лишь в
// профиле LV), четыре языка. Те же подтверждённые строки, что на карточке
// программы, и тот же блок; отметки общие с карточкой — ключ хранения один
// (вуз + уровень). Серверная страница: клиентский только островок с галочками.
export async function generateMetadata({ params }: PageProps<"/[locale]/student-documents">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  if (!hasFeature(locale, "studentDocuments")) notFound();

  const dict = await getDictionary(locale);
  return {
    title: dict.studentDocuments.title,
    description: dict.studentDocuments.intro,
    alternates: buildAlternates("/student-documents", locale),
  };
}

export default async function StudentDocumentsPage({ params }: PageProps<"/[locale]/student-documents">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  if (!hasFeature(locale, "studentDocuments")) notFound();

  const dict = await getDictionary(locale);
  const language = languageOf(locale);
  const t = dict.studentDocuments;
  const lists = await getCountryDocumentLists(countryOf(locale));

  // вуз → его уровни, в порядке запроса
  const universities: { slug: string; name: string; lists: typeof lists }[] = [];
  for (const list of lists) {
    let entry = universities.find((university) => university.slug === list.university.slug);
    if (!entry) {
      entry = { slug: list.university.slug, name: localizedName(list.university, language), lists: [] };
      universities.push(entry);
    }
    entry.lists.push(list);
  }

  return (
    <main className="page-container py-8 sm:py-12">
      <header className="mx-auto max-w-3xl lg:mx-0 lg:max-w-none">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">{t.title}</h1>
        <p className="mt-3 text-lg leading-relaxed text-zinc-600">{t.intro}</p>
        <p className="mt-5 flex items-start gap-2 rounded-2xl bg-brand-soft px-4 py-2.5 text-xs leading-relaxed text-zinc-700">
          <ClipboardCheckIcon size={14} className="mt-0.5 shrink-0 text-brand" />
          <span>
            {language !== "en" && <>{dict.programme.foreignDocuments.notesLanguage} </>}
            {dict.programme.foreignDocuments.more}
          </span>
        </p>
      </header>

      {universities.length === 0 ? (
        <p className="mt-8 text-sm text-zinc-600">{t.empty}</p>
      ) : (
        <>
          <nav aria-labelledby="student-documents-toc" className="mt-8">
            <h2 id="student-documents-toc" className="text-xs uppercase tracking-wide text-zinc-600">
              {t.tocTitle}
            </h2>
            <ul className="mt-2 flex flex-wrap gap-2">
              {universities.map((university) => (
                <li key={university.slug}>
                  <a
                    href={`#${university.slug}`}
                    className="inline-block rounded-full border border-zinc-200 px-3 py-1.5 text-sm text-zinc-800 hover:border-brand hover:text-brand-dark"
                  >
                    {university.name}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          {universities.map((university) => (
            <section key={university.slug} id={university.slug} className="mt-10 scroll-mt-24" aria-labelledby={`${university.slug}-name`}>
              <h2 id={`${university.slug}-name`} className="text-2xl font-semibold tracking-tight text-zinc-900">
                {university.name}
              </h2>
              {university.lists.map((list) => (
                <ForeignDocuments
                  key={list.degreeLevel}
                  dict={dict}
                  language={language}
                  universitySlug={university.slug}
                  degreeLevel={list.degreeLevel}
                  items={list.items}
                  english={list.english}
                  heading={dict.catalog.degreeLevel[list.degreeLevel as keyof typeof dict.catalog.degreeLevel] ?? list.degreeLevel}
                  headingId={`${university.slug}-${list.degreeLevel}`}
                  englishByProgramme={
                    list.englishByProgramme
                      ? `/${locale}/programmes?language=en&university=${university.slug}&level=${list.degreeLevel}`
                      : null
                  }
                />
              ))}
            </section>
          ))}
        </>
      )}
    </main>
  );
}
