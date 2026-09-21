"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { Button, Checkbox, CheckboxGroup, Radio, RadioGroup } from "@heroui/react";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { CITY_KEYS, enumLabel } from "@/lib/catalog";
import { ArrowRightIcon, CheckIcon, SearchIcon } from "@/components/icons";

type Funding = "budget_only" | "any";
type LanguageChoice = "lv" | "en" | "any";
type ModeChoice = "full_time" | "part_time" | "distance" | "any";

type Answers = {
  exams: string[];
  interests: string[];
  funding: Funding;
  cities: string[];
  anywhere: boolean;
  language: LanguageChoice;
  mode: ModeChoice;
};

const initialAnswers: Answers = {
  exams: [],
  interests: [],
  funding: "any",
  cities: [],
  anywhere: false,
  language: "any",
  mode: "any",
};

const STEP_COUNT = 6;

const FOCUS = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

// Варианты — плитками, а не вертикальным списком чекбоксов: на первом шаге
// десять предметов, на шаге города — шесть, и столбиком они читаются как
// бланк, а не как выбор. Слоты base/label — штатный способ HeroUI задать
// свой вид, при котором сохраняются нативный input и доступность;
// data-selected HeroUI ставит сам.
const TILE = {
  base:
    "m-0 w-full max-w-none cursor-pointer items-center gap-3 rounded-2xl border border-zinc-200 bg-white p-4 shadow-control transition-colors hover:border-zinc-300 " +
    "data-[selected=true]:border-brand data-[selected=true]:bg-brand-soft",
  label: "text-sm font-medium leading-snug text-zinc-800",
};

// Сетка плиток внутри группы. Один столбец на телефоне, два-три дальше —
// десять предметов в один столбец дают экран прокрутки на пустом месте.
const TILE_GRID = { wrapper: "grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-3" };

// Радио — те же плитки, но вариантов два-четыре: в один столбец на телефоне,
// в ряд дальше. Слот control — сама точка, её оставляем как есть.
const RADIO_GRID = { wrapper: "grid grid-cols-1 gap-2.5 sm:grid-cols-2" };

function StepShell({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <fieldset className="min-w-0">
      <legend className="text-xl font-semibold tracking-tight text-zinc-900">{title}</legend>
      {hint && <p className="mt-2 max-w-[60ch] text-sm leading-relaxed text-zinc-500">{hint}</p>}
      <div className="mt-5">{children}</div>
    </fieldset>
  );
}

export function SurveyWizard({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Answers>(initialAnswers);

  function skipToSearch() {
    router.push(`/${locale}/programmes`);
  }

  function submit() {
    // Экзамены (шаг 1) сознательно не попадают в URL — пока ни на что не
    // влияют, см. подсказку под вопросом. Интересы (шаг 2) — влияют:
    // каталог фильтрует по направлению программы (пункт 16 ревью).
    const params = new URLSearchParams();
    if (answers.interests.length > 0) params.set("interest", answers.interests.join(","));
    if (answers.funding === "budget_only") params.set("budget", "1");
    if (!answers.anywhere && answers.cities.length > 0) {
      params.set("city", answers.cities.join(","));
    }
    if (answers.language !== "any") params.set("language", answers.language);
    if (answers.mode !== "any") params.set("mode", answers.mode);

    const query = params.toString();
    router.push(`/${locale}/programmes${query ? `?${query}` : ""}`);
  }

  const isLast = step === STEP_COUNT - 1;
  const progress = ((step + 1) / STEP_COUNT) * 100;
  // Сколько выбрано на шагах с множественным выбором: человеку нужно видеть,
  // что «ничего не выбрано» — это допустимый ответ, а не незаполненный шаг.
  const selectedOnStep =
    step === 0 ? answers.exams.length : step === 1 ? answers.interests.length : step === 3 ? answers.cities.length : null;

  return (
    <main className="page-container py-8 sm:py-12">
      <div className="mx-auto max-w-3xl">
        {/* Заголовок на сером фоне, карточка — только под вопросом: так же,
            как на /rights. Вступление отделено от содержания. */}
        <header className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3">
          <div className="min-w-0">
            <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">{dict.survey.title}</h1>
            <p className="mt-3 max-w-[58ch] text-lg leading-relaxed text-zinc-600">{dict.survey.intro}</p>
          </div>
          {/* Вторая дверь: «я уже знаю, что ищу». Раньше была подчёркнутой
              серой строчкой в углу — то есть почти невидимой. Это не сноска,
              а равноправный вход в каталог (раздел 01 плана). */}
          <button
            type="button"
            onClick={skipToSearch}
            className={`inline-flex h-10 shrink-0 items-center gap-2 rounded-full border border-zinc-200 bg-white px-4 text-sm font-medium text-zinc-700 shadow-control transition-colors hover:border-zinc-300 hover:text-zinc-900 ${FOCUS}`}
          >
            <SearchIcon size={15} className="text-zinc-400" />
            {dict.survey.skipToSearch}
          </button>
        </header>

        {/* Прогресс: полоса плюс номера шагов. Раньше был только текст
            «шаг 1 из 6» — по нему не видно ни сколько осталось, ни того,
            что можно вернуться. Номера кликабельны: обязательных ответов
            в анкете нет, значит запирать порядок незачем. */}
        <nav aria-label={dict.survey.stepLabel} className="mt-8">
          <div
            aria-hidden="true"
            className="h-1.5 overflow-hidden rounded-full bg-zinc-200"
          >
            <div
              className="h-full rounded-full bg-brand transition-[width] duration-300 ease-out motion-reduce:transition-none"
              style={{ width: `${progress}%` }}
            />
          </div>
          <ol className="mt-3 flex items-center gap-1.5">
            {Array.from({ length: STEP_COUNT }, (_, index) => {
              const isCurrent = index === step;
              const isDone = index < step;
              return (
                <li key={index}>
                  <button
                    type="button"
                    onClick={() => setStep(index)}
                    aria-current={isCurrent ? "step" : undefined}
                    aria-label={`${dict.survey.stepLabel} ${index + 1} ${dict.survey.of} ${STEP_COUNT}`}
                    className={`grid h-8 w-8 place-items-center rounded-full text-xs font-semibold tabular-nums transition-colors ${FOCUS} ${
                      isCurrent
                        ? "bg-brand text-white"
                        : isDone
                          ? "bg-brand-soft text-brand hover:bg-brand/15"
                          : "bg-white text-zinc-400 shadow-control hover:text-zinc-600"
                    }`}
                  >
                    {isDone ? <CheckIcon size={14} /> : index + 1}
                  </button>
                </li>
              );
            })}
          </ol>
        </nav>

        <div className="surface mt-6 p-6 sm:p-10">
          {step === 0 && (
            <StepShell title={dict.survey.exams.title} hint={dict.survey.exams.hint}>
              <CheckboxGroup
                classNames={TILE_GRID}
                value={answers.exams}
                onValueChange={(value) => setAnswers((a) => ({ ...a, exams: value }))}
              >
                {Object.entries(dict.survey.exams.subjects).map(([key, label]) => (
                  <Checkbox key={key} value={key} classNames={TILE}>
                    {label}
                  </Checkbox>
                ))}
              </CheckboxGroup>
            </StepShell>
          )}

          {step === 1 && (
            <StepShell title={dict.survey.interests.title} hint={dict.survey.interests.hint}>
              <CheckboxGroup
                classNames={TILE_GRID}
                value={answers.interests}
                onValueChange={(value) => setAnswers((a) => ({ ...a, interests: value }))}
              >
                {Object.entries(dict.survey.interests.categories).map(([key, label]) => (
                  <Checkbox key={key} value={key} classNames={TILE}>
                    {label}
                  </Checkbox>
                ))}
              </CheckboxGroup>
            </StepShell>
          )}

          {step === 2 && (
            <StepShell title={dict.survey.funding.title}>
              <RadioGroup
                classNames={RADIO_GRID}
                value={answers.funding}
                onValueChange={(value) => setAnswers((a) => ({ ...a, funding: value as Funding }))}
              >
                <Radio value="budget_only" classNames={TILE}>
                  {dict.survey.funding.budgetOnly}
                </Radio>
                <Radio value="any" classNames={TILE}>
                  {dict.survey.funding.any}
                </Radio>
              </RadioGroup>
            </StepShell>
          )}

          {step === 3 && (
            <StepShell title={dict.survey.city.title}>
              <CheckboxGroup
                classNames={TILE_GRID}
                value={answers.cities}
                isDisabled={answers.anywhere}
                onValueChange={(value) => setAnswers((a) => ({ ...a, cities: value }))}
              >
                {CITY_KEYS.map((key) => (
                  <Checkbox key={key} value={key} classNames={TILE}>
                    {enumLabel(dict.catalog.city, key)}
                  </Checkbox>
                ))}
              </CheckboxGroup>
              {/* «Всё равно где» выключает города, поэтому стоит отдельно
                  и после них, за разделителем — иначе читается как седьмой
                  город в том же ряду. */}
              <div className="mt-5 border-t border-zinc-100 pt-5">
                <Checkbox
                  classNames={TILE}
                  isSelected={answers.anywhere}
                  onValueChange={(value) => setAnswers((a) => ({ ...a, anywhere: value }))}
                >
                  {dict.survey.city.anywhere}
                </Checkbox>
              </div>
            </StepShell>
          )}

          {step === 4 && (
            <StepShell title={dict.survey.language.title}>
              <RadioGroup
                classNames={RADIO_GRID}
                value={answers.language}
                onValueChange={(value) => setAnswers((a) => ({ ...a, language: value as LanguageChoice }))}
              >
                <Radio value="lv" classNames={TILE}>
                  {dict.catalog.language.lv}
                </Radio>
                <Radio value="en" classNames={TILE}>
                  {dict.catalog.language.en}
                </Radio>
                <Radio value="any" classNames={TILE}>
                  {dict.survey.language.any}
                </Radio>
              </RadioGroup>
            </StepShell>
          )}

          {step === 5 && (
            <StepShell title={dict.survey.mode.title}>
              <RadioGroup
                classNames={RADIO_GRID}
                value={answers.mode}
                onValueChange={(value) => setAnswers((a) => ({ ...a, mode: value as ModeChoice }))}
              >
                <Radio value="full_time" classNames={TILE}>
                  {dict.catalog.studyMode.full_time}
                </Radio>
                <Radio value="part_time" classNames={TILE}>
                  {dict.catalog.studyMode.part_time}
                </Radio>
                <Radio value="distance" classNames={TILE}>
                  {dict.catalog.studyMode.distance}
                </Radio>
                <Radio value="any" classNames={TILE}>
                  {dict.survey.mode.any}
                </Radio>
              </RadioGroup>
            </StepShell>
          )}

          {/* Кнопки — внутри карточки за разделителем, а не в воздухе под ней:
              они относятся к вопросу, а не к странице. Счётчик выбранного
              слева показывает, что пустой ответ тоже ответ. */}
          <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-zinc-100 pt-6">
            <p className="text-sm tabular-nums text-zinc-500">
              {selectedOnStep !== null && selectedOnStep > 0 ? `${selectedOnStep} ✓` : ""}
            </p>
            <div className="flex items-center gap-2">
              <Button variant="flat" isDisabled={step === 0} onPress={() => setStep((s) => s - 1)}>
                {dict.survey.back}
              </Button>
              <Button
                color="primary"
                onPress={isLast ? submit : () => setStep((s) => s + 1)}
                endContent={<ArrowRightIcon size={15} />}
              >
                {isLast ? dict.survey.submit : dict.survey.next}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
