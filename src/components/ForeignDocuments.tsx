import Link from "next/link";
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
// Тот же блок стоит на странице /student-documents (все вузы): там заголовок
// — уровень обучения (h3), а отметки общие с карточкой — ключ тот же.

export function ForeignDocuments({
  dict,
  language,
  universitySlug,
  degreeLevel,
  items,
  english,
  heading,
  headingId = "foreign-documents",
  englishByProgramme = null,
  allHref = null,
}: {
  dict: Dictionary;
  language: string;
  universitySlug: string;
  degreeLevel: string;
  items: DocumentRequirement[];
  english: EnglishRequirement | null;
  /** Заголовок h3 вместо h2 «Documents to prepare» (страница всех вузов). */
  heading?: string;
  headingId?: string;
  /** Требования к английскому у вуза по программам: ссылка на каталог вместо цифр. */
  englishByProgramme?: string | null;
  /** Ссылка «все вузы» под списком на карточке. */
  allHref?: string | null;
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
  // внутренние заголовки на ступень ниже заголовка блока: h3 на карточке, h4 на странице всех вузов
  const Inner = heading ? "h4" : "h3";
  const Root = heading ? "div" : "section";
  const sources = checklistSources(items);
  const englishLines = english ? englishTests(english, t.english, language) : [];
  const englishSource = english ? httpUrl(english.sourceUrl) : null;

  return (
    // На странице всех вузов блок уровня — не отдельная область: восемь областей
    // «Bachelor's studies» / «Master's studies» с одинаковыми названиями (axe: landmark-unique).
    <Root className={heading ? "mt-6" : "mt-8"} aria-labelledby={heading ? undefined : headingId}>
      {heading ? (
        <h3 id={headingId} className="text-base font-semibold text-zinc-900">
          {heading}
        </h3>
      ) : (
        <>
          <h2 id={headingId} className="text-xs uppercase tracking-wide text-zinc-600">
            {t.title}
          </h2>
          <p className="mt-2 text-sm text-zinc-600">{t.intro}</p>
        </>
      )}
      {!english && englishByProgramme && (
        <p className="mt-3 rounded-2xl bg-zinc-50 p-4 text-sm text-zinc-800">
          <Link href={englishByProgramme} className="font-medium text-brand-dark underline hover:text-brand">
            {t.english.byProgramme}
          </Link>
        </p>
      )}
      {english && englishLines.length > 0 && (
        <div className="mt-3 rounded-2xl bg-zinc-50 p-4 text-sm">
          <Inner className="font-semibold text-zinc-900">{t.english.title}</Inner>
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
          <p className="mt-1 text-xs leading-relaxed text-zinc-600">
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
          <Inner className="font-semibold text-zinc-900">{t.stages.by_university}</Inner>
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
      {/* На странице всех вузов эта оговорка стоит один раз вверху. */}
      {!heading && (
        <p className="mt-3 text-xs leading-relaxed text-zinc-600">
          {language !== "en" && <>{t.notesLanguage} </>}
          {t.more}
        </p>
      )}
      {sources.verifiedAt && (
        <p className="mt-1 text-xs leading-relaxed text-zinc-600">
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
      {allHref && (
        <Link href={allHref} className="mt-3 inline-block text-sm font-medium text-brand-dark underline hover:text-brand">
          {t.allLink}
        </Link>
      )}
    </Root>
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
