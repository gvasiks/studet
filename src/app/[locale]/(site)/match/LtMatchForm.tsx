"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Input, Radio, RadioGroup } from "@heroui/react";
import { languageOf, type Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { LtScoreBreakdown } from "@/components/LtScoreBreakdown";
import { normalize } from "@/lib/catalog-view";
import { parsePercent } from "@/lib/exam-input";
import { ltInputSubjects, ltScore, MIN_COUNTED_SCORE, type LtExams, type LtScore } from "@/lib/lt-score";
import type { LtMatchGroup, LtMatchProgramme } from "@/lib/lt-score-queries";
import { enumLabel } from "@/lib/names";
import { interpolate } from "@/lib/outcomes";

// Официальные страницы LAMA BPO: калькулятор (дополнительные баллы и
// окончательный расчёт) и объявление о порядке приёма (минимальные требования).
const OFFICIAL_CALCULATOR = "https://lamabpo.lt/pirmosios-pakopos-ir-vientisosios-studijos/konkursinio-balo-skaiciuokle/";
const MINIMUM_REQUIREMENTS = "https://lamabpo.lt/patvirtintas-2026-m-konkursiniu-eiliu-sudarymo-tvarkos-aprasas/";

const TWO_COURSE_SUBJECTS = new Set(["lithuanian", "mathematics"]);
// Сколько программ группы видно сразу; остальные — по кнопке.
const VISIBLE_PROGRAMMES = 8;

type SubjectInput = { score: string; course: "A" | "B" };
// Карточка результата: программы, у которых при введённых оценках балл и его
// разбор совпали полностью.
type Scored = {
  key: string;
  components: LtMatchGroup["components"];
  score: LtScore;
  complete: boolean;
  /** Каких составляющих не хватает — готовые строки для показа. */
  missing: string[];
  programmes: LtMatchProgramme[];
};

// Литовское «куда я прохожу». Правило расчёта в Литве одно на страну,
// поэтому балл считается не по программам, а по группам программ с
// одинаковым составом балла: сотни программ получают один и тот же балл, и
// показывать их одинаковыми строками незачем.
//
// Оценки живут только в памяти этой страницы: не в адресе, не в
// localStorage и не на сервере (экзамены несовершеннолетних, CLAUDE.md).
export function LtMatchForm({
  dict,
  locale,
  groups,
  withoutCalculator,
  admissionYear,
  checkedAt,
  sourceUrl,
}: {
  dict: Dictionary;
  locale: Locale;
  groups: LtMatchGroup[];
  withoutCalculator: number;
  admissionYear: number | null;
  checkedAt: string | null;
  sourceUrl: string | null;
}) {
  const text = dict.ltMatch;
  const calculator = dict.ltCalculator;
  const language = languageOf(locale);
  const subjects = useMemo(() => ltInputSubjects(groups.flatMap((group) => group.components)), [groups]);
  const [inputs, setInputs] = useState<Record<string, SubjectInput>>(() =>
    Object.fromEntries(subjects.map((subject) => [subject, { score: "", course: "A" as const }])),
  );
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const label = (subject: string) => calculator.subjects[subject as keyof typeof calculator.subjects] ?? subject;
  const number = (value: number) => value.toLocaleString(language, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  const parsed = subjects.map((subject) => {
    const value = parsePercent(inputs[subject].score);
    const invalid = value.state === "invalid" || (value.state === "ok" && value.value < MIN_COUNTED_SCORE);
    return { subject, value, invalid };
  });
  const hasInvalid = parsed.some((item) => item.invalid);
  const exams: LtExams = Object.fromEntries(
    parsed
      .filter((item) => item.value.state === "ok" && !item.invalid)
      .map((item) => [item.subject, { score: (item.value as { value: number }).value, course: inputs[item.subject].course }]),
  );
  const hasExams = Object.keys(exams).length > 0;

  // Чего не хватает составляющей: её номер и предметы, которые в неё подходят.
  const missingFor = (group: LtMatchGroup, score: LtScore) =>
    score.items
      .filter((item) => item.value === null)
      .map((item) => {
        const component = group.components.find((candidate) => candidate.position === item.position);
        const names = (component?.subjects ?? []).filter((subject) => subject !== "competence_assessment").map(label);
        const list =
          names.length > 4 ? `${names.slice(0, 4).join(" / ")}…` : names.join(component?.mode === "average" ? " + " : " / ");
        return `${interpolate(calculator.component, { n: String(item.position) })} (${list})`;
      });

  // Без useMemo: групп десятки, расчёт мгновенный.
  const needle = normalize(query.trim());
  // Составов балла в стране около тридцати, но при конкретных оценках многие
  // дают один и тот же балл с одним и тем же разбором (списки предметов «на
  // выбор» разные, а выбран один и тот же). Такие группы сливаются в одну
  // карточку — иначе шли бы подряд карточки с одинаковыми числами.
  const merged = new Map<string, Scored>();
  for (const group of groups) {
    const score = ltScore(group.components, exams);
    const programmes = needle
      ? group.programmes.filter((programme) => normalize(`${programme.name} ${programme.universityName}`).includes(needle))
      : group.programmes;
    if (programmes.length === 0) continue;
    const missing = missingFor(group, score);
    const key = JSON.stringify([score.items, missing]);
    const card = merged.get(key);
    if (card) card.programmes.push(...programmes);
    else {
      merged.set(key, {
        key,
        components: group.components,
        score,
        complete: missing.length === 0,
        missing,
        programmes: [...programmes],
      });
    }
  }
  const collator = new Intl.Collator(language, { sensitivity: "base", numeric: true });
  const scored = [...merged.values()]
    .map((card) => ({
      ...card,
      programmes: card.programmes.sort(
        (a, b) => collator.compare(a.name, b.name) || collator.compare(a.universityName, b.universityName),
      ),
    }))
    // Шкала одна на всю страну, поэтому по баллу сортировать можно (в
    // латвийском разделе так делать нельзя — там у каждого вуза своя шкала).
    .sort((a, b) => b.score.total - a.score.total);
  const complete = scored.filter((item) => item.complete);
  const partial = scored.filter((item) => !item.complete);
  const count = (items: Scored[]) => items.reduce((sum, item) => sum + item.programmes.length, 0);

  return (
    <div>
      {/* Ввод экзаменов — форма, поэтому HeroUI здесь уместен (правило 4). */}
      <section aria-labelledby="lt-match-exams" className="surface p-6 sm:p-8">
        <h2 id="lt-match-exams" className="text-lg font-semibold tracking-tight text-zinc-900">
          {dict.match.examsHeading}
        </h2>
        <p className="mt-1 max-w-[65ch] text-sm text-zinc-600">{dict.match.examsHint}</p>

        <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {parsed.map(({ subject, invalid }) => {
            const filled = inputs[subject].score !== "";
            const errorId = `lt-match-error-${subject}`;
            return (
              <div
                key={subject}
                className={`rounded-2xl border p-3 transition-colors ${
                  filled ? "border-brand/40 bg-brand-soft/40" : "border-zinc-200 bg-white"
                }`}
              >
                <span className="block text-sm font-medium leading-snug text-zinc-800">{label(subject)}</span>
                <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
                  <Input
                    type="text"
                    inputMode="decimal"
                    maxLength={5}
                    size="sm"
                    className="w-24"
                    aria-label={label(subject)}
                    aria-describedby={invalid ? errorId : undefined}
                    isInvalid={invalid}
                    value={inputs[subject].score}
                    onValueChange={(value) => setInputs((prev) => ({ ...prev, [subject]: { ...prev[subject], score: value } }))}
                  />
                  {TWO_COURSE_SUBJECTS.has(subject) && (
                    <RadioGroup
                      orientation="horizontal"
                      size="sm"
                      aria-label={`${label(subject)} — ${calculator.courseLabel}`}
                      value={inputs[subject].course}
                      onValueChange={(value) =>
                        setInputs((prev) => ({ ...prev, [subject]: { ...prev[subject], course: value as "A" | "B" } }))
                      }
                    >
                      <Radio value="A">A</Radio>
                      <Radio value="B">B</Radio>
                    </RadioGroup>
                  )}
                </div>
                {invalid && (
                  <p id={errorId} className="mt-2 text-sm text-red-700">
                    {calculator.invalid}
                  </p>
                )}
              </div>
            );
          })}
        </div>
        <p className="mt-4 text-xs leading-relaxed text-zinc-600">
          {text.courseHint} {dict.match.privacy}
        </p>
      </section>

      <section aria-labelledby="lt-match-results" className="mt-8">
        <h2 id="lt-match-results" className="sr-only">
          {text.resultsHeading}
        </h2>

        {!hasExams || hasInvalid ? (
          <p className="surface p-6 text-zinc-700">{hasInvalid ? dict.calculator.fixInvalid : dict.match.emptyNoExams}</p>
        ) : (
          <>
            <div className="surface p-6 sm:p-8">
              <p className="text-sm font-medium text-zinc-800" aria-live="polite">
                {interpolate(text.summary, { complete: count(complete), partial: count(partial) })}
              </p>
              <p className="mt-2 max-w-[70ch] text-sm leading-relaxed text-zinc-600">{text.sameScale}</p>
              <label className="mt-5 block text-sm font-medium text-zinc-800" htmlFor="lt-match-search">
                {text.searchLabel}
              </label>
              <input
                id="lt-match-search"
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="mt-1.5 h-10 w-full max-w-md rounded-xl border border-zinc-300 bg-white px-3 text-sm text-zinc-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
              />
            </div>

            {scored.length === 0 && <p className="surface mt-6 p-6 text-zinc-700">{text.emptySearch}</p>}

            {[
              { id: "complete", title: text.completeTitle, hint: text.completeHint, items: complete },
              { id: "partial", title: text.partialTitle, hint: text.partialHint, items: partial },
            ]
              .filter((block) => block.items.length > 0)
              .map((block) => (
                <div key={block.id} className="mt-8">
                  <h3 className="text-lg font-semibold tracking-tight text-zinc-900">
                    {block.title} <span className="font-normal text-zinc-600">· {count(block.items)}</span>
                  </h3>
                  <p className="mt-1 max-w-[70ch] text-sm text-zinc-600">{block.hint}</p>
                  <ul className="mt-4 space-y-4">
                    {block.items.map(({ key, components, score, missing, programmes }, index) => {
                      const open = expanded[key] ?? false;
                      const shown = open ? programmes : programmes.slice(0, VISIBLE_PROGRAMMES);
                      const listId = `lt-match-programmes-${block.id}-${index}`;
                      return (
                        <li key={key} className="surface p-5 sm:p-6">
                          <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
                            <p>
                              <span className="text-sm text-zinc-600">{calculator.totalLabel}: </span>
                              <span className="text-2xl font-bold tracking-tight tabular-nums text-zinc-900">{number(score.total)}</span>
                            </p>
                            <p className="text-sm text-zinc-600">{interpolate(text.programmes, { count: programmes.length })}</p>
                          </div>
                          {missing.length > 0 && (
                            <p className="mt-2 text-sm text-amber-900">
                              {text.missing} {missing.join("; ")}
                            </p>
                          )}

                          <details className="mt-3">
                            <summary className="cursor-pointer text-sm font-medium text-brand-dark">{calculator.breakdownTitle}</summary>
                            <div className="mt-3">
                              <LtScoreBreakdown dict={dict} language={language} components={components} items={score.items} />
                            </div>
                          </details>

                          <ul id={listId} className="mt-4 grid gap-x-6 gap-y-1.5 text-sm sm:grid-cols-2">
                            {shown.map((programme) => (
                              <li key={`${programme.universitySlug}/${programme.slug}`}>
                                <Link
                                  href={`/${locale}/programmes/${programme.universitySlug}/${programme.slug}`}
                                  className="text-zinc-900 underline decoration-zinc-300 underline-offset-2 hover:decoration-zinc-900"
                                >
                                  {programme.name}
                                </Link>
                                <span className="text-zinc-600">
                                  {" — "}
                                  {programme.universityName}
                                  {programme.city ? `, ${enumLabel(dict.catalog.city, programme.city)}` : ""}
                                </span>
                              </li>
                            ))}
                          </ul>
                          {programmes.length > VISIBLE_PROGRAMMES && (
                            <button
                              type="button"
                              aria-expanded={open}
                              aria-controls={listId}
                              onClick={() => setExpanded((prev) => ({ ...prev, [key]: !open }))}
                              className="mt-3 inline-flex h-9 items-center rounded-full border border-zinc-300 px-4 text-sm font-medium text-zinc-800 hover:bg-zinc-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
                            >
                              {open ? text.showLess : interpolate(text.showAll, { count: programmes.length })}
                            </button>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ))}
          </>
        )}
      </section>

      <div className="mt-8 space-y-3 text-sm leading-relaxed text-zinc-600">
        <p className="rounded-xl bg-amber-50 px-4 py-3 text-amber-900">
          {calculator.extrasNote}{" "}
          <a href={OFFICIAL_CALCULATOR} target="_blank" rel="noopener noreferrer" className="underline">
            {calculator.officialLink}
          </a>
        </p>
        <p>
          {text.minimum}{" "}
          <a href={MINIMUM_REQUIREMENTS} target="_blank" rel="noopener noreferrer" className="underline">
            {text.minimumSource}
          </a>
        </p>
        {withoutCalculator > 0 && <p>{interpolate(text.withoutCalculator, { count: withoutCalculator })}</p>}
        <p className="text-xs text-zinc-600">
          {admissionYear !== null && interpolate(calculator.rulesNote, { year: String(admissionYear) })}{" "}
          {checkedAt && interpolate(calculator.checkedNote, { date: new Date(checkedAt).toLocaleDateString(language) })}{" "}
          {sourceUrl && (
            <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="underline">
              {calculator.sourceLink}
            </a>
          )}
        </p>
        <p className="text-xs text-zinc-600">{calculator.decidedBy}</p>
      </div>
    </div>
  );
}
