import type { Dictionary } from "@/i18n/dictionaries";
import { formatDate } from "@/lib/dates";
import { httpUrl } from "@/lib/application-channel";
import {
  checklistSources,
  checklistStorageKey,
  groupByStage,
  type DocumentRequirement,
} from "@/lib/foreign-documents";
import { DocumentChecklistItems, type ChecklistGroup } from "@/components/DocumentChecklistItems";

// «Documents to prepare» на карточке английской программы (docs/PLAN-
// FOREIGNERS.md, шаг 3). Серверный компонент: подписи собираются здесь, в
// клиентский островок уходят готовые строки — словарь в бандл не попадает.
// Сюда приходят только подтверждённые человеком строки (решение владельца
// 2026-11-14); под списком — источники и дата проверки (правило 5).

export function ForeignDocuments({
  dict,
  language,
  universitySlug,
  degreeLevel,
  items,
}: {
  dict: Dictionary;
  language: string;
  universitySlug: string;
  degreeLevel: string;
  items: DocumentRequirement[];
}) {
  const t = dict.programme.foreignDocuments;
  const groups: ChecklistGroup[] = groupByStage(items).map((group) => ({
    title: t.stages[group.stage],
    items: group.items.map((item) => ({
      id: `${item.document}:${item.appliesTo}`,
      label: t.documents[item.document],
      condition: item.appliesTo === "all" ? null : t.conditions[item.appliesTo],
      note: item.note,
    })),
  }));
  const sources = checklistSources(items);

  return (
    <section className="mt-8" aria-labelledby="foreign-documents">
      <h2 id="foreign-documents" className="text-xs uppercase tracking-wide text-zinc-500">
        {t.title}
      </h2>
      <p className="mt-2 text-sm text-zinc-600">{t.intro}</p>
      <div className="mt-3 rounded-2xl border border-zinc-200 p-4">
        <DocumentChecklistItems
          storageKey={checklistStorageKey(universitySlug, degreeLevel)}
          groups={groups}
          progressTemplate={t.progress}
          notesLanguage="en"
        />
      </div>
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
