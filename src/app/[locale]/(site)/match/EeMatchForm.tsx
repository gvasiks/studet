"use client";

import Link from "next/link";
import { Input, Radio, RadioGroup } from "@heroui/react";
import { countryOf, languageOf, type Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { isEeExamInput, useSessionExams } from "@/lib/exam-session";
import { ClearExamsButton } from "@/components/ClearExamsButton";
import { parsePercent } from "@/lib/exam-input";
import { eeMatch, STATUS_ORDER, type EeEnglishInput, type EeExams, type EeMatchStatus } from "@/lib/ee-match";
import type { EeMatchProgramme } from "@/lib/ee-match-queries";
import type { EeThresholdSet } from "@/lib/ee-rule";
import { variantLines, variantTexts } from "@/lib/ee-variants";
import { plainDate } from "@/lib/ee-admission";
import { enumLabel } from "@/lib/names";
import { interpolate } from "@/lib/outcomes";
import { useTrackOnce } from "@/components/Analytics";
import { Providers } from "@/app/[locale]/providers";
import { HEROUI_FIELD_CLASSES } from "@/lib/field-text";

// Эстонское «куда можно поступить» (ee-match.ts): результаты госэкзаменов
// сравниваются с порогами правил приёма следующего учебного года — пока
// TalTech 2027/28. Формулировки — только из решения владельца 2026-10-25:
// «порог для подачи пройден / не пройден», «гарантирующий порог по правилу
// вуза пройден», ниже него — «остальные места по рейтингу». Ни процентов, ни
// позиции, ни «скорее всего».
//
// Результаты живут только в этой вкладке браузера (exam-session.ts): не в
// адресе и не на сервере (экзамены несовершеннолетних, CLAUDE.md).

const SUBJECTS = ["math", "estonian", "english"] as const;
type Subject = (typeof SUBJECTS)[number];
type Field = { score: string; kind: string };
const EMPTY: Field = { score: "", kind: "" };
const DEFAULT_KIND: Record<Subject, string> = { math: "wide", estonian: "native", english: "" };
const ENGLISH_LEVELS = ["none", "B1", "B2", "C1"] as const;

function EeMatchFormForm({
  dict,
  locale,
  programmes,
  academicYear,
  decidedOn,
  sourceUrl,
  sourceTitle,
}: {
  dict: Dictionary;
  locale: Locale;
  programmes: EeMatchProgramme[];
  academicYear: string | null;
  decidedOn: string | null;
  sourceUrl: string | null;
  sourceTitle: string | null;
}) {
  const text = dict.eeMatch;
  const language = languageOf(locale);
  const estonian = language === "et" ? undefined : "et";
  const [inputs, setInputs, clearInputs] = useSessionExams(countryOf(locale), SUBJECTS, EMPTY, isEeExamInput);
  const kindOf = (subject: Subject) => inputs[subject].kind || DEFAULT_KIND[subject];
  const set = (subject: Subject, patch: Partial<Field>) =>
    setInputs((prev) => ({ ...prev, [subject]: { ...prev[subject], kind: prev[subject].kind || DEFAULT_KIND[subject], ...patch } }));

  const math = parsePercent(inputs.math.score);
  const est = parsePercent(inputs.estonian.score);
  const invalid = { math: math.state === "invalid", estonian: est.state === "invalid" };
  const hasInvalid = invalid.math || invalid.estonian;
  const exams: EeExams = {
    ...(math.state === "ok" && { math: { score: math.value, kind: kindOf("math") === "narrow" ? "narrow" : "wide" } }),
    ...(est.state === "ok" && { estonian: { score: est.value, kind: kindOf("estonian") === "second" ? "second" : "native" } }),
    ...(inputs.english.kind !== "" && { english: inputs.english.kind as EeEnglishInput }),
  };
  const hasExams = exams.math !== undefined || exams.estonian !== undefined;
  const anyFilled = SUBJECTS.some((subject) => inputs[subject].score !== "" || inputs[subject].kind !== "");

  const collator = new Intl.Collator(language, { sensitivity: "base", numeric: true });
  const results = programmes
    .map((programme) => ({ programme, result: eeMatch(programme.rule, exams) }))
    .sort((a, b) => collator.compare(a.programme.name, b.programme.name));
  const groups = STATUS_ORDER.map((status) => ({ status, items: results.filter((item) => item.result.status === status) })).filter(
    (group) => group.items.length > 0,
  );
  useTrackOnce("match_result_shown", hasExams && !hasInvalid && results.some((item) => item.result.status !== "incomplete"));

  const line = (values: EeThresholdSet) =>
    interpolate(text.thresholdLine, {
      math: String(values.math),
      estonian: String(values.estonian),
      second: String(values.estonianSecond),
    }) + (values.english ? interpolate(text.englishLine, { level: values.english }) : "");
  const statusTitle = (status: EeMatchStatus) => text.status[status];
  const statusHint = (status: EeMatchStatus) => text.status[`${status}Hint`];

  const scoreField = (subject: "math" | "estonian", kinds: readonly [string, string], kindLabel: string) => {
    const errorId = `ee-match-error-${subject}`;
    const filled = inputs[subject].score !== "";
    return (
      <div
        key={subject}
        className={`rounded-2xl border p-3 transition-colors ${filled ? "border-brand/40 bg-brand-soft/40" : "border-zinc-200 bg-white"}`}
      >
        <span className="block text-sm font-medium leading-snug text-zinc-800">{text[subject]}</span>
        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-2">
          <Input
            type="text"
            inputMode="numeric"
            maxLength={5}
            size="sm"
            className="w-24"
            classNames={HEROUI_FIELD_CLASSES}
            aria-label={text[subject]}
            aria-describedby={invalid[subject] ? errorId : undefined}
            isInvalid={invalid[subject]}
            value={inputs[subject].score}
            onValueChange={(value) => set(subject, { score: value })}
          />
          <RadioGroup
            orientation="horizontal"
            size="sm"
            aria-label={`${text[subject]} — ${kindLabel}`}
            value={kindOf(subject)}
            onValueChange={(value) => set(subject, { kind: value })}
          >
            {kinds.map((kind) => (
              <Radio key={kind} value={kind}>
                {text[kind as "wide" | "narrow" | "native" | "second"]}
              </Radio>
            ))}
          </RadioGroup>
        </div>
        {invalid[subject] && (
          <p id={errorId} className="mt-2 text-sm text-red-700">
            {text.invalid}
          </p>
        )}
      </div>
    );
  };

  return (
    <div>
      {/* Ввод экзаменов — форма, поэтому HeroUI здесь уместен (правило 4). */}
      <section aria-labelledby="ee-match-exams" className="surface p-6 sm:p-8">
        <h2 id="ee-match-exams" className="text-lg font-semibold tracking-tight text-zinc-900">
          {dict.match.examsHeading}
        </h2>
        <p className="mt-1 max-w-[65ch] text-sm text-zinc-600">{text.hint}</p>

        <div className="mt-6 grid gap-3 lg:grid-cols-3">
          {scoreField("math", ["wide", "narrow"], text.mathKind)}
          {scoreField("estonian", ["native", "second"], text.estonianKind)}
          <div
            className={`rounded-2xl border p-3 transition-colors ${
              inputs.english.kind !== "" ? "border-brand/40 bg-brand-soft/40" : "border-zinc-200 bg-white"
            }`}
          >
            <RadioGroup
              size="sm"
              label={text.english}
              classNames={{ label: "text-sm font-medium leading-snug text-zinc-800" }}
              value={inputs.english.kind}
              onValueChange={(value) => set("english", { kind: value })}
            >
              {ENGLISH_LEVELS.map((level) => (
                <Radio key={level} value={level}>
                  {level === "none" ? text.englishNone : level}
                </Radio>
              ))}
            </RadioGroup>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-start justify-between gap-3">
          <p className="max-w-[65ch] text-xs leading-relaxed text-zinc-600">{dict.match.privacy}</p>
          {anyFilled && <ClearExamsButton label={dict.match.clearResults} onClear={clearInputs} />}
        </div>
      </section>

      <section aria-labelledby="ee-match-results" className="mt-8">
        <h2 id="ee-match-results" className="sr-only">
          {dict.match.title}
        </h2>
        {!hasExams || hasInvalid ? (
          <p className="surface p-6 text-zinc-700">{hasInvalid ? dict.calculator.fixInvalid : dict.match.emptyNoExams}</p>
        ) : (
          <>
            <p className="text-sm font-medium text-zinc-800" aria-live="polite">
              {interpolate(text.summary, { count: String(results.length) })}
            </p>
            {groups.map(({ status, items }) => (
              <div key={status} className="mt-6">
                <h3 className="text-lg font-semibold tracking-tight text-zinc-900">
                  {statusTitle(status)} <span className="font-normal text-zinc-600">· {items.length}</span>
                </h3>
                <p className="mt-1 max-w-[70ch] text-sm text-zinc-600">{statusHint(status)}</p>
                <ul className="mt-3 space-y-3">
                  {items.map(({ programme, result }) => {
                    const notes = variantLines(programme.variant ?? undefined, variantTexts(dict.catalog));
                    return (
                      <li key={programme.id} className="surface p-4 sm:p-5">
                        <Link
                          href={`/${locale}/programmes/${programme.universitySlug}/${programme.slug}`}
                          className="font-medium text-zinc-900 underline decoration-zinc-300 underline-offset-2 hover:decoration-zinc-900"
                        >
                          {programme.name}
                        </Link>
                        <span className="text-sm text-zinc-600">
                          {" — "}
                          {programme.universityName}
                          {programme.city ? `, ${enumLabel(dict.catalog.city, programme.city)}` : ""}
                        </span>
                        {notes.map((note) => (
                          <p key={note} className="mt-1 text-[13px] leading-snug text-zinc-600">
                            {note}
                          </p>
                        ))}
                        {programme.newCurriculum && <p className="mt-1 text-[13px] leading-snug text-zinc-600">{text.newCurriculum}</p>}
                        <dl className="mt-2 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
                          {programme.rule.apply && (
                            <div>
                              <dt className="inline text-zinc-600">{text.apply}: </dt>
                              <dd className="inline text-zinc-900">{line(programme.rule.apply)}</dd>
                            </div>
                          )}
                          <div>
                            <dt className="inline text-zinc-600">{text.guarantee}: </dt>
                            <dd className="inline text-zinc-900">{line(programme.rule.guarantee)}</dd>
                          </div>
                        </dl>
                        {programme.rule.places !== null && (
                          <p className="mt-1 text-sm text-zinc-600">{interpolate(text.places, { places: String(programme.rule.places) })}</p>
                        )}
                        {result.missing.length > 0 && (
                          <p className="mt-2 text-sm text-amber-900">
                            {interpolate(text.missing, { list: result.missing.map((item) => text.missingNames[item]).join(", ") })}
                          </p>
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
        <p>{text.coverage}</p>
        {academicYear && sourceTitle && decidedOn && (
          <p className="text-xs">
            {interpolate(text.rulesNote, {
              year: academicYear,
              title: "\u0000",
              date: plainDate(decidedOn, language),
            })
              .split("\u0000")
              .map((part, index) =>
                index === 0 ? (
                  <span key={index}>{part}</span>
                ) : (
                  <span key={index}>
                    <span lang={estonian}>{sourceTitle}</span>
                    {part}
                  </span>
                ),
              )}{" "}
            {sourceUrl && (
              <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="underline">
                {text.sourceLink}
              </a>
            )}
          </p>
        )}
        <p className="text-xs">{text.decidedBy}</p>
      </div>
    </div>
  );
}

// Провайдер HeroUI — только вокруг интерактивной формы (правило 4 CLAUDE.md).
export function EeMatchForm(props: React.ComponentProps<typeof EeMatchFormForm>) {
  return (
    <Providers>
      <EeMatchFormForm {...props} />
    </Providers>
  );
}
