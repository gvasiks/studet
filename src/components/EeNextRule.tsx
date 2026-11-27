import type { Language } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { EeAdmissionRule } from "@/components/EeAdmissionRule";
import { plainDate } from "@/lib/ee-admission";
import type { EeNextRule as NextRule } from "@/lib/ee-admission-queries";
import { interpolate } from "@/lib/outcomes";

// Условия приёма следующего учебного года из решения вуза (решение владельца
// 2026-11-27) — над блоком прошлого конкурса SAIS. Только факты правила
// приёма: пороги, места, есть ли рейтинг; ни расчёта, ни вывода о человеке.
// Подпись источника — у EeAdmissionRule («извлечено автоматически»).
// Серверный компонент, обычная разметка.

export function EeNextRule({ dict, language, next }: { dict: Dictionary; language: Language; next: NextRule }) {
  const text = dict.eeAdmission.next;
  const estonian = language === "et" ? undefined : "et";
  return (
    <section className="mt-8">
      <h2 className="text-xs uppercase tracking-wide text-zinc-500">{interpolate(text.title, { year: next.academicYear })}</h2>
      <p className="mt-3 text-sm leading-relaxed text-zinc-700">
        {interpolate(text.approved, { date: plainDate(next.decidedOn, language) })}{" "}
        <span lang={estonian}>{next.sourceTitle}</span>
      </p>
      {next.newCurriculum && <p className="mt-2 text-sm leading-relaxed text-zinc-700">{text.newCurriculum}</p>}
      <EeAdmissionRule dict={dict} language={language} rule={next.rule} sourceUrl={next.sourceUrl} extractedAt={next.extractedAt} />
      <p className="mt-4 text-sm leading-relaxed text-zinc-600">{interpolate(text.note, { year: next.academicYear })}</p>
    </section>
  );
}
