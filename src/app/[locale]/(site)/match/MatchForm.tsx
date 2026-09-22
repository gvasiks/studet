"use client";

import Link from "next/link";
import { useState } from "react";
import { Input } from "@heroui/react";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import type { ExamLevel, ExamResult } from "@/lib/formula";
import { matchProgrammes, matchRequirements, type MatchItem, type MatchStatus } from "@/lib/match";
import type { MatchFormula, MatchRequirement, RequirementMatchItem } from "@/lib/match";
import { interpolate } from "@/lib/outcomes";
import { subjectLabel, termLabel } from "@/lib/term-labels";
import { ArrowRightIcon, CheckIcon, InfoIcon } from "@/components/icons";

const LEVELS: ExamLevel[] = ["augstakais", "optimalais", "vispaarigais"];

type SubjectInput = { percent: string; level: ExamLevel };

// Порядок групп на экране после "можно посчитать" и "атбилст прасибам"
// (эта — не MatchStatus, у неё свой блок и в счётчиках, и в результатах,
// см. ниже) — остальные три статуса формулы, от красного к серому.
const TAIL_STATUSES: MatchStatus[] = ["gate_failed", "missing_extras", "missing_exams"];

// Статус — главное, что несёт эта страница, поэтому он закодирован не только
// текстом заголовка: у каждой группы свой цвет полосы и метки. Классы записаны
// целиком, а не собираются из кусков: Tailwind читает исходник, а не значения
// во время работы.
// edge — та же полоса, но как левая граница: в <dl> внутри обёртки могут лежать
// только <dt>/<dd>, отдельный <span> для полосы там недопустим (axe: dlitem).
const GROUP_STYLE: Record<
  MatchStatus,
  { bar: string; edge: string; chip: string; key: "computed" | "gateFailed" | "missingExtras" | "missingExams" }
> = {
  computed: { bar: "bg-emerald-500", edge: "border-emerald-500", chip: "bg-emerald-50 text-emerald-800", key: "computed" },
  gate_failed: { bar: "bg-red-400", edge: "border-red-400", chip: "bg-red-50 text-red-800", key: "gateFailed" },
  missing_extras: { bar: "bg-amber-400", edge: "border-amber-400", chip: "bg-amber-50 text-amber-900", key: "missingExtras" },
  missing_exams: { bar: "bg-zinc-300", edge: "border-zinc-300", chip: "bg-zinc-100 text-zinc-700", key: "missingExams" },
};

// "Атбилст прасибам" — не MatchStatus (это НЕ формула, счёта нет вовсе),
// поэтому свой стиль рядом, не внутри GROUP_STYLE. Синий, не зелёный:
// не путать с "можно посчитать балл" (computed) — это более бедный ответ.
const REQUIREMENTS_STYLE = { bar: "bg-sky-500", edge: "border-sky-500", chip: "bg-sky-50 text-sky-800" };

export function MatchForm({
  dict,
  locale,
  formulas,
  requirements,
  levelCoefficients,
  isFixture,
}: {
  dict: Dictionary;
  locale: Locale;
  formulas: MatchFormula[];
  requirements: MatchRequirement[];
  levelCoefficients: Record<ExamLevel, number>;
  isFixture: boolean;
}) {
  const subjects = Object.keys(dict.survey.exams.subjects);
  const t = dict.match;

  // Всё состояние — только в памяти этой страницы: ни в URL, ни в
  // localStorage, ни на сервер (экзамены несовершеннолетних, CLAUDE.md)
  const [inputs, setInputs] = useState<Record<string, SubjectInput>>(() =>
    Object.fromEntries(subjects.map((subject) => [subject, { percent: "", level: "augstakais" as ExamLevel }])),
  );

  const exams: ExamResult[] = subjects.flatMap((subject) => {
    const value = inputs[subject];
    const percent = Number(value.percent);
    if (value.percent === "" || Number.isNaN(percent) || percent < 0 || percent > 100) return [];
    return [{ subject, percent, level: value.level }];
  });

  // Без useMemo: формул десятки-сотни, счёт мгновенный, а зависимость от
  // пересобираемого на каждый рендер списка экзаменов только запутала бы код
  const groups = matchProgrammes(formulas, exams, levelCoefficients);
  const eligibleByRequirements = matchRequirements(requirements, exams);

  const summary = interpolate(t.summary, {
    computed: groups.computed.length,
    eligible: eligibleByRequirements.length,
    missingExams: groups.missing_exams.length,
    missingExtras: groups.missing_extras.length,
    gateFailed: groups.gate_failed.length,
  });

  return (
    <div>
      {isFixture && (
        <p className="mb-6 flex items-start gap-2 rounded-2xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-900" role="note">
          <InfoIcon size={16} className="mt-0.5 shrink-0" />
          {t.testData}
        </p>
      )}

      {/* Ввод экзаменов — форма, поэтому HeroUI здесь уместен (правило 4). */}
      <section aria-labelledby="match-exams" className="surface p-6 sm:p-8">
        <h2 id="match-exams" className="text-lg font-semibold tracking-tight text-zinc-900">
          {t.examsHeading}
        </h2>
        <p className="mt-1 max-w-[65ch] text-sm text-zinc-600">{t.examsHint}</p>

        {/* Сетка вместо одиннадцати строк в столбик: большинство сдаёт
            три-четыре предмета, и им нужно видеть весь список сразу, а не
            прокручивать его. Заполненное поле подсвечено — так виден прогресс. */}
        <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {subjects.map((subject) => {
            const filled = inputs[subject].percent !== "";
            return (
              <div
                key={subject}
                className={`rounded-2xl border p-3 transition-colors ${
                  filled ? "border-brand/40 bg-brand-soft/40" : "border-zinc-200 bg-white"
                }`}
              >
                <span className="block text-sm font-medium leading-snug text-zinc-800">
                  {subjectLabel(dict, subject)}
                </span>
                <div className="mt-2 flex items-center gap-2">
                  <Input
                    type="number"
                    min={0}
                    max={100}
                    size="sm"
                    className="w-[5.5rem] shrink-0"
                    aria-label={`${subjectLabel(dict, subject)}, ${t.percentSuffix}`}
                    value={inputs[subject].percent}
                    onValueChange={(value) =>
                      setInputs((prev) => ({ ...prev, [subject]: { ...prev[subject], percent: value } }))
                    }
                    endContent={<span className="text-zinc-500">{t.percentSuffix}</span>}
                  />
                  <select
                    className="h-9 min-w-0 flex-1 rounded-lg border border-zinc-300 bg-white px-2 text-sm text-zinc-900 shadow-control"
                    aria-label={`${subjectLabel(dict, subject)}, ${t.levelLabel}`}
                    value={inputs[subject].level}
                    onChange={(event) =>
                      setInputs((prev) => ({
                        ...prev,
                        [subject]: { ...prev[subject], level: event.target.value as ExamLevel },
                      }))
                    }
                  >
                    {LEVELS.map((level) => (
                      <option key={level} value={level}>
                        {dict.calculator.levels[level]}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            );
          })}
        </div>

        <p className="mt-5 flex items-start gap-2 border-t border-zinc-100 pt-4 text-xs leading-relaxed text-zinc-600">
          <InfoIcon size={14} className="mt-px shrink-0 text-zinc-400" />
          {t.privacy}
        </p>
      </section>

      {/* Сводка — счётчики по группам: одной строкой прозой её не прочитать,
          а именно она отвечает на вопрос страницы. Текст из словаря остаётся
          для скринридера и как объяснение цифр. */}
      <div className="mt-6" role="status" aria-live="polite">
        {exams.length === 0 ? (
          <p className="surface p-6 text-zinc-600 sm:p-8">{t.emptyNoExams}</p>
        ) : (
          <div className="surface p-6 sm:p-8">
            <dl className="grid grid-cols-2 gap-4 sm:grid-cols-5">
              <div className={`min-w-0 border-l-4 pl-3 ${GROUP_STYLE.computed.edge}`}>
                <dt className="text-xs font-medium leading-snug text-zinc-500">{dict.match.groups.computed}</dt>
                <dd className="mt-0.5 text-2xl font-bold tabular-nums tracking-tight text-zinc-900">
                  {groups.computed.length}
                </dd>
              </div>
              <div className={`min-w-0 border-l-4 pl-3 ${REQUIREMENTS_STYLE.edge}`}>
                <dt className="text-xs font-medium leading-snug text-zinc-500">
                  {dict.match.groups.eligibleByRequirements}
                </dt>
                <dd className="mt-0.5 text-2xl font-bold tabular-nums tracking-tight text-zinc-900">
                  {eligibleByRequirements.length}
                </dd>
              </div>
              {TAIL_STATUSES.map((status) => {
                const style = GROUP_STYLE[status];
                return (
                  <div key={status} className={`min-w-0 border-l-4 pl-3 ${style.edge}`}>
                    <dt className="text-xs font-medium leading-snug text-zinc-500">
                      {dict.match.groups[style.key]}
                    </dt>
                    <dd className="mt-0.5 text-2xl font-bold tabular-nums tracking-tight text-zinc-900">
                      {groups[status].length}
                    </dd>
                  </div>
                );
              })}
            </dl>
            <p className="mt-5 border-t border-zinc-100 pt-4 text-sm text-zinc-600">{summary}</p>
          </div>
        )}
      </div>

      {exams.length > 0 && (
        <>
          {groups.computed.length > 0 && (
            <ResultGroup
              status="computed"
              items={groups.computed}
              dict={dict}
              locale={locale}
              isFixture={isFixture}
              notComparable={t.notComparable}
            />
          )}
          {eligibleByRequirements.length > 0 && (
            <RequirementGroup items={eligibleByRequirements} dict={dict} locale={locale} isFixture={isFixture} />
          )}
          {TAIL_STATUSES.map((status) =>
            groups[status].length > 0 ? (
              <ResultGroup
                key={status}
                status={status}
                items={groups[status]}
                dict={dict}
                locale={locale}
                isFixture={isFixture}
                notComparable={t.notComparable}
              />
            ) : null,
          )}
          <p className="mt-8 max-w-[70ch] text-xs leading-relaxed text-zinc-600">{dict.calculator.disclaimer}</p>
        </>
      )}
    </div>
  );
}

function ResultGroup({
  status,
  items,
  dict,
  locale,
  isFixture,
  notComparable,
}: {
  status: MatchStatus;
  items: MatchItem[];
  dict: Dictionary;
  locale: Locale;
  isFixture: boolean;
  notComparable: string;
}) {
  const style = GROUP_STYLE[status];
  const hint = dict.match.groups[`${style.key}Hint` as keyof typeof dict.match.groups];
  const headingId = `match-group-${status}`;

  // Программы одного вуза — вместе, под названием вуза (шкалы у вузов разные)
  const byUniversity = new Map<string, MatchItem[]>();
  for (const item of items) {
    const list = byUniversity.get(item.formula.universityName) ?? [];
    list.push(item);
    byUniversity.set(item.formula.universityName, list);
  }

  return (
    <section aria-labelledby={headingId} className="surface mt-6 overflow-hidden">
      <div className="flex gap-4 border-b border-zinc-100 p-6 sm:p-8">
        <span aria-hidden="true" className={`w-1 shrink-0 rounded-full ${style.bar}`} />
        <div className="min-w-0">
          <h2 id={headingId} className="flex flex-wrap items-baseline gap-2 text-lg font-semibold tracking-tight text-zinc-900">
            {dict.match.groups[style.key]}
            <span className={`rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${style.chip}`}>
              {items.length}
            </span>
          </h2>
          <p className="mt-1 max-w-[65ch] text-sm leading-relaxed text-zinc-600">{hint}</p>
          {/* Предупреждение о несравнимости шкал стоит там, где показаны сами
              баллы, а не общей строкой наверху страницы. */}
          {status === "computed" && (
            <p className="mt-3 flex items-start gap-2 rounded-xl bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-900">
              <InfoIcon size={14} className="mt-px shrink-0" />
              {notComparable}
            </p>
          )}
        </div>
      </div>

      <div className="divide-y divide-zinc-100">
        {[...byUniversity.entries()].map(([universityName, universityItems]) => (
          <div key={universityName} className="px-6 py-5 sm:px-8">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">{universityName}</h3>
            <ul className="mt-3 space-y-3">
              {universityItems.map((item) => (
                <ResultRow key={item.formula.formulaId} item={item} dict={dict} locale={locale} isFixture={isFixture} />
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

function ResultRow({
  item,
  dict,
  locale,
  isFixture,
}: {
  item: MatchItem;
  dict: Dictionary;
  locale: Locale;
  isFixture: boolean;
}) {
  const t = dict.match;
  const { formula } = item;
  const programmeHref = `/${locale}/programmes/${formula.universitySlug}/${formula.programmeSlug}`;

  return (
    <li className="rounded-2xl border border-zinc-200 p-4">
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        {isFixture ? (
          <span className="min-w-0 flex-1 font-medium leading-snug text-zinc-900">{formula.programmeName}</span>
        ) : (
          <Link
            href={programmeHref}
            className="min-w-0 flex-1 font-medium leading-snug text-zinc-900 hover:text-brand"
          >
            {formula.programmeName}
          </Link>
        )}
        {/* Балл — то, за чем пришли: крупно, моноширинными цифрами, справа. */}
        {item.score && (
          <span className="shrink-0 text-right">
            <span className="block text-[10px] font-medium uppercase tracking-wide text-zinc-500">{t.scoreLabel}</span>
            <strong className="block text-2xl font-bold leading-tight tabular-nums tracking-tight text-zinc-900">
              {item.score.total.toFixed(2)}
            </strong>
          </span>
        )}
      </div>

      {item.status === "missing_exams" && (
        <p className="mt-2 text-sm leading-relaxed text-zinc-700">
          <span className="font-medium">{t.missingPrefix}</span>
          {": "}
          {item.missingSubjects.map((subject) => subjectLabel(dict, subject)).join(", ")}
        </p>
      )}
      {item.status === "missing_extras" && (
        <p className="mt-2 text-sm leading-relaxed text-zinc-700">
          <span className="font-medium">{t.extrasPrefix}</span>
          {": "}
          {item.missingExtras.map((term) => termLabel(dict, term)).join(", ")}
          {!isFixture && (
            <>
              {" · "}
              <Link
                href={`${programmeHref}/calculator`}
                className="inline-flex items-center gap-1 font-medium text-brand hover:text-brand-dark"
              >
                {t.openCalculator}
                <ArrowRightIcon size={12} />
              </Link>
            </>
          )}
        </p>
      )}
      {item.status === "gate_failed" && (
        <p className="mt-2 flex items-start gap-2 rounded-xl bg-red-50 px-3 py-2 text-sm leading-relaxed text-red-800">
          <span>
            <span className="font-medium">{t.gateFailedPrefix}</span>
            {": "}
            {item.failedGates.map((gate) => `${subjectLabel(dict, gate.subject)} ≥ ${gate.minPercent}%`).join(", ")}
          </span>
        </p>
      )}

      {item.score && (
        <details className="group mt-3 border-t border-zinc-100 pt-3">
          <summary className="flex cursor-pointer list-none items-center gap-1.5 text-sm font-medium text-zinc-700 hover:text-brand">
            <ArrowRightIcon size={13} className="shrink-0 transition-transform group-open:rotate-90" />
            {t.breakdown}
          </summary>
          <dl className="mt-3 space-y-1.5 text-sm">
            {item.score.lines.map((line, index) => (
              <div key={index} className="flex justify-between gap-4 border-b border-dashed border-zinc-100 pb-1.5 last:border-0">
                <dt className="text-zinc-600">{termLabel(dict, line.term)}</dt>
                <dd className="shrink-0 font-medium tabular-nums text-zinc-900">{line.points.toFixed(2)}</dd>
              </div>
            ))}
          </dl>
          {/* Дата проверки и ссылка на норму рядом с числом — правило 5. */}
          <p className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-zinc-600">
            <CheckIcon size={13} className="shrink-0 text-emerald-600" />
            <span>
              {dict.catalog.verifiedPrefix} {new Date(formula.verifiedAt).toLocaleDateString(locale)}
            </span>
            {formula.sourceUrl && (
              <a
                href={formula.sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-brand hover:underline"
              >
                {dict.catalog.sourceLinkLabel}
                <ArrowRightIcon size={11} className="-rotate-45" />
              </a>
            )}
          </p>
        </details>
      )}
    </li>
  );
}

// Программы без формулы, но с подтверждёнными требованиями (план
// 2026-09-21, пункт 02) — своя, более бедная карточка: нет балла, нет
// разбора, нет ссылки на калькулятор программы (калькулятора без формулы
// не существует). Структурно повторяет ResultGroup (группировка по вузу),
// но не переиспользует её: типы разные (RequirementMatchItem — не MatchItem).
function RequirementGroup({
  items,
  dict,
  locale,
  isFixture,
}: {
  items: RequirementMatchItem[];
  dict: Dictionary;
  locale: Locale;
  isFixture: boolean;
}) {
  const t = dict.match;
  const headingId = "match-group-eligible-requirements";

  const byUniversity = new Map<string, RequirementMatchItem[]>();
  for (const item of items) {
    const list = byUniversity.get(item.requirement.universityName) ?? [];
    list.push(item);
    byUniversity.set(item.requirement.universityName, list);
  }

  return (
    <section aria-labelledby={headingId} className="surface mt-6 overflow-hidden">
      <div className="flex gap-4 border-b border-zinc-100 p-6 sm:p-8">
        <span aria-hidden="true" className={`w-1 shrink-0 rounded-full ${REQUIREMENTS_STYLE.bar}`} />
        <div className="min-w-0">
          <h2 id={headingId} className="flex flex-wrap items-baseline gap-2 text-lg font-semibold tracking-tight text-zinc-900">
            {t.groups.eligibleByRequirements}
            <span className={`rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${REQUIREMENTS_STYLE.chip}`}>
              {items.length}
            </span>
          </h2>
          <p className="mt-1 max-w-[65ch] text-sm leading-relaxed text-zinc-600">{t.groups.eligibleByRequirementsHint}</p>
        </div>
      </div>

      <div className="divide-y divide-zinc-100">
        {[...byUniversity.entries()].map(([universityName, universityItems]) => (
          <div key={universityName} className="px-6 py-5 sm:px-8">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-500">{universityName}</h3>
            <ul className="mt-3 space-y-2">
              {universityItems.map((item) => (
                <RequirementRow key={item.requirement.requirementId} item={item} locale={locale} isFixture={isFixture} dict={dict} />
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

function RequirementRow({
  item,
  dict,
  locale,
  isFixture,
}: {
  item: RequirementMatchItem;
  dict: Dictionary;
  locale: Locale;
  isFixture: boolean;
}) {
  const { requirement } = item;
  const programmeHref = `/${locale}/programmes/${requirement.universitySlug}/${requirement.programmeSlug}`;

  return (
    <li className="rounded-2xl border border-zinc-200 p-4">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
        {isFixture ? (
          <span className="min-w-0 flex-1 font-medium leading-snug text-zinc-900">{requirement.programmeName}</span>
        ) : (
          <Link href={programmeHref} className="min-w-0 flex-1 font-medium leading-snug text-zinc-900 hover:text-brand">
            {requirement.programmeName}
          </Link>
        )}
      </div>
      <p className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-zinc-600">
        <CheckIcon size={13} className="shrink-0 text-emerald-600" />
        <span>
          {dict.catalog.verifiedPrefix} {new Date(requirement.verifiedAt).toLocaleDateString(locale)}
        </span>
        {requirement.sourceUrl && (
          <a
            href={requirement.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-brand hover:underline"
          >
            {dict.catalog.sourceLinkLabel}
            <ArrowRightIcon size={11} className="-rotate-45" />
          </a>
        )}
      </p>
    </li>
  );
}
