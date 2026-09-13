"use client";

import { useMemo, useState } from "react";
import { Input, Radio, RadioGroup } from "@heroui/react";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import {
  calculateScore,
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
  if (term.subject) return subjectLabel(dict, term.subject);
  const known = dict.calculator.termKinds as Record<string, string>;
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
  // certificate/entrance_exam — не привязаны к предмету, у каждой формулы
  // максимум по одному слагаемому такого рода (ЛУ/Вентспилс, сентябрь 2026)
  const hasCertificate = terms.some((t) => t.kind === "certificate");
  const hasEntranceExam = terms.some((t) => t.kind === "entrance_exam");

  const [inputs, setInputs] = useState<Record<string, SubjectInput>>(() =>
    Object.fromEntries(subjects.map((subject) => [subject, { percent: "", level: "augstakais" as ExamLevel }])),
  );
  const [certificate, setCertificate] = useState("");
  const [entranceExam, setEntranceExam] = useState("");

  const examResults: ExamResult[] = subjects.flatMap((subject) => {
    const value = inputs[subject];
    const percent = Number(value.percent);
    if (value.percent === "" || Number.isNaN(percent)) return [];
    return [{ subject, percent, level: value.level }];
  });

  const extras: { certificate?: number; entranceExam?: number } = {};
  if (certificate !== "" && !Number.isNaN(Number(certificate))) extras.certificate = Number(certificate);
  if (entranceExam !== "" && !Number.isNaN(Number(entranceExam))) extras.entranceExam = Number(entranceExam);

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

        {hasCertificate && (
          <div className="flex flex-wrap items-center gap-4">
            <span className="w-40 shrink-0 text-sm font-medium text-zinc-700">
              {dict.calculator.termKinds.certificate}
            </span>
            <Input
              type="number"
              min={0}
              max={10}
              size="sm"
              className="w-24"
              value={certificate}
              onValueChange={setCertificate}
            />
          </div>
        )}

        {hasEntranceExam && (
          <div className="flex flex-wrap items-center gap-4">
            <span className="w-40 shrink-0 text-sm font-medium text-zinc-700">
              {dict.calculator.termKinds.entrance_exam}
            </span>
            <Input
              type="number"
              min={0}
              max={10}
              size="sm"
              className="w-24"
              value={entranceExam}
              onValueChange={setEntranceExam}
            />
          </div>
        )}
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
