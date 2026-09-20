"use client";

import Link from "next/link";
import { useState } from "react";
import { Input } from "@heroui/react";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import type { ExamLevel, ExamResult } from "@/lib/formula";
import { matchProgrammes, type MatchItem, type MatchStatus } from "@/lib/match";
import type { MatchFormula } from "@/lib/match";
import { interpolate } from "@/lib/outcomes";
import { subjectLabel, termLabel } from "@/lib/term-labels";

const LEVELS: ExamLevel[] = ["augstakais", "optimalais", "vispaarigais"];

type SubjectInput = { percent: string; level: ExamLevel };

// Порядок групп на экране: сначала то, что уже можно посчитать
const GROUP_ORDER: MatchStatus[] = ["computed", "gate_failed", "missing_extras", "missing_exams"];

export function MatchForm({
  dict,
  locale,
  formulas,
  levelCoefficients,
  isFixture,
}: {
  dict: Dictionary;
  locale: Locale;
  formulas: MatchFormula[];
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

  const summary = interpolate(t.summary, {
    computed: groups.computed.length,
    missingExams: groups.missing_exams.length,
    missingExtras: groups.missing_extras.length,
    gateFailed: groups.gate_failed.length,
  });

  return (
    <div className="mt-8">
      {isFixture && (
        <p className="mb-6 rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-red-900" role="note">
          {t.testData}
        </p>
      )}

      <section aria-labelledby="match-exams">
        <h2 id="match-exams" className="text-lg font-semibold text-zinc-900">
          {t.examsHeading}
        </h2>
        <p className="mt-1 text-sm text-zinc-600">{t.examsHint}</p>

        <div className="mt-5 space-y-4">
          {subjects.map((subject) => (
            <div key={subject} className="flex flex-wrap items-center gap-3">
              <span className="w-44 shrink-0 text-sm font-medium text-zinc-800">{subjectLabel(dict, subject)}</span>
              <Input
                type="number"
                min={0}
                max={100}
                size="sm"
                className="w-24"
                aria-label={`${subjectLabel(dict, subject)}, ${t.percentSuffix}`}
                value={inputs[subject].percent}
                onValueChange={(value) =>
                  setInputs((prev) => ({ ...prev, [subject]: { ...prev[subject], percent: value } }))
                }
                endContent={<span className="text-zinc-500">{t.percentSuffix}</span>}
              />
              <select
                className="h-9 rounded-lg border border-zinc-300 bg-white px-2 text-sm text-zinc-900"
                aria-label={`${subjectLabel(dict, subject)}, ${t.levelLabel}`}
                value={inputs[subject].level}
                onChange={(event) =>
                  setInputs((prev) => ({ ...prev, [subject]: { ...prev[subject], level: event.target.value as ExamLevel } }))
                }
              >
                {LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {dict.calculator.levels[level]}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-zinc-600">{t.privacy}</p>
      </section>

      <div className="mt-8" role="status" aria-live="polite">
        {exams.length === 0 ? (
          <p className="text-zinc-600">{t.emptyNoExams}</p>
        ) : (
          <p className="text-sm font-medium text-zinc-800">{summary}</p>
        )}
      </div>

      {exams.length > 0 && (
        <>
          <p className="mt-3 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900">{t.notComparable}</p>
          {GROUP_ORDER.map((status) =>
            groups[status].length > 0 ? (
              <ResultGroup key={status} status={status} items={groups[status]} dict={dict} locale={locale} isFixture={isFixture} />
            ) : null,
          )}
          <p className="mt-8 text-xs text-zinc-600">{dict.calculator.disclaimer}</p>
        </>
      )}
    </div>
  );
}

const GROUP_TEXT: Record<MatchStatus, { title: "computed" | "gateFailed" | "missingExtras" | "missingExams" }> = {
  computed: { title: "computed" },
  gate_failed: { title: "gateFailed" },
  missing_extras: { title: "missingExtras" },
  missing_exams: { title: "missingExams" },
};

function ResultGroup({
  status,
  items,
  dict,
  locale,
  isFixture,
}: {
  status: MatchStatus;
  items: MatchItem[];
  dict: Dictionary;
  locale: Locale;
  isFixture: boolean;
}) {
  const key = GROUP_TEXT[status].title;
  const hint = dict.match.groups[`${key}Hint` as keyof typeof dict.match.groups];
  const headingId = `match-group-${status}`;

  // Программы одного вуза — вместе, под названием вуза (шкалы у вузов разные)
  const byUniversity = new Map<string, MatchItem[]>();
  for (const item of items) {
    const list = byUniversity.get(item.formula.universityName) ?? [];
    list.push(item);
    byUniversity.set(item.formula.universityName, list);
  }

  return (
    <section aria-labelledby={headingId} className="mt-8">
      <h2 id={headingId} className="text-lg font-semibold text-zinc-900">
        {dict.match.groups[key]} ({items.length})
      </h2>
      <p className="mt-1 text-sm text-zinc-600">{hint}</p>

      {[...byUniversity.entries()].map(([universityName, universityItems]) => (
        <div key={universityName} className="mt-4">
          <h3 className="text-sm font-semibold text-zinc-700">{universityName}</h3>
          <ul className="mt-2 divide-y divide-zinc-200 rounded-xl border border-zinc-200">
            {universityItems.map((item) => (
              <ResultRow key={item.formula.formulaId} item={item} dict={dict} locale={locale} isFixture={isFixture} />
            ))}
          </ul>
        </div>
      ))}
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
    <li className="p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        {isFixture ? (
          <span className="font-medium text-zinc-900">{formula.programmeName}</span>
        ) : (
          <Link href={programmeHref} className="font-medium text-zinc-900 underline-offset-2 hover:underline">
            {formula.programmeName}
          </Link>
        )}
        {item.score && (
          <span className="text-sm text-zinc-700">
            {t.scoreLabel}: <strong className="text-lg text-zinc-900">{item.score.total.toFixed(2)}</strong>
          </span>
        )}
      </div>

      {item.status === "missing_exams" && (
        <p className="mt-1 text-sm text-zinc-700">
          {t.missingPrefix}: {item.missingSubjects.map((subject) => subjectLabel(dict, subject)).join(", ")}
        </p>
      )}
      {item.status === "missing_extras" && (
        <p className="mt-1 text-sm text-zinc-700">
          {t.extrasPrefix}: {item.missingExtras.map((term) => termLabel(dict, term)).join(", ")}
          {!isFixture && (
            <>
              {" · "}
              <Link href={`${programmeHref}/calculator`} className="text-brand underline">
                {t.openCalculator}
              </Link>
            </>
          )}
        </p>
      )}
      {item.status === "gate_failed" && (
        <p className="mt-1 text-sm text-red-800">
          {t.gateFailedPrefix}:{" "}
          {item.failedGates.map((gate) => `${subjectLabel(dict, gate.subject)} ≥ ${gate.minPercent}%`).join(", ")}
        </p>
      )}

      {item.score && (
        <details className="mt-2 text-sm text-zinc-700">
          <summary className="cursor-pointer text-zinc-800">{t.breakdown}</summary>
          <dl className="mt-2 space-y-1">
            {item.score.lines.map((line, index) => (
              <div key={index} className="flex justify-between gap-4">
                <dt>{termLabel(dict, line.term)}</dt>
                <dd>{line.points.toFixed(2)}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-2 text-xs text-zinc-600">
            {dict.catalog.verifiedPrefix} {new Date(formula.verifiedAt).toLocaleDateString(locale)}
            {formula.sourceUrl && (
              <>
                {" · "}
                <a href={formula.sourceUrl} target="_blank" rel="noopener noreferrer" className="underline">
                  {dict.catalog.sourceLinkLabel}
                </a>
              </>
            )}
          </p>
        </details>
      )}
    </li>
  );
}
