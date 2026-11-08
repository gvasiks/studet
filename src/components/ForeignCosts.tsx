import type { Dictionary } from "@/i18n/dictionaries";
import { formatDate } from "@/lib/dates";
import { httpUrl } from "@/lib/application-channel";
import { interpolate } from "@/lib/outcomes";
import {
  costFor,
  euPriceIncludesCandidates,
  feesFor,
  firstYearTotal,
  formatMoney,
  type AppliesTo,
  type CountryCost,
  type ProgrammeFee,
} from "@/lib/foreign-costs";

// «Costs for international students» на карточке программы (docs/PLAN-
// FOREIGNERS.md, шаг 1). Серверный компонент, без "use client" (правило 4):
// карточка — то, что приходит из поиска.
//
// Сюда приходят только подтверждённые человеком суммы (правило 6). У каждой
// строки — дата проверки и ссылка на источник (правило 5). Чего нет в базе,
// того нет и на экране: плата, которую ещё не проверили, — честная строка
// «не проверено», а не цена из соседнего поля.

type Line = { label: string; value: string; verifiedAt: string; sourceUrl: string; sourceTitle?: string };

export function ForeignCosts({
  dict,
  language,
  costs,
  fees,
}: {
  dict: Dictionary;
  language: string;
  /** Действующие на сегодня суммы страны (currentCountryCosts). */
  costs: CountryCost[];
  fees: ProgrammeFee[];
}) {
  const t = dict.programme.foreignCosts;

  function money(amount: number, currency: string) {
    return formatMoney(amount, currency, language);
  }

  function group(appliesTo: AppliesTo) {
    const own = feesFor(fees, appliesTo);
    const lines: Line[] = [];
    if (own.tuition) {
      lines.push({
        label: interpolate(t.tuition, { year: own.tuition.academicYear }),
        value: money(own.tuition.amount, own.tuition.currency),
        verifiedAt: own.tuition.verifiedAt,
        sourceUrl: own.tuition.sourceUrl,
      });
    }
    for (const [kind, label] of [
      ["application_fee", t.applicationFee],
      ["enrolment_fee", t.enrolmentFee],
    ] as const) {
      const fee = own[kind];
      if (fee) lines.push({ label, value: money(fee.amount, fee.currency), verifiedAt: fee.verifiedAt, sourceUrl: fee.sourceUrl });
    }
    for (const [code, label] of [
      ["residence_permit_review", t.residencePermitReview],
      ["residence_permit_registration", t.residencePermitRegistration],
      ["long_stay_visa", t.longStayVisa],
    ] as const) {
      const cost = costFor(costs, code, appliesTo);
      if (cost) {
        lines.push({
          label,
          value: money(cost.amount, cost.currency),
          verifiedAt: cost.verifiedAt,
          sourceUrl: cost.sourceUrl,
          sourceTitle: cost.sourceTitle,
        });
      }
    }
    return { tuitionKnown: Boolean(own.tuition), lines, total: firstYearTotal(own, costs, appliesTo) };
  }

  const eu = group("eu");
  const nonEu = group("non_eu");
  const means = costFor(costs, "means_per_month", "non_eu");

  return (
    <section className="mt-8" aria-labelledby="foreign-costs">
      <h2 id="foreign-costs" className="text-xs uppercase tracking-wide text-zinc-500">
        {t.title}
      </h2>
      <p className="mt-2 text-sm text-zinc-600">{t.intro}</p>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {(
          [
            [t.euTitle, eu],
            [t.nonEuTitle, nonEu],
          ] as const
        ).map(([title, data]) => (
          <div key={title} className="rounded-2xl border border-zinc-200 p-4">
            <h3 className="text-sm font-semibold text-zinc-900">{title}</h3>
            {!data.tuitionKnown && <p className="mt-2 text-sm text-zinc-600">{t.tuitionMissing}</p>}
            {data.lines.length > 0 && (
              <dl className="mt-3 space-y-3 text-sm">
                {data.lines.map((line) => (
                  <CostLine key={line.label} line={line} dict={dict} language={language} />
                ))}
              </dl>
            )}
            {data.total && (
              <div className="mt-4 border-t border-zinc-200 pt-3">
                <p className="flex items-baseline justify-between gap-4 text-sm font-semibold text-zinc-900">
                  <span>{t.total}</span>
                  <span className="tabular-nums">{money(data.total.amount, data.total.currency)}</span>
                </p>
                <p className="mt-1 text-xs leading-relaxed text-zinc-500">{t.totalNote}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Вуз шире понимает «цену ЕС», чем подпись колонки (миграция 20261108130000). */}
      {euPriceIncludesCandidates(fees) && <p className="mt-3 text-sm text-zinc-700">{t.euIncludesCandidates}</p>}

      {means && (
        <div className="mt-4 rounded-2xl bg-zinc-50 p-4 text-sm">
          <dl>
            <CostLine
              line={{
                label: `${t.means} (${t.nonEuTitle.toLowerCase()})`,
                value: interpolate(t.meansValue, { amount: money(means.amount, means.currency) }),
                verifiedAt: means.verifiedAt,
                sourceUrl: means.sourceUrl,
                sourceTitle: means.sourceTitle,
              }}
              dict={dict}
              language={language}
            />
          </dl>
          <p className="mt-2 text-xs leading-relaxed text-zinc-600">{t.meansNote}</p>
        </div>
      )}

      <p className="mt-4 text-xs leading-relaxed text-zinc-500">
        {t.insuranceNote} {t.disclaimer}
      </p>
    </section>
  );
}

function CostLine({ line, dict, language }: { line: Line; dict: Dictionary; language: string }) {
  const sourceUrl = httpUrl(line.sourceUrl);
  return (
    // Внутри <dl> обёртка может держать только <dt> и <dd> (axe: dlitem),
    // поэтому подпись с датой и источником — часть <dt>.
    <div className="flex items-baseline justify-between gap-4">
      <dt className="min-w-0 text-zinc-700">
        {line.label}
        {/* Дата проверки и источник у каждой суммы — правило 5. */}
        <span className="mt-0.5 block text-xs text-zinc-500">
          {dict.catalog.verifiedPrefix} {formatDate(line.verifiedAt, language).replace(/\.?$/, ".")}
          {line.sourceTitle && <> {line.sourceTitle}.</>}
          {sourceUrl && (
            <>
              {" "}
              <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="underline">
                {dict.catalog.sourceLinkLabel}
              </a>
            </>
          )}
        </span>
      </dt>
      <dd className="shrink-0 font-medium tabular-nums text-zinc-900">{line.value}</dd>
    </div>
  );
}
