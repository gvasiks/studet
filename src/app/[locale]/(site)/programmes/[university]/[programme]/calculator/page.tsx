import { BackButton } from "@/components/BackButton";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { countryOf, isLocale, languageOf } from "@/i18n/config";
import { hasFeature } from "@/lib/country";
import { getDictionary } from "@/i18n/dictionaries";
import { getProgramme, localizedName } from "@/lib/catalog";
import { getFormula, getLevelCoefficients } from "@/lib/formula-queries";
import { getAdmissionType } from "@/lib/admission-type-queries";
import { getLtFormula } from "@/lib/lt-score-queries";
import { buildAlternates, SITE_URL } from "@/lib/site";
import { ReportErrorLink } from "@/components/ReportErrorLink";
import { CalculatorForm } from "./CalculatorForm";
import { LtCalculatorForm } from "./LtCalculatorForm";

type Params = PageProps<"/[locale]/programmes/[university]/[programme]/calculator">["params"];

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { locale, university, programme: programmeSlug } = await params;
  if (!isLocale(locale)) notFound();
  if (!hasFeature(locale, "calculator")) notFound();

  const dict = await getDictionary(locale);
  const record = await getProgramme(countryOf(locale), university, programmeSlug);
  if (!record) notFound();

  const name = localizedName(record, languageOf(locale));
  const path = `/programmes/${university}/${programmeSlug}/calculator`;
  return {
    title: { absolute: `${dict.calculator.title} — ${name}` },
    alternates: buildAlternates(path, locale),
  };
}

export default async function CalculatorPage({ params }: { params: Params }) {
  const { locale, university, programme: programmeSlug } = await params;
  if (!isLocale(locale)) notFound();
  if (!hasFeature(locale, "calculator")) notFound();

  const dict = await getDictionary(locale);
  const record = await getProgramme(countryOf(locale), university, programmeSlug);
  if (!record) notFound();

  // В Литве правило расчёта общее на страну, формулы лежат в своих
  // таблицах и считаются своим вычислителем — отдельная ветка ниже.
  if (countryOf(locale) === "LT") {
    const ltFormula = await getLtFormula(record.id);
    return (
      <main className="page-container py-8 sm:py-12">
        <div className="surface mx-auto max-w-2xl p-6 sm:p-10">
          <BackButton fallbackHref={`/${locale}/programmes/${university}/${programmeSlug}`} label={dict.programme.back} />
          <p className="mt-4 text-sm text-zinc-500">{localizedName(record, languageOf(locale))}</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tighter text-zinc-900">{dict.calculator.title}</h1>
          {ltFormula ? (
            <LtCalculatorForm
              dict={dict}
              locale={locale}
              components={ltFormula.components}
              admissionYear={ltFormula.admissionYear}
              sourceUrl={ltFormula.sourceUrl}
              checkedAt={ltFormula.checkedAt}
            />
          ) : (
            <p className="mt-8 text-zinc-600">{dict.ltCalculator.notAvailable}</p>
          )}
          <ReportErrorLink
            dict={dict}
            programmeName={localizedName(record, languageOf(locale))}
            universityName={localizedName(record.university, languageOf(locale))}
            pageUrl={`${SITE_URL}/${locale}/programmes/${university}/${programmeSlug}/calculator`}
          />
        </div>
      </main>
    );
  }

  const formula = await getFormula(record.id);
  const levelCoefficients = await getLevelCoefficients();

  // Пункт 06 ревью 2026-09: если тип отбора подтверждён и это не
  // конкурсный балл, сообщение объясняет почему, а не повторяет общее
  // "формула ещё не готова" — см. тот же приём на основной странице
  // программы ([programme]/page.tsx).
  let notAvailableMessage = dict.calculator.notAvailable;
  if (!formula) {
    const admissionType = await getAdmissionType(record.university_id);
    if (admissionType && admissionType.selectionType !== "competitive_score") {
      notAvailableMessage = dict.programme.selectionTypes[admissionType.selectionType];
    }
  }

  return (
    <main className="page-container py-8 sm:py-12">
      <div className="surface mx-auto max-w-2xl p-6 sm:p-10">
      <BackButton fallbackHref={`/${locale}/programmes/${university}/${programmeSlug}`} label={dict.programme.back} />

      <p className="mt-4 text-sm text-zinc-500">{localizedName(record, languageOf(locale))}</p>
      <h1 className="mt-1 text-2xl font-bold tracking-tighter text-zinc-900">{dict.calculator.title}</h1>

      {!formula ? (
        <p className="mt-8 text-zinc-600">{notAvailableMessage}</p>
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

      {/* В письмо подставляется только адрес страницы — введённые
          результаты экзаменов браузер не покидают. */}
      <ReportErrorLink
        dict={dict}
        programmeName={localizedName(record, languageOf(locale))}
        universityName={localizedName(record.university, languageOf(locale))}
        pageUrl={`${SITE_URL}/${locale}/programmes/${university}/${programmeSlug}/calculator`}
      />
    </div>
    </main>
  );
}
