"use client";

import { useMemo, useState } from "react";
import { Input, Radio, RadioGroup } from "@heroui/react";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { parseNonNegative, parsePercent } from "@/lib/exam-input";
import {
  calculateScore,
  extraKey,
  type ExamLevel,
  type ExamResult,
  type FormulaGate,
  type FormulaTerm,
} from "@/lib/formula";
import { interpolate } from "@/lib/outcomes";
import { subjectLabel, termLabel } from "@/lib/term-labels";

const LEVELS: ExamLevel[] = ["augstakais", "optimalais", "vispaarigais"];

type SubjectInput = { percent: string; level: ExamLevel };

export function CalculatorForm({
  dict,
  terms,
  gates,
  levelCoefficients,
  sourceUrl,
  verifiedAt,
  locale,
}: {
  dict: Dictionary;
  terms: FormulaTerm[];
  gates: FormulaGate[];
  levelCoefficients: Record<ExamLevel, number>;
  sourceUrl: string | null;
  verifiedAt: string | null;
  locale: Locale;
}) {
  const subjects = useMemo(
    () => [...new Set(terms.filter((t) => t.kind === "ce" && t.subject).map((t) => t.subject as string))],
    [terms],
  );
  // certificate/entrance_exam — формула может нести несколько таких
  // слагаемых сразу (RTU Rīgas Biznesa skola: тест английского +
  // собеседование + тест математики — три разных числа), различаются
  // по extraKey (kind + subject-метка испытания).
  const extraTerms = useMemo(
    () => terms.filter((t) => t.kind === "certificate" || t.kind === "entrance_exam"),
    [terms],
  );
  // Экзамен обязателен, если хотя бы одно его слагаемое не помечено
  // «ja nav …, tad 0» (optional) — то же правило, что в match.ts.
  const requiredSubjects = useMemo(
    () => new Set(terms.filter((t) => t.kind === "ce" && t.subject && !t.optional).map((t) => t.subject as string)),
    [terms],
  );

  const [inputs, setInputs] = useState<Record<string, SubjectInput>>(() =>
    Object.fromEntries(subjects.map((subject) => [subject, { percent: "", level: "augstakais" as ExamLevel }])),
  );
  const [extraInputs, setExtraInputs] = useState<Record<string, string>>(() =>
    Object.fromEntries(extraTerms.map((term) => [extraKey(term), ""])),
  );

  const parsedSubjects = subjects.map((subject) => ({ subject, parsed: parsePercent(inputs[subject].percent) }));
  const parsedExtras = extraTerms.map((term) => {
    const key = extraKey(term);
    return { term, key, parsed: parseNonNegative(extraInputs[key]) };
  });

  const examResults: ExamResult[] = parsedSubjects.flatMap(({ subject, parsed }) =>
    parsed.state === "ok" ? [{ subject, percent: parsed.value, level: inputs[subject].level }] : [],
  );
  const extras: Record<string, number> = {};
  for (const { key, parsed } of parsedExtras) {
    if (parsed.state === "ok") extras[key] = parsed.value;
  }

  // Итог показывается, только когда введено всё обязательное и нет полей с
  // ошибкой. Раньше при пустом поле выводилось «0.00» или сумма без одного
  // экзамена — число, неотличимое от настоящего результата (аудит
  // 2026-10-04, пункт 2).
  const missing = [
    ...parsedSubjects
      .filter(({ subject, parsed }) => parsed.state === "empty" && requiredSubjects.has(subject))
      .map(({ subject }) => subjectLabel(dict, subject)),
    ...parsedExtras
      .filter(({ term, parsed }) => parsed.state === "empty" && !term.optional)
      .map(({ term }) => termLabel(dict, term)),
  ];
  const hasInvalid =
    parsedSubjects.some(({ parsed }) => parsed.state === "invalid") ||
    parsedExtras.some(({ parsed }) => parsed.state === "invalid");
  const result =
    missing.length === 0 && !hasInvalid ? calculateScore(terms, gates, examResults, levelCoefficients, extras) : null;

  return (
    <div className="mt-8">
      <div className="space-y-5">
        {parsedSubjects.map(({ subject, parsed }) => {
          const invalid = parsed.state === "invalid";
          const errorId = `calculator-error-${subject}`;
          return (
            <div key={subject} className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <span className="w-40 shrink-0 text-sm font-medium text-zinc-700">
                {subjectLabel(dict, subject)}
              </span>
              {/* Текстовое поле, а не type="number": так запятая в «72,5» не
                  теряется в браузере с английской локалью, а разбор — наш
                  (exam-input.ts). inputMode даёт цифровую клавиатуру на телефоне. */}
              <Input
                type="text"
                inputMode="decimal"
                maxLength={6}
                size="sm"
                className="w-24"
                // Видимый <span> рядом — не <label>, программно ни с чем
                // не связан; без aria-label скринридер объявил бы просто
                // "edit text" без указания предмета (ревью 2026-09,
                // пункт 15: "читаются ли подписи к полям калькулятора").
                aria-label={subjectLabel(dict, subject)}
                aria-describedby={invalid ? errorId : undefined}
                isInvalid={invalid}
                value={inputs[subject].percent}
                onValueChange={(value) =>
                  setInputs((prev) => ({ ...prev, [subject]: { ...prev[subject], percent: value } }))
                }
                endContent={<span className="text-zinc-500">%</span>}
              />
              <RadioGroup
                orientation="horizontal"
                size="sm"
                aria-label={subjectLabel(dict, subject)}
                value={inputs[subject].level}
                onValueChange={(value) =>
                  setInputs((prev) => ({ ...prev, [subject]: { ...prev[subject], level: value as ExamLevel } }))
                }
              >
                {LEVELS.map((level) => (
                  <Radio key={level} value={level}>
                    {dict.calculator.levels[level]}
                  </Radio>
                ))}
              </RadioGroup>
              {invalid && (
                <p id={errorId} className="basis-full text-sm text-red-700">
                  {dict.calculator.invalidPercent}
                </p>
              )}
            </div>
          );
        })}

        {parsedExtras.map(({ term, key, parsed }) => {
          const invalid = parsed.state === "invalid";
          const errorId = `calculator-error-${key}`;
          return (
            <div key={key} className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <span className="w-40 shrink-0 text-sm font-medium text-zinc-700">{termLabel(dict, term)}</span>
              {/* Без верхней границы: у разных вузов эти слагаемые на разных
                  сырых шкалах — ЛУ где-то (5×100=500) даёт вход 0–100, а где-то
                  (0,4×1000=400) — 0–1000. Единого ограничения нет. */}
              <Input
                type="text"
                inputMode="decimal"
                maxLength={8}
                size="sm"
                className="w-24"
                aria-label={termLabel(dict, term)}
                aria-describedby={invalid ? errorId : undefined}
                isInvalid={invalid}
                value={extraInputs[key]}
                onValueChange={(value) => setExtraInputs((prev) => ({ ...prev, [key]: value }))}
              />
              {invalid && (
                <p id={errorId} className="basis-full text-sm text-red-700">
                  {dict.calculator.invalidNumber}
                </p>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-8 rounded-xl bg-zinc-50 p-6">
        <p className="text-sm text-zinc-500">{dict.calculator.totalLabel}</p>
        {result ? (
          <>
            <p className="text-4xl font-bold tracking-tighter text-zinc-900">{result.total.toFixed(2)}</p>

            <dl className="mt-4 space-y-1 text-sm text-zinc-600">
              {result.lines.map((line, index) => (
                <div key={index} className="flex justify-between">
                  <dt>{termLabel(dict, line.term)}</dt>
                  <dd>{line.points.toFixed(2)}</dd>
                </div>
              ))}
            </dl>

            {result.failedGates.length > 0 && (
              <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">{dict.calculator.gateWarning}</p>
            )}
          </>
        ) : (
          <>
            <p className="text-4xl font-bold tracking-tighter text-zinc-500" aria-hidden="true">
              —
            </p>
            <p className="mt-2 text-sm text-zinc-700">
              {hasInvalid
                ? dict.calculator.fixInvalid
                : interpolate(dict.calculator.incomplete, { list: missing.join(", ") })}
            </p>
          </>
        )}
      </div>

      <p className="mt-6 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900">
        {verifiedAt
          ? `${dict.catalog.verifiedPrefix} ${new Date(verifiedAt).toLocaleDateString(locale)}`
          : dict.catalog.unverifiedLabel}
        {sourceUrl && (
          <>
            {" "}
            <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="underline">
              {dict.catalog.sourceLinkLabel}
            </a>
          </>
        )}
      </p>
      <p className="mt-4 text-xs text-zinc-500">{dict.calculator.disclaimer}</p>
    </div>
  );
}
