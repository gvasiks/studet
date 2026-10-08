import type { Language } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { httpUrl } from "@/lib/application-channel";
import type { LtFieldOutcome as Outcome } from "@/lib/lt-field-outcome-queries";
import { interpolate } from "@/lib/outcomes";

// «Что стало с выпускниками» на карточке литовской программы. Показатели —
// по направлению и ступени по всей стране (так их публикует министерство),
// а не по программе и не по вузу: об этом сказано прямо в блоке. Название
// направления остаётся литовским, как в источнике. Серверный компонент.
export function LtFieldOutcome({
  dict,
  language,
  degreeLevel,
  outcome,
}: {
  dict: Dictionary;
  language: Language;
  degreeLevel: string;
  outcome: Outcome;
}) {
  const text = dict.ltOutcomes;
  const percent = (value: number) => value.toLocaleString(language, { maximumFractionDigits: 0 });
  const level = text.levels[degreeLevel as keyof typeof text.levels] ?? degreeLevel;
  const sourceUrl = httpUrl(outcome.sourceUrl);

  return (
    <section className="mt-8">
      <h2 className="text-xs uppercase tracking-wide text-zinc-500">{dict.outcomes.title}</h2>
      <p className="mt-2 text-sm text-zinc-600">
        {interpolate(text.scope, { level, from: outcome.cohortFrom, to: outcome.cohortTo })}{" "}
        <span lang="lt">„{outcome.fieldName}“</span>
      </p>
      <ul className="mt-3 space-y-1 text-zinc-900">
        <li>{interpolate(text.employed, { percent: percent(outcome.employedPercent) })}</li>
        <li>{interpolate(text.qualified, { percent: percent(outcome.qualifiedPercent) })}</li>
        <li>
          {interpolate(text.income, {
            percent: percent(outcome.incomePercent),
            average: outcome.levelAverageIncomeEur.toLocaleString(language),
          })}
        </li>
      </ul>
      <p className="mt-3 text-xs leading-relaxed text-zinc-500">{text.caveat}</p>
      {/* Дата и источник рядом с числами — правило 5. */}
      <p className="mt-1 text-xs leading-relaxed text-zinc-500">
        {interpolate(text.source, { date: new Date(outcome.publishedOn).toLocaleDateString(language) })}
        {sourceUrl && (
          <>
            {" "}
            <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="underline">
              {dict.catalog.sourceLinkLabel}
            </a>
          </>
        )}
      </p>
    </section>
  );
}
