import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { enumLabel, getProgramme, localizedName } from "@/lib/catalog";

type Params = PageProps<"/[locale]/programmes/[university]/[programme]">["params"];

export const dynamic = "force-dynamic";

async function loadProgramme(params: Params) {
  const { locale, university, programme } = await params;
  if (!isLocale(locale)) notFound();

  const record = await getProgramme(university, programme);
  if (!record) notFound();

  return { locale, record };
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { locale, record } = await loadProgramme(params);
  const name = localizedName(record, locale);
  const universityName = localizedName(record.university, locale);
  return { title: `${name} — ${universityName}` };
}

export default async function ProgrammePage({ params }: { params: Params }) {
  const { locale, record } = await loadProgramme(params);
  const dict = await getDictionary(locale);

  const name = localizedName(record, locale);
  const universityName = localizedName(record.university, locale);

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <Link href={`/${locale}/programmes`} className="text-sm text-zinc-500 hover:underline">
        {dict.programme.backToCatalog}
      </Link>

      <p className="mt-4 text-sm text-zinc-500">{universityName}</p>
      <h1 className="mt-1 text-3xl font-semibold tracking-tight text-zinc-900">{name}</h1>

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
        {record.accreditation_valid_until && (
          <Fact label={dict.programme.accreditation} value={record.accreditation_valid_until} />
        )}
      </dl>

      <p className="mt-8 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-900">
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
