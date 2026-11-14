import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { hasFeature } from "@/lib/country";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import { LegalItems } from "@/components/LegalItems";
import { ClipboardCheckIcon } from "@/components/icons";

// Путь ВНЖ для студента (docs/PLAN-FOREIGNERS.md, шаг 2). Только Латвия
// (решение Р1): раздел "studentPermit" есть лишь в профиле LV, на всех четырёх
// языках. Тексты — в словарях (studentPermit.*), у каждого пункта норма;
// сверка с дословным текстом — docs/checks/STUDENT-PERMIT-SOURCES.md.
// Сумм пошлин здесь нет: это поля правила 6, они показываются в блоке
// стоимости на карточке программы только после подтверждения человеком.
export async function generateMetadata({ params }: PageProps<"/[locale]/student-permit">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  if (!hasFeature(locale, "studentPermit")) notFound();

  const dict = await getDictionary(locale);
  return {
    title: dict.studentPermit.title,
    description: dict.studentPermit.intro,
    alternates: buildAlternates("/student-permit", locale),
  };
}

export default async function StudentPermitPage({ params }: PageProps<"/[locale]/student-permit">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();
  if (!hasFeature(locale, "studentPermit")) notFound();

  const { studentPermit: permit } = await getDictionary(locale);

  return (
    <main className="page-container py-8 sm:py-12">
      <header className="mx-auto max-w-3xl lg:mx-0 lg:max-w-none">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">{permit.title}</h1>
        <p className="mt-3 text-lg leading-relaxed text-zinc-600">{permit.intro}</p>
        <p className="mt-5 flex items-start gap-2 rounded-2xl bg-brand-soft px-4 py-2.5 text-xs leading-relaxed text-zinc-700">
          <ClipboardCheckIcon size={14} className="mt-0.5 shrink-0 text-brand" />
          <span>{permit.checkedNote}</span>
        </p>
      </header>

      <LegalItems
        headingId="student-permit-heading"
        title={permit.title}
        items={permit.items}
        sourceLabel={permit.sourceLabel}
        sourcesTitle={permit.sourcesTitle}
        sources={permit.sources}
      />
    </main>
  );
}
