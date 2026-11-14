import type { Dictionary } from "@/i18n/dictionaries";
import { formatDate } from "@/lib/dates";
import { httpUrl } from "@/lib/application-channel";
import {
  checklistSources,
  checklistStorageKey,
  groupByStage,
  type DocumentRequirement,
} from "@/lib/foreign-documents";
import { interpolate } from "@/lib/outcomes";
import type { EnglishRequirement } from "@/lib/english-requirement";
import { DocumentChecklistItems, type ChecklistGroup } from "@/components/DocumentChecklistItems";

// «Documents to prepare» на карточке английской программы (docs/PLAN-
// FOREIGNERS.md, шаг 3). Серверный компонент: подписи собираются здесь, в
// клиентский островок уходят готовые строки — словарь в бандл не попадает.
// Сюда приходят только подтверждённые человеком строки (решение владельца
// 2026-11-14); под списком — источники и дата проверки (правило 5).
// Сверху — минимум теста по английскому (шаг 4, правило 6: только подтверждённый).
// Этап by_university (вуз делает сам) — отдельным списком без отметок.

export function ForeignDocuments({
  dict,
  language,
  universitySlug,
  degreeLevel,
  items,
  english,
}: {
  dict: Dictionary;
  language: string;
  universitySlug: string;
  degreeLevel: string;
  items: DocumentRequirement[];
  english: EnglishRequirement | null;
}) {
  const t = dict.programme.foreignDocuments;
  const stages = groupByStage(items);
  const byUniversity = stages.find((group) => group.stage === "by_university")?.items ?? [];
  const groups: ChecklistGroup[] = stages.filter((group) => group.stage !== "by_university").map((group) => ({
    title: t.stages[group.stage],
    items: group.items.map((item) => ({
      id: `${item.document}:${item.appliesTo}`,
      label: t.documents[item.document],
      condition: item.appliesTo === "all" ? null : t.conditions[item.appliesTo],
      note: item.note,
    })),
  }));
  const sources = checklistSources(items);
  const englishLines = english ? englishTests(english, t.english, language) : [];
  const englishSource = english ? httpUrl(english.sourceUrl) : null;

  return (
    <section className="mt-8" aria-labelledby="foreign-documents">
      <h2 id="foreign-documents" className="text-xs uppercase tracking-wide text-zinc-500">
        {t.title}
      </h2>
      <p className="mt-2 text-sm text-zinc-600">{t.intro}</p>
      {english && englishLines.length > 0 && (
        <div className="mt-3 rounded-2xl bg-zinc-50 p-4 text-sm">
          <h3 className="font-semibold text-zinc-900">{t.english.title}</h3>
          <ul className="mt-1 text-zinc-800">
            {englishLines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          {english.note && (
            <p lang="en" className="mt-1 text-xs leading-relaxed text-zinc-600">
              {english.note}
            </p>
          )}
          <p className="mt-1 text-xs leading-relaxed text-zinc-500">
            {t.english.otherTests} {dict.catalog.verifiedPrefix}{" "}
            {formatDate(english.verifiedAt, language).replace(/\.?$/, ".")}
            {englishSource && (
              <>
                {" "}
                <a href={englishSource} target="_blank" rel="noopener noreferrer" className="underline">
                  {dict.catalog.sourceLinkLabel}
                </a>
              </>
            )}
          </p>
        </div>
      )}
      {groups.length > 0 && (
        <div className="mt-3 rounded-2xl border border-zinc-200 p-4">
          <DocumentChecklistItems
            storageKey={checklistStorageKey(universitySlug, degreeLevel)}
            groups={groups}
            progressTemplate={t.progress}
            notesLanguage="en"
          />
        </div>
      )}
      {byUniversity.length > 0 && (
        <div className="mt-3 rounded-2xl bg-zinc-50 p-4 text-sm">
          <h3 className="font-semibold text-zinc-900">{t.stages.by_university}</h3>
          <ul className="mt-2 space-y-2">
            {byUniversity.map((item) => (
              <li key={`${item.document}:${item.appliesTo}`} className="text-zinc-800">
                {t.documents[item.document]}
                {item.appliesTo !== "all" && <span className="text-zinc-600"> — {t.conditions[item.appliesTo]}</span>}
                {item.note && (
                  <span lang="en" className="mt-0.5 block text-xs leading-relaxed text-zinc-600">
                    {item.note}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      <p className="mt-3 text-xs leading-relaxed text-zinc-500">
        {language !== "en" && <>{t.notesLanguage} </>}
        {t.more}
      </p>
      {sources.verifiedAt && (
        <p className="mt-1 text-xs leading-relaxed text-zinc-500">
          {dict.catalog.verifiedPrefix} {formatDate(sources.verifiedAt, language).replace(/\.?$/, ".")} {t.sources}{" "}
          {sources.urls
            .map((url) => httpUrl(url))
            .filter((url): url is string => Boolean(url))
            .map((url, index) => (
              <span key={url}>
                {index > 0 && ", "}
                <a href={url} target="_blank" rel="noopener noreferrer" className="break-all underline">
                  {shortUrl(url)}
                </a>
              </span>
            ))}
        </p>
      )}
    </section>
  );
}

// «rtu.lv/en/studies/admission-1»: у одного вуза источников несколько, и
// по одному имени сайта ссылки не различить.
function shortUrl(url: string): string {
  try {
    const parsed = new URL(url);
    return `${parsed.hostname.replace(/^www\./, "")}${parsed.pathname.replace(/\/$/, "")}`;
  } catch {
    return url;
  }
}

// «IELTS 6,0», «TOEFL iBT 80 (or 4 on the scale used since 21 January 2026)».
function englishTests(
  english: EnglishRequirement,
  t: Dictionary["programme"]["foreignDocuments"]["english"],
  language: string,
): string[] {
  const decimal = new Intl.NumberFormat(language, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const plain = new Intl.NumberFormat(language, { maximumFractionDigits: 1 });
  const lines: string[] = [];
  if (english.ieltsMin !== null) lines.push(interpolate(t.ielts, { score: decimal.format(english.ieltsMin) }));
  if (english.toeflIbtMin !== null) {
    lines.push(
      english.toeflIbtBand !== null
        ? interpolate(t.toeflBand, { score: plain.format(english.toeflIbtMin), band: plain.format(english.toeflIbtBand) })
        : interpolate(t.toefl, { score: plain.format(english.toeflIbtMin) }),
    );
  }
  return lines;
}
