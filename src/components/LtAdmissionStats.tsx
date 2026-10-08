import type { Language } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { httpUrl } from "@/lib/application-channel";
import type { LtAdmissionYear } from "@/lib/lt-admission-stats";
import { interpolate } from "@/lib/outcomes";

// Цифры прошлого приёма на карточке литовской программы. Только факты о
// прошедшем приёме: сколько раз программу внесли в заявление, сколько из
// них первым номером, сколько человек пригласили и сколько подписали
// договор. Ни процентов, ни «проходишь», ни сравнения с баллом человека —
// числа мест и проходных баллов в источнике нет (CLAUDE.md, «Балл и
// прошлогодний конкурс»). Серверный компонент, обычная разметка.
export function LtAdmissionStats({
  dict,
  language,
  stats,
}: {
  dict: Dictionary;
  language: Language;
  stats: LtAdmissionYear;
}) {
  const text = dict.ltStats;
  const number = (value: number) => value.toLocaleString(language);
  const sourceUrl = httpUrl(stats.sourceUrl);

  return (
    <section className="mt-8">
      <h2 className="text-xs uppercase tracking-wide text-zinc-500">
        {interpolate(text.title, { year: stats.year })}
      </h2>
      <div className="mt-3 space-y-4">
        {stats.rows.map((row) => (
          <div key={row.funding}>
            <h3 className="text-sm font-medium text-zinc-900">{text.funding[row.funding]}</h3>
            <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
              <Count label={text.applications} value={number(row.applications)} />
              <Count label={text.firstPriority} value={number(row.firstPriority)} />
              <Count label={text.invited} value={number(row.invited)} />
              <Count label={text.signed} value={number(row.signed)} />
            </dl>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm leading-relaxed text-zinc-600">{text.scope}</p>
      <p className="mt-2 text-sm leading-relaxed text-zinc-600">{text.caveat}</p>
      {/* Дата и источник рядом с числами — правило 5. */}
      <p className="mt-2 text-xs leading-relaxed text-zinc-500">
        {interpolate(text.source, { date: new Date(stats.extractedAt).toLocaleDateString(language) })}
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
      <dd className="mt-0.5 text-lg font-semibold tabular-nums text-zinc-900">{value}</dd>
    </div>
  );
}
