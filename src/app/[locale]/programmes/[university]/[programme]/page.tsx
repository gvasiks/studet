import Link from "next/link";
import type { Metadata } from "next";
import type { Dictionary } from "@/i18n/dictionaries";
import type { Locale } from "@/i18n/config";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { enumLabel, getProgramme, localizedName, type Programme, type University } from "@/lib/catalog";
import { getFormula } from "@/lib/formula-queries";
import { getApplicationRounds } from "@/lib/deadline-queries";
import { matchRounds } from "@/lib/deadlines";
import { getAdmissionType } from "@/lib/admission-type-queries";
import { getProgrammeOutcome } from "@/lib/outcome-queries";
import { areaCode } from "@/lib/fields";
import { employmentPercent, interpolate, OUTCOMES_SOURCE_URL, pickOutcomes } from "@/lib/outcomes";
import { FavoriteButton } from "@/components/FavoriteButton";
import { buildAlternates, SITE_URL } from "@/lib/site";

type Params = PageProps<"/[locale]/programmes/[university]/[programme]">["params"];

export const dynamic = "force-dynamic";

async function loadProgramme(params: Params) {
  const { locale, university, programme } = await params;
  if (!isLocale(locale)) notFound();

  const record = await getProgramme(university, programme);
  if (!record) notFound();

  return { locale, record };
}

// Из реальных полей карточки, не шаблонная фраза "изучите X у нас" —
// ревью 2026-09, пункт 08. Структура предложения одна и та же для всех
// программ (иначе никак), но содержание каждый раз собирается из того,
// что реально известно об этой конкретной программе.
function buildDescription(
  record: Programme & { university: Pick<University, "name_lv" | "name_en"> },
  dict: Dictionary,
  locale: Locale,
): string {
  const universityName = localizedName(record.university, locale);
  const degree = enumLabel(dict.catalog.degreeLevel, record.degree_level);
  const language = enumLabel(dict.catalog.language, record.language_of_instruction);
  const mode = enumLabel(dict.catalog.studyMode, record.study_mode);
  const city = record.city ? enumLabel(dict.catalog.city, record.city) : null;

  const parts = [`${degree} — ${universityName}${city ? `, ${city}` : ""}.`];
  parts.push(`${dict.programme.language}: ${language}. ${dict.programme.studyMode}: ${mode}.`);
  parts.push(
    record.tuition_fee_amount !== null
      ? `${dict.programme.tuitionFee}: ${record.tuition_fee_amount} ${record.tuition_fee_currency}.`
      : `${enumLabel(dict.catalog.funding, record.funding_type)}.`,
  );
  return parts.join(" ");
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { locale, record } = await loadProgramme(params);
  const dict = await getDictionary(locale);
  const name = localizedName(record, locale);
  const universityName = localizedName(record.university, locale);
  const path = `/programmes/${record.university.slug}/${record.slug}`;

  return {
    // title.absolute обходит шаблон "%s — {название сайта}" из
    // [locale]/layout.tsx — тут уже есть своё "программа — вуз".
    title: { absolute: `${name} — ${universityName}` },
    description: buildDescription(record, dict, locale),
    alternates: buildAlternates(path, locale),
  };
}

export default async function ProgrammePage({ params }: { params: Params }) {
  const { locale, record } = await loadProgramme(params);
  const dict = await getDictionary(locale);
  const [formula, rounds, admissionType, outcome] = await Promise.all([
    getFormula(record.id),
    getApplicationRounds(),
    getAdmissionType(record.university_id),
    getProgrammeOutcome(record.id, record.university_id),
  ]);
  // Блок "что стало с выпускниками" (пункт 14 ревью) — только при
  // подтверждённом направлении программы, см. outcome-queries.ts.
  const outcomeSnapshots = outcome ? pickOutcomes(outcome.rows, record.degree_level) : [];
  const applicationRounds = matchRounds(
    rounds,
    record.university_id,
    record.degree_level,
    record.language_of_instruction,
  );
  // Пункт 06 ревью 2026-09: без формулы карточка молчала одинаково и
  // там, где формулу ещё не собрали, и там, где конкурсного балла нет
  // в принципе (8 из 14 вузов — все частные). Если тип отбора
  // подтверждён и это не конкурсный балл — показываем объяснение вместо
  // тишины; если неизвестен или сам конкурсный балл — поведение прежнее
  // (пусто, пока формулу не собрали и не подтвердили).
  let noCompetitiveScoreReason: string | null = null;
  if (!formula && admissionType && admissionType.selectionType !== "competitive_score") {
    noCompetitiveScoreReason = dict.programme.selectionTypes[admissionType.selectionType];
  }

  const name = localizedName(record, locale);
  const universityName = localizedName(record.university, locale);
  const pageUrl = `${SITE_URL}/${locale}/programmes/${record.university.slug}/${record.slug}`;

  // Course + provider (CollegeOrUniversity) — ревью 2026-09, пункт 08.
  // Держим схему минимальной и корректной, а не максималистской:
  // study_mode ("full_time"/"part_time"/"distance") — это не то же
  // самое, что schema.org courseMode ("online"/"onsite"/"blended"),
  // натягивать одно на другое значило бы публиковать неверные данные
  // ради галочки "разметка есть" — hasCourseInstance сюда сознательно
  // не пошёл.
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Course",
    name,
    description: buildDescription(record, dict, locale),
    url: pageUrl,
    inLanguage: record.language_of_instruction,
    provider: {
      "@type": "CollegeOrUniversity",
      name: universityName,
      ...(record.university.website_url ? { sameAs: record.university.website_url } : {}),
    },
    ...(record.tuition_fee_amount !== null
      ? {
          offers: {
            "@type": "Offer",
            price: record.tuition_fee_amount,
            priceCurrency: record.tuition_fee_currency,
          },
        }
      : {}),
  };

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
      <Link href={`/${locale}/programmes`} className="text-sm text-zinc-500 hover:underline">
        {dict.programme.backToCatalog}
      </Link>

      <p className="mt-4 text-sm text-zinc-500">{universityName}</p>
      <div className="flex items-start justify-between gap-3">
        <h1 className="mt-1 text-3xl font-bold tracking-tighter text-zinc-900">{name}</h1>
        <FavoriteButton
          programmeId={record.id}
          addLabel={dict.favorites.add}
          removeLabel={dict.favorites.remove}
          className="mt-2 text-2xl"
        />
      </div>

      <dl className="mt-8 grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
        <Fact label={dict.programme.degreeLevel} value={enumLabel(dict.catalog.degreeLevel, record.degree_level)} />
        <Fact
          label={dict.programme.language}
          value={enumLabel(dict.catalog.language, record.language_of_instruction)}
        />
        <Fact label={dict.programme.studyMode} value={enumLabel(dict.catalog.studyMode, record.study_mode)} />
        {record.duration_years !== null && (
          <Fact label={dict.programme.duration} value={`${record.duration_years} ${dict.catalog.years}`} />
        )}
        {record.city && <Fact label={dict.programme.city} value={enumLabel(dict.catalog.city, record.city)} />}
        <Fact label={dict.programme.funding} value={enumLabel(dict.catalog.funding, record.funding_type)} />
        {record.tuition_fee_amount !== null && (
          <Fact
            label={dict.programme.tuitionFee}
            value={`${record.tuition_fee_amount} ${record.tuition_fee_currency}`}
          />
        )}
        {record.budget_places !== null && (
          <Fact label={dict.programme.budgetPlaces} value={String(record.budget_places)} />
        )}
        {record.accreditation_valid_until && (
          <Fact label={dict.programme.accreditation} value={record.accreditation_valid_until} />
        )}
      </dl>

      <section className="mt-8">
        <h2 className="text-xs uppercase tracking-wide text-zinc-500">{dict.programme.deadlinesTitle}</h2>
        {applicationRounds.length > 0 ? (
          <ul className="mt-2 space-y-1 text-zinc-900">
            {applicationRounds.map((round) => (
              <li key={round.label}>
                {round.label}
                {(round.opensOn || round.closesOn) && (
                  <>
                    {": "}
                    {round.opensOn && `${dict.programme.deadlinesOpens} ${new Date(round.opensOn).toLocaleDateString(locale)}`}
                    {round.opensOn && round.closesOn && " "}
                    {round.closesOn && `${dict.programme.deadlinesCloses} ${new Date(round.closesOn).toLocaleDateString(locale)}`}
                  </>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-zinc-500">{dict.programme.deadlinesNotAvailable}</p>
        )}
      </section>

      {formula && (
        <Link
          href={`/${locale}/programmes/${record.university.slug}/${record.slug}/calculator`}
          className="mt-8 inline-block w-fit rounded-full bg-brand px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-dark"
        >
          {dict.calculator.title}
        </Link>
      )}

      {noCompetitiveScoreReason && <p className="mt-8 text-sm text-zinc-600">{noCompetitiveScoreReason}</p>}

      {outcome && outcomeSnapshots.length > 0 && (
        <section className="mt-8">
          <h2 className="text-xs uppercase tracking-wide text-zinc-500">{dict.outcomes.title}</h2>
          <p className="mt-2 text-sm text-zinc-600">
            {interpolate(dict.outcomes.scope, {
              university: universityName,
              field: enumLabel(dict.fields.areas, areaCode(outcome.fieldCode)),
              code: outcome.fieldCode,
              level: enumLabel(dict.outcomes.levels, record.degree_level),
            })}
          </p>
          <ul className="mt-3 space-y-3">
            {outcomeSnapshots.map((snapshot) => (
              <li key={snapshot.graduationYear} className="text-zinc-900">
                <p className="text-sm font-medium">
                  {interpolate(dict.outcomes.cohort, { year: snapshot.graduationYear, taxYear: snapshot.taxYear })}
                </p>
                <p>
                  {interpolate(dict.outcomes.employed, {
                    employed: snapshot.employed,
                    graduates: snapshot.graduates,
                    percent: employmentPercent(snapshot),
                  })}
                </p>
                {snapshot.medianIncomeEur !== null ? (
                  <p>
                    {interpolate(dict.outcomes.median, {
                      amount: Math.round(snapshot.medianIncomeEur).toLocaleString(locale),
                    })}
                  </p>
                ) : (
                  // У докторов доходы не публикуются вовсе — причина другая,
                  // чем "меньше 30 занятых", поэтому там строку не показываем.
                  record.degree_level !== "doctoral" && (
                    <p className="text-sm text-zinc-500">{dict.outcomes.incomeHidden}</p>
                  )
                )}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-zinc-500">{dict.outcomes.caveat}</p>
          <p className="mt-1 text-xs text-zinc-500">
            <a href={OUTCOMES_SOURCE_URL} target="_blank" rel="noopener noreferrer" className="underline">
              {dict.outcomes.source}
            </a>
          </p>
        </section>
      )}

      <p className="mt-8 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900">
        {record.verified_at
          ? `${dict.catalog.verifiedPrefix} ${new Date(record.verified_at).toLocaleDateString(locale)}`
          : dict.catalog.unverifiedLabel}
        {record.source_url && (
          <>
            {" "}
            <a
              href={record.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="underline"
            >
              {dict.catalog.sourceLinkLabel}
            </a>
          </>
        )}
      </p>
    </main>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-zinc-500">{label}</dt>
      <dd className="mt-1 text-zinc-900">{value}</dd>
    </div>
  );
}
