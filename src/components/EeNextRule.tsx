import type { Language } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { EeAdmissionRule } from "@/components/EeAdmissionRule";
import { httpUrl } from "@/lib/application-channel";
import { plainDate, tallinnDate } from "@/lib/ee-admission";
import type { EeNextRule as NextRule } from "@/lib/ee-admission-queries";
import type { EeTextRule } from "@/lib/ee-rule";
import { interpolate } from "@/lib/outcomes";
import { sourceHost } from "@/lib/programme-details";

// Условия приёма следующего учебного года из решения вуза (решение владельца
// 2026-11-27) — над блоком прошлого конкурса SAIS. Только факты правила
// приёма; ни расчёта, ни вывода о человеке.
// - Бакалавриат: пороги госэкзаменов и места — тем же компонентом, что у
//   прошлого конкурса (EeAdmissionRule, там же подпись источника).
// - Магистратура: требования, испытания и порог — текстом решения
//   по-эстонски, с нашими подписями; перевода нет (это была бы уже
//   интерпретация правил вуза).
// Серверный компонент, обычная разметка.

const label = "text-xs uppercase tracking-wide text-zinc-500";

function TextRule({ rule, dict, language }: { rule: EeTextRule; dict: Dictionary; language: Language }) {
  const text = dict.eeAdmission.next;
  const forms = dict.eeAdmission.forms;
  const estonian = language === "et" ? undefined : "et";
  const studyForm = { P: forms.daytime, S: forms.session, "P/S": `${forms.daytime}, ${forms.session}` }[rule.studyForm];
  const plus = [rule.threshold, rule.foreignThreshold].some((value) => value?.includes("+"));
  return (
    <>
      <dl className="mt-4 grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
        <div>
          <dt className={label}>{dict.eeAdmission.studyForm}</dt>
          <dd className="mt-1 text-zinc-900">{studyForm}</dd>
        </div>
        <div>
          <dt className={label}>{text.threshold}</dt>
          <dd className="mt-1 text-zinc-900" lang={estonian}>
            {rule.threshold}
          </dd>
        </div>
        <div className="sm:col-span-2">
          <dt className={label}>{text.education}</dt>
          <dd className="mt-1 text-zinc-900" lang={estonian}>
            {rule.education}
          </dd>
        </div>
        <div className="sm:col-span-2">
          <dt className={label}>{text.tests}</dt>
          <dd className="mt-1 text-zinc-900" lang={estonian}>
            {rule.tests}
          </dd>
        </div>
        {rule.foreignTests && (
          <div className="sm:col-span-2">
            <dt className={label}>{text.foreign}</dt>
            <dd className="mt-1 text-zinc-900" lang={estonian}>
              {rule.foreignTests}
              {rule.foreignThreshold && ` — ${rule.foreignThreshold}`}
            </dd>
          </div>
        )}
      </dl>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-relaxed text-zinc-700">
        <li>{text.scaleNote}</li>
        {plus && <li>{text.plusNote}</li>}
        {rule.gre && <li>{text.gre}</li>}
        {estonian && <li>{text.textNote}</li>}
      </ul>
    </>
  );
}

export function EeNextRule({ dict, language, next }: { dict: Dictionary; language: Language; next: NextRule }) {
  const text = dict.eeAdmission.next;
  const estonian = language === "et" ? undefined : "et";
  const link = httpUrl(next.sourceUrl);
  return (
    <section className="mt-8">
      <h2 className={label}>{interpolate(text.title, { year: next.academicYear })}</h2>
      <p className="mt-3 text-sm leading-relaxed text-zinc-700">
        {interpolate(text.approved, { date: plainDate(next.decidedOn, language) })}{" "}
        <span lang={estonian}>{next.sourceTitle}</span>
      </p>
      {next.newCurriculum && <p className="mt-2 text-sm leading-relaxed text-zinc-700">{text.newCurriculum}</p>}
      {next.rule.model === "text" ? (
        <>
          <TextRule rule={next.rule} dict={dict} language={language} />
          {link && (
            <p className="mt-2 text-xs leading-relaxed text-zinc-500">
              {interpolate(dict.programme.detailsSource, {
                source: sourceHost(link) ?? "",
                date: tallinnDate(next.extractedAt, language),
              })}{" "}
              <a href={link} target="_blank" rel="noopener noreferrer" className="underline">
                {dict.catalog.sourceLinkLabel}
              </a>
            </p>
          )}
        </>
      ) : (
        <EeAdmissionRule dict={dict} language={language} rule={next.rule} sourceUrl={next.sourceUrl} extractedAt={next.extractedAt} />
      )}
      <p className="mt-4 text-sm leading-relaxed text-zinc-600">{interpolate(text.note, { year: next.academicYear })}</p>
    </section>
  );
}
