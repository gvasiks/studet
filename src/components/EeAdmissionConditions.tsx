import type { Language } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { httpUrl } from "@/lib/application-channel";
import {
  plainDate,
  studyFormKey,
  studyForms,
  tallinnDate,
  type EeAdmission,
  type EeAdmissionState,
} from "@/lib/ee-admission";
import { interpolate } from "@/lib/outcomes";
import { sourceHost } from "@/lib/programme-details";

// Условия конкурса на карточке эстонской программы: форма обучения, место,
// начало занятий, нагрузка с финансированием и цена — со страницы конкурса в
// системе подачи SAIS. Человек их не подтверждает (решение владельца
// 2026-10-11, как для Литвы), поэтому под блоком — пометка об автоматическом
// извлечении, дата и ссылка на страницу (правило 5).
//
// У большинства программ конкурс прошлый: тогда это условия прошлого приёма,
// и блок так и говорит. Название конкурса показано, потому что конкурс
// бывает частным случаем программы — дополнительный набор, одна тема
// докторантуры, одна из форм обучения.
//
// Значения, которые SAIS пишет по-эстонски (название конкурса, место,
// незнакомая форма обучения), помечены языком (WCAG 3.1.2). Серверный
// компонент, обычная разметка.
export function EeAdmissionConditions({
  dict,
  language,
  admission,
  state,
}: {
  dict: Dictionary;
  language: Language;
  admission: EeAdmission;
  state: EeAdmissionState;
}) {
  // Без названия страница конкурса не прочитана или удалена — показывать нечего.
  if (admission.title === null || admission.detailsFetchedAt === null) return null;

  const text = dict.eeAdmission;
  const saisUrl = httpUrl(admission.saisUrl);
  const forms = studyForms(admission.studyForm);
  const estonian = language === "et" ? undefined : "et";

  return (
    <section className="mt-8">
      <h2 className="text-xs uppercase tracking-wide text-zinc-500">{text.title}</h2>
      <dl className="mt-3 grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <dt className="text-xs uppercase tracking-wide text-zinc-500">{text.competition}</dt>
          <dd className="mt-1 text-zinc-900" lang={estonian}>
            {admission.title}
          </dd>
        </div>
        {forms.length > 0 && (
          <div>
            <dt className="text-xs uppercase tracking-wide text-zinc-500">{text.studyForm}</dt>
            <dd className="mt-1 text-zinc-900">
              {forms.map((form, index) => {
                const key = studyFormKey(form);
                return (
                  <span key={form}>
                    {index > 0 && ", "}
                    {key ? text.forms[key] : <span lang={estonian}>{form}</span>}
                  </span>
                );
              })}
            </dd>
          </div>
        )}
        {admission.location && (
          <div>
            <dt className="text-xs uppercase tracking-wide text-zinc-500">{text.location}</dt>
            <dd className="mt-1 text-zinc-900" lang={estonian}>
              {admission.location}
            </dd>
          </div>
        )}
        {admission.startsOn && (
          <div>
            <dt className="text-xs uppercase tracking-wide text-zinc-500">{text.startsOn}</dt>
            <dd className="mt-1 text-zinc-900">{plainDate(admission.startsOn, language)}</dd>
          </div>
        )}
        {admission.funding.length > 0 && (
          <div className="sm:col-span-2">
            <dt className="text-xs uppercase tracking-wide text-zinc-500">{text.funding}</dt>
            <dd className="mt-1 text-zinc-900">
              <ul className="space-y-1">
                {admission.funding.map((entry, index) => (
                  <li key={index}>
                    {text.loads[entry.load]} — {entry.paid ? text.paid : text.free}
                    {entry.prices.length > 0 && ": "}
                    {entry.prices.map((price, priceIndex) => (
                      <span key={priceIndex}>
                        {priceIndex > 0 && "; "}
                        {price.amount.toLocaleString(language)} {price.currency}{" "}
                        {price.period === "other" ? (
                          <span lang={estonian}>{price.periodText}</span>
                        ) : (
                          text.periods[price.period]
                        )}
                        {price.target && (
                          <>
                            {" ("}
                            <span lang={estonian}>{price.target}</span>
                            {")"}
                          </>
                        )}
                      </span>
                    ))}
                  </li>
                ))}
              </ul>
            </dd>
          </div>
        )}
      </dl>
      {state === "past" && <p className="mt-4 text-sm leading-relaxed text-zinc-600">{text.pastNote}</p>}
      <p className="mt-2 text-xs leading-relaxed text-zinc-500">
        {interpolate(dict.programme.detailsSource, {
          source: sourceHost(admission.saisUrl) ?? "",
          date: tallinnDate(admission.detailsFetchedAt, language),
        })}
        {saisUrl && (
          <>
            {" "}
            <a href={saisUrl} target="_blank" rel="noopener noreferrer" className="underline">
              {dict.catalog.sourceLinkLabel}
            </a>
          </>
        )}
      </p>
    </section>
  );
}
