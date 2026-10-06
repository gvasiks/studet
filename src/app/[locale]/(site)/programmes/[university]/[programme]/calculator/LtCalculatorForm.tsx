"use client";

import { useMemo, useState } from "react";
import { Input, Radio, RadioGroup } from "@heroui/react";
import { languageOf, type Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { LtScoreBreakdown } from "@/components/LtScoreBreakdown";
import { parsePercent } from "@/lib/exam-input";
import { ltInputSubjects, ltScore, MIN_COUNTED_SCORE, type LtComponent, type LtExams } from "@/lib/lt-score";
import { interpolate } from "@/lib/outcomes";

// Страница официального калькулятора LAMA BPO — туда ведём за
// дополнительными баллами и за окончательным расчётом.
const OFFICIAL_CALCULATOR = "https://lamabpo.lt/pirmosios-pakopos-ir-vientisosios-studijos/konkursinio-balo-skaiciuokle/";

// Предметы с двумя курсами: общий курс (B) считается с понижением.
const TWO_COURSE_SUBJECTS = new Set(["lithuanian", "mathematics"]);

type SubjectInput = { score: string; course: "A" | "B" };

// Литовский расчёт балла. Формула общая на страну и приходит из базы уже
// сверенной (см. src/lib/lt-score-queries.ts); сам расчёт — src/lib/lt-score.ts.
// Оценки считаются в браузере и никуда не отправляются — как в латвийском
// калькуляторе.
export function LtCalculatorForm({
  dict,
  locale,
  components,
  admissionYear,
  sourceUrl,
  checkedAt,
}: {
  dict: Dictionary;
  locale: Locale;
  components: LtComponent[];
  admissionYear: number;
  sourceUrl: string;
  checkedAt: string;
}) {
  const text = dict.ltCalculator;
  const language = languageOf(locale);
  const subjects = useMemo(() => ltInputSubjects(components), [components]);
  const [inputs, setInputs] = useState<Record<string, SubjectInput>>(() =>
    Object.fromEntries(subjects.map((subject) => [subject, { score: "", course: "A" as const }])),
  );

  const label = (subject: string) => text.subjects[subject as keyof typeof text.subjects] ?? subject;

  const parsed = subjects.map((subject) => {
    const number = parsePercent(inputs[subject].score);
    // Оценку ниже 30 официальный калькулятор для экзаменов этого года не
    // принимает — здесь это такая же ошибка ввода, а не «ноль баллов».
    const invalid = number.state === "invalid" || (number.state === "ok" && number.value < MIN_COUNTED_SCORE);
    return { subject, number, invalid };
  });
  const hasInvalid = parsed.some((item) => item.invalid);
  const exams: LtExams = Object.fromEntries(
    parsed
      .filter((item) => item.number.state === "ok" && !item.invalid)
      .map((item) => [
        item.subject,
        { score: (item.number as { value: number }).value, course: inputs[item.subject].course },
      ]),
  );
  const hasAny = Object.keys(exams).length > 0;
  const result = hasAny && !hasInvalid ? ltScore(components, exams) : null;

  const number = (value: number) => value.toLocaleString(language, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div className="mt-6">
      <p className="text-sm leading-relaxed text-zinc-600">{text.intro}</p>

      <div className="mt-6 space-y-5">
        {parsed.map(({ subject, invalid }) => {
          const errorId = `lt-calculator-error-${subject}`;
          return (
            <div key={subject} className="flex flex-wrap items-center gap-x-4 gap-y-2">
              <span className="w-48 shrink-0 text-sm font-medium text-zinc-700">{label(subject)}</span>
              {/* Текстовое поле, а не type="number" — по той же причине, что в
                  латвийском калькуляторе: запятая не теряется, разбор наш. */}
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
                  aria-label={`${label(subject)} — ${text.courseLabel}`}
                  value={inputs[subject].course}
                  onValueChange={(value) =>
                    setInputs((prev) => ({ ...prev, [subject]: { ...prev[subject], course: value as "A" | "B" } }))
                  }
                >
                  <Radio value="A">{text.courseA}</Radio>
                  <Radio value="B">{text.courseB}</Radio>
                </RadioGroup>
              )}
              {invalid && (
                <p id={errorId} className="basis-full text-sm text-red-700">
                  {text.invalid}
                </p>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-8 rounded-xl bg-zinc-50 p-6">
        <p className="text-sm text-zinc-500">{text.totalLabel}</p>
        {result ? (
          <>
            <p className="text-4xl font-bold tracking-tighter text-zinc-900">{number(result.total)}</p>

            <h2 className="mt-5 text-xs uppercase tracking-wide text-zinc-500">{text.breakdownTitle}</h2>
            <div className="mt-2">
              <LtScoreBreakdown dict={dict} language={language} components={components} items={result.items} />
            </div>
          </>
        ) : (
          <>
            <p className="text-4xl font-bold tracking-tighter text-zinc-500" aria-hidden="true">
              —
            </p>
            <p className="mt-2 text-sm text-zinc-700">{hasInvalid ? dict.calculator.fixInvalid : text.empty}</p>
          </>
        )}
      </div>

      <p className="mt-6 rounded-xl bg-amber-50 px-4 py-3 text-sm leading-relaxed text-amber-900">
        {text.extrasNote}{" "}
        <a href={OFFICIAL_CALCULATOR} target="_blank" rel="noopener noreferrer" className="underline">
          {text.officialLink}
        </a>
      </p>
      <p className="mt-4 text-xs leading-relaxed text-zinc-500">
        {interpolate(text.rulesNote, { year: String(admissionYear) })}{" "}
        {interpolate(text.checkedNote, { date: new Date(checkedAt).toLocaleDateString(language) })}{" "}
        <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="underline">
          {text.sourceLink}
        </a>
      </p>
      <p className="mt-2 text-xs leading-relaxed text-zinc-500">{text.decidedBy}</p>
    </div>
  );
}
