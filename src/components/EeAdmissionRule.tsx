import type { Language } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { httpUrl } from "@/lib/application-channel";
import { tallinnDate } from "@/lib/ee-admission";
import type { EeRule, EeRulePart, EeThresholdSet, EeWeightedRule, EeThresholdRule } from "@/lib/ee-rule";
import { interpolate } from "@/lib/outcomes";
import { sourceHost } from "@/lib/programme-details";

// Правило конкурса эстонской программы — часть блока «Условия конкурса»
// (EeAdmissionConditions). Только факты из правил вуза: из чего складывается
// балл, какие пороги, сколько мест. Ничего о конкретном человеке — ни
// расчёта, ни «порог пройден» (решение об этом за владельцем, docs/PLAN-ESTONIA.md,
// раздел 6). Названия испытаний вуза — по-эстонски, как в источнике, с
// пометкой языка (WCAG 3.1.2). Серверный компонент, обычная разметка.

type Text = Dictionary["eeAdmission"]["rule"];

const heading = "text-xs uppercase tracking-wide text-zinc-500";

function Part({ part, text, estonian }: { part: EeRulePart; text: Text; estonian: string | undefined }) {
  return (
    <>
      {"exam" in part ? text.exams[part.exam] : <span lang={estonian}>{part.other}</span>} {part.weight}%
    </>
  );
}

function Weighted({ rule, text, estonian }: { rule: EeWeightedRule; text: Text; estonian: string | undefined }) {
  const usesMath = rule.variants.some((variant) => variant.some((part) => "exam" in part && part.exam === "math"));
  const facts = [
    rule.applyMin !== null && interpolate(text.applyMin, { points: String(rule.applyMin) }),
    rule.guaranteeMin !== null && interpolate(text.guaranteeMin, { points: String(rule.guaranteeMin) }),
    usesMath && rule.wideMathBonus !== null && interpolate(text.wideMathBonus, { points: String(rule.wideMathBonus) }),
    rule.medalBonus !== null && interpolate(text.medalBonus, { points: String(rule.medalBonus) }),
    rule.english !== null && interpolate(text.english, { level: rule.english }),
  ].filter((fact): fact is string => typeof fact === "string");

  return (
    <>
      <h3 className={heading}>{text.scoreTitle}</h3>
      <p className="mt-2 text-sm leading-relaxed text-zinc-600">
        {text.scoreIntro}
        {rule.variants.length > 1 && ` ${text.variantsIntro}`}
      </p>
      <ul className="mt-2 space-y-1 text-zinc-900">
        {rule.variants.map((variant, index) => (
          <li key={index}>
            {index > 0 && `${text.or} `}
            {variant.map((part, partIndex) => (
              <span key={partIndex}>
                {partIndex > 0 && " + "}
                <Part part={part} text={text} estonian={estonian} />
              </span>
            ))}
          </li>
        ))}
      </ul>
      {facts.length > 0 && (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-relaxed text-zinc-700">
          {facts.map((fact) => (
            <li key={fact}>{fact}</li>
          ))}
        </ul>
      )}
    </>
  );
}

function ThresholdList({ set, text }: { set: EeThresholdSet; text: Text }) {
  const atLeast = (value: number | string) => interpolate(text.atLeast, { value: String(value) });
  return (
    <ul className="mt-1 space-y-1 text-zinc-900">
      <li>
        {text.subjects.math} — {atLeast(set.math)}
      </li>
      <li>
        {text.subjects.estonian} — {atLeast(set.estonian)}; {text.subjects.estonianSecond} — {atLeast(set.estonianSecond)}
      </li>
      {set.english && (
        <li>
          {text.subjects.english} — {atLeast(set.english)}
        </li>
      )}
    </ul>
  );
}

function Thresholds({ rule, text, estonian }: { rule: EeThresholdRule; text: Text; estonian: string | undefined }) {
  const [beforeQuote, afterQuote] = text.mathNote.split("{quote}");
  return (
    <>
      <h3 className={heading}>{text.thresholdsTitle}</h3>
      <dl className="mt-2 grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
        {rule.apply && (
          <div>
            <dt className="text-sm font-medium text-zinc-700">{text.applySet}</dt>
            <dd>
              <ThresholdList set={rule.apply} text={text} />
            </dd>
          </div>
        )}
        <div>
          <dt className="text-sm font-medium text-zinc-700">{text.guaranteeSet}</dt>
          <dd>
            <ThresholdList set={rule.guarantee} text={text} />
          </dd>
        </div>
      </dl>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-relaxed text-zinc-700">
        {rule.places !== null && <li>{interpolate(text.places, { places: String(rule.places) })}</li>}
        <li>{rule.ranking ? text.ranking : text.onlyThreshold}</li>
        <li>
          {beforeQuote}
          <span lang={estonian}>(laia) matemaatika riigieksam</span>
          {afterQuote}
        </li>
      </ul>
    </>
  );
}

export function EeAdmissionRule({
  dict,
  language,
  rule,
  sourceUrl,
  extractedAt,
}: {
  dict: Dictionary;
  language: Language;
  rule: EeRule;
  sourceUrl: string | null;
  extractedAt: string | null;
}) {
  const text = dict.eeAdmission.rule;
  const estonian = language === "et" ? undefined : "et";
  const link = sourceUrl ? httpUrl(sourceUrl) : null;
  return (
    <div className="mt-6">
      {rule.model === "weighted" ? (
        <Weighted rule={rule} text={text} estonian={estonian} />
      ) : (
        <Thresholds rule={rule} text={text} estonian={estonian} />
      )}
      {/* Пороги ТÜ взяты со страницы программы у вуза — у неё своя подпись источника. */}
      {link && extractedAt && (
        <p className="mt-2 text-xs leading-relaxed text-zinc-500">
          {interpolate(dict.programme.detailsSource, {
            source: sourceHost(link) ?? "",
            date: tallinnDate(extractedAt, language),
          })}{" "}
          <a href={link} target="_blank" rel="noopener noreferrer" className="underline">
            {dict.catalog.sourceLinkLabel}
          </a>
        </p>
      )}
    </div>
  );
}
