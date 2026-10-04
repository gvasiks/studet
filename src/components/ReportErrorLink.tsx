import type { Dictionary } from "@/i18n/dictionaries";
import { interpolate } from "@/lib/outcomes";
import { buildReportMailto, getReportEmail } from "@/lib/report";

// Ссылка «Заметил ошибку? Напиши нам» — серверный компонент, обычный
// mailto. В письмо заранее подставлены тема и адрес страницы; что именно
// неверно, человек пишет сам. Пока адрес не задан в окружении
// (FEEDBACK_EMAIL или PRIVACY_CONTACT_EMAIL), компонент ничего не выводит.
export function ReportErrorLink({
  dict,
  programmeName,
  universityName,
  pageUrl,
}: {
  dict: Dictionary;
  programmeName: string;
  universityName: string;
  pageUrl: string;
}) {
  const email = getReportEmail();
  if (!email) return null;

  const subject = interpolate(dict.report.subject, { programme: programmeName, university: universityName });
  const body = interpolate(dict.report.body, { url: pageUrl });

  return (
    <p className="mt-4 text-sm text-zinc-600">
      <a href={buildReportMailto(email, subject, body)} className="font-medium text-zinc-900 underline">
        {dict.report.link}
      </a>{" "}
      {dict.report.hint}
    </p>
  );
}
