import type { Language } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { httpUrl } from "@/lib/application-channel";
import { formatDate } from "@/lib/dates";
import { interpolate } from "@/lib/outcomes";
import { vuppFundingKey, vuppModeKey, type VuppGroup, type VuppStat, type VuppYear } from "@/lib/vupp-stats";

// Больше стольких подпрограмм — каждая свёрнута под своим названием
// («Skolotājs» у DU — 24 подпрограммы, страница иначе тонет в таблицах).
const COLLAPSE_AFTER = 3;

// Прошлогодний конкурс на карточке латвийской программы (statistika.vupp.lv).
// Только факты о прошедшем приёме: места, заявления, с 1-м приоритетом,
// предварительно прошли конкурс. Ни процентов, ни «проходишь», ни сравнения
// с баллом человека — проходных баллов портал не публикует (CLAUDE.md,
// «Балл и прошлогодний конкурс»). Серверный компонент, обычная разметка.
export function VuppAdmissionStats({
  dict,
  language,
  stats,
}: {
  dict: Dictionary;
  language: Language;
  stats: VuppYear;
}) {
  const text = dict.vuppStats;
  const sourceUrl = httpUrl(stats.sourceUrl);
  const number = (value: number | null) => (value === null ? "—" : value.toLocaleString(language));
  // Значение портала, которого нет в словаре, показывается как есть, по-латышски.
  const funding = (row: VuppStat) => {
    const key = vuppFundingKey(row.funding);
    return key ? text.funding[key] : row.funding;
  };
  const mode = (row: VuppStat) => {
    const key = vuppModeKey(row.studyMode);
    return key ? text.mode[key] : row.studyMode;
  };
  const showNames = stats.groups.length > 1;
  const collapse = stats.groups.length > COLLAPSE_AFTER;

  // Таблица одной группы: на телефоне пять колонок не помещаются — каждая
  // строка карточкой с четырьмя числами, как в литовском блоке; таблица — от sm.
  const figures = (group: VuppGroup) => (
    <>
      <ul className="mt-2 space-y-3 sm:hidden">
        {group.rows.map((row) => (
          <li key={`${row.programmeCode}|${row.funding}|${row.studyMode}|${row.city}`}>
            <p className="text-sm text-zinc-900">
              {funding(row)} · {mode(row)} · {row.city}
            </p>
            <dl className="mt-1 grid grid-cols-2 gap-x-6 gap-y-2">
              <Count label={text.places} value={row.placesUnlimited ? text.unlimited : number(row.places)} />
              <Count label={text.applications} value={number(row.applications)} />
              <Count label={text.firstPriority} value={number(row.firstPriority)} />
              <Count label={text.passed} value={number(row.passed)} />
            </dl>
          </li>
        ))}
      </ul>
      <div className="mt-2 hidden sm:block">
        <table className="w-full text-left text-sm">
          <caption className="sr-only">{showNames ? `${text.tableLabel}: ${group.name}` : text.tableLabel}</caption>
          <thead>
            <tr className="border-b border-zinc-200 text-xs text-zinc-500">
              <th scope="col" className="py-2 pr-4 font-normal">
                {text.rowHeader}
              </th>
              <th scope="col" className="py-2 pr-4 text-right font-normal">
                {text.places}
              </th>
              <th scope="col" className="py-2 pr-4 text-right font-normal">
                {text.applications}
              </th>
              <th scope="col" className="py-2 pr-4 text-right font-normal">
                {text.firstPriority}
              </th>
              <th scope="col" className="py-2 text-right font-normal">
                {text.passed}
              </th>
            </tr>
          </thead>
          <tbody>
            {group.rows.map((row) => (
              <tr key={`${row.programmeCode}|${row.funding}|${row.studyMode}|${row.city}`} className="border-b border-zinc-100">
                <th scope="row" className="py-2 pr-4 font-normal text-zinc-900">
                  {funding(row)} · {mode(row)} · {row.city}
                </th>
                <td className="py-2 pr-4 text-right tabular-nums text-zinc-900">
                  {row.placesUnlimited ? text.unlimited : number(row.places)}
                </td>
                <td className="py-2 pr-4 text-right tabular-nums text-zinc-900">{number(row.applications)}</td>
                <td className="py-2 pr-4 text-right tabular-nums text-zinc-900">{number(row.firstPriority)}</td>
                <td className="py-2 text-right tabular-nums text-zinc-900">{number(row.passed)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );

  return (
    <section id="past-admission" className="mt-8 scroll-mt-24">
      <h2 className="text-xs uppercase tracking-wide text-zinc-500">{interpolate(text.title, { year: stats.year })}</h2>
      {stats.round !== null && (
        <p className="mt-1 text-sm text-zinc-600">{interpolate(text.round, { round: stats.round })}</p>
      )}
      <div className={collapse ? "mt-3 space-y-2" : "mt-3 space-y-5"}>
        {stats.groups.map((group) =>
          collapse ? (
            <details key={group.name} className="group">
              {/* Подпрограммы — своим названием с портала (латышским, как в источнике). */}
              <summary lang="lv" className="cursor-pointer text-sm font-medium text-zinc-900 hover:text-brand">
                {group.name}
              </summary>
              {figures(group)}
            </details>
          ) : (
            <div key={group.name}>
              {showNames && (
                <h3 lang="lv" className="text-sm font-medium text-zinc-900">
                  {group.name}
                </h3>
              )}
              {figures(group)}
            </div>
          ),
        )}
      </div>
      <p className="mt-4 text-sm leading-relaxed text-zinc-600">{text.scope}</p>
      <p className="mt-2 text-sm leading-relaxed text-zinc-600">{text.caveat}</p>
      {/* Дата и источник рядом с числами — правило 5. */}
      <p className="mt-2 text-xs leading-relaxed text-zinc-500">
        {interpolate(text.source, {
          updated: formatDate(stats.portalUpdatedOn ?? stats.extractedAt, language),
          date: formatDate(stats.extractedAt, language),
        })}
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

function Count({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-zinc-500">{label}</dt>
      <dd className="mt-0.5 font-semibold tabular-nums text-zinc-900">{value}</dd>
    </div>
  );
}
