"use client";

import { useMemo, useState } from "react";
import { Input, Radio, RadioGroup } from "@heroui/react";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import {
  calculateScore,
  extraKey,
  type ExamLevel,
  type ExamResult,
  type FormulaGate,
  type FormulaTerm,
} from "@/lib/formula";

const LEVELS: ExamLevel[] = ["augstakais", "optimalais", "vispaarigais"];

type SubjectInput = { percent: string; level: ExamLevel };

function subjectLabel(dict: Dictionary, subject: string): string {
  const known = dict.survey.exams.subjects as Record<string, string>;
  return known[subject] ?? subject;
}

function termLabel(dict: Dictionary, term: FormulaTerm): string {
  if (term.kind === "ce" && term.subject) return subjectLabel(dict, term.subject);
  const known = dict.calculator.termKinds as Record<string, string>;
  // Именованное испытание (RTU Rīgas Biznesa skola: несколько разных
  // entrance_exam в одной формуле) — своя метка по составному ключу;
  // безымянное (Вентспилс) — просто по виду термина.
  if (term.subject) return known[`${term.kind}_${term.subject}`] ?? term.subject;
  return known[term.kind] ?? term.kind;
}

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

  const [inputs, setInputs] = useState<Record<string, SubjectInput>>(() =>
    Object.fromEntries(subjects.map((subject) => [subject, { percent: "", level: "augstakais" as ExamLevel }])),
  );
  const [extraInputs, setExtraInputs] = useState<Record<string, string>>(() =>
    Object.fromEntries(extraTerms.map((term) => [extraKey(term), ""])),
  );

  const examResults: ExamResult[] = subjects.flatMap((subject) => {
    const value = inputs[subject];
    const percent = Number(value.percent);
    if (value.percent === "" || Number.isNaN(percent)) return [];
    return [{ subject, percent, level: value.level }];
  });

  const extras: Record<string, number> = {};
  for (const term of extraTerms) {
    const key = extraKey(term);
    const value = Number(extraInputs[key]);
    if (extraInputs[key] !== "" && !Number.isNaN(value)) extras[key] = value;
  }

  const result = calculateScore(terms, gates, examResults, levelCoefficients, extras);

  return (
    <div className="mt-8">
      <div className="space-y-5">
        {subjects.map((subject) => (
          <div key={subject} className="flex flex-wrap items-center gap-4">
            <span className="w-40 shrink-0 text-sm font-medium text-zinc-700">
              {subjectLabel(dict, subject)}
            </span>
            <Input
              type="number"
              min={0}
              max={100}
              size="sm"
              className="w-24"
              value={inputs[subject].percent}
              onValueChange={(value) =>
                setInputs((prev) => ({ ...prev, [subject]: { ...prev[subject], percent: value } }))
              }
              endContent={<span className="text-zinc-400">%</span>}
            />
            <RadioGroup
              orientation="horizontal"
              size="sm"
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
          </div>
        ))}

        {extraTerms.map((term) => {
          const key = extraKey(term);
          return (
            <div key={key} className="flex flex-wrap items-center gap-4">
              <span className="w-40 shrink-0 text-sm font-medium text-zinc-700">{termLabel(dict, term)}</span>
              {/* Без max: у разных вузов эти слагаемые на разных сырых
                  шкалах — ЛУ где-то (5×100=500) даёт вход 0–100, а где-то
                  (0,4×1000=400) — 0–1000. Единого ограничения нет. */}
              <Input
                type="number"
                min={0}
                size="sm"
                className="w-24"
                value={extraInputs[key]}
                onValueChange={(value) => setExtraInputs((prev) => ({ ...prev, [key]: value }))}
              />
            </div>
          );
        })}
      </div>

      <div className="mt-8 rounded-xl bg-zinc-50 p-6">
        <p className="text-sm text-zinc-500">{dict.calculator.totalLabel}</p>
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
