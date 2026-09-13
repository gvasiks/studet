"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Checkbox, CheckboxGroup, Radio, RadioGroup } from "@heroui/react";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { enumLabel } from "@/lib/catalog";

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

const CITY_KEYS = ["riga", "daugavpils", "valmiera", "ventspils", "jelgava", "liepaja", "rezekne"];
const STEP_COUNT = 6;

export function SurveyWizard({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Answers>(initialAnswers);

  function skipToSearch() {
    router.push(`/${locale}/programmes`);
  }

  function submit() {
    // Экзамены и интересы (шаги 1-2) сознательно не попадают в URL — они
    // пока ни на что не влияют, см. подсказки под этими вопросами.
    const params = new URLSearchParams();
    if (answers.funding === "budget_only") params.set("budget", "1");
    if (!answers.anywhere && answers.cities.length > 0) {
      params.set("city", answers.cities.join(","));
    }
    if (answers.language !== "any") params.set("language", answers.language);
    if (answers.mode !== "any") params.set("mode", answers.mode);

    const query = params.toString();
    router.push(`/${locale}/programmes${query ? `?${query}` : ""}`);
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <div className="flex items-start justify-between gap-4">
        <h1 className="text-2xl font-bold tracking-tighter text-zinc-900">{dict.survey.title}</h1>
        <button type="button" onClick={skipToSearch} className="shrink-0 text-sm text-zinc-500 underline">
          {dict.survey.skipToSearch}
        </button>
      </div>
      <p className="mt-2 text-zinc-600">{dict.survey.intro}</p>
      <p className="mt-6 text-sm font-medium text-zinc-500">
        {dict.survey.stepLabel} {step + 1} {dict.survey.of} {STEP_COUNT}
      </p>

      <div className="mt-6">
        {step === 0 && (
          <fieldset>
            <legend className="text-lg font-medium text-zinc-900">{dict.survey.exams.title}</legend>
            <p className="mt-1 text-sm text-zinc-500">{dict.survey.exams.hint}</p>
            <CheckboxGroup
              className="mt-4"
              value={answers.exams}
              onValueChange={(value) => setAnswers((a) => ({ ...a, exams: value }))}
            >
              {Object.entries(dict.survey.exams.subjects).map(([key, label]) => (
                <Checkbox key={key} value={key}>
                  {label}
                </Checkbox>
              ))}
            </CheckboxGroup>
          </fieldset>
        )}

        {step === 1 && (
          <fieldset>
            <legend className="text-lg font-medium text-zinc-900">{dict.survey.interests.title}</legend>
            <p className="mt-1 text-sm text-zinc-500">{dict.survey.interests.hint}</p>
            <CheckboxGroup
              className="mt-4"
              value={answers.interests}
              onValueChange={(value) => setAnswers((a) => ({ ...a, interests: value }))}
            >
              {Object.entries(dict.survey.interests.categories).map(([key, label]) => (
                <Checkbox key={key} value={key}>
                  {label}
                </Checkbox>
              ))}
            </CheckboxGroup>
          </fieldset>
        )}

        {step === 2 && (
          <fieldset>
            <legend className="text-lg font-medium text-zinc-900">{dict.survey.funding.title}</legend>
            <RadioGroup
              className="mt-4"
              value={answers.funding}
              onValueChange={(value) => setAnswers((a) => ({ ...a, funding: value as Funding }))}
            >
              <Radio value="budget_only">{dict.survey.funding.budgetOnly}</Radio>
              <Radio value="any">{dict.survey.funding.any}</Radio>
            </RadioGroup>
          </fieldset>
        )}

        {step === 3 && (
          <fieldset>
            <legend className="text-lg font-medium text-zinc-900">{dict.survey.city.title}</legend>
            <CheckboxGroup
              className="mt-4"
              value={answers.cities}
              isDisabled={answers.anywhere}
              onValueChange={(value) => setAnswers((a) => ({ ...a, cities: value }))}
            >
              {CITY_KEYS.map((key) => (
                <Checkbox key={key} value={key}>
                  {enumLabel(dict.catalog.city, key)}
                </Checkbox>
              ))}
            </CheckboxGroup>
            <Checkbox
              className="mt-4"
              isSelected={answers.anywhere}
              onValueChange={(value) => setAnswers((a) => ({ ...a, anywhere: value }))}
            >
              {dict.survey.city.anywhere}
            </Checkbox>
          </fieldset>
        )}

        {step === 4 && (
          <fieldset>
            <legend className="text-lg font-medium text-zinc-900">{dict.survey.language.title}</legend>
            <RadioGroup
              className="mt-4"
              value={answers.language}
              onValueChange={(value) => setAnswers((a) => ({ ...a, language: value as LanguageChoice }))}
            >
              <Radio value="lv">{dict.catalog.language.lv}</Radio>
              <Radio value="en">{dict.catalog.language.en}</Radio>
              <Radio value="any">{dict.survey.language.any}</Radio>
            </RadioGroup>
          </fieldset>
        )}

        {step === 5 && (
          <fieldset>
            <legend className="text-lg font-medium text-zinc-900">{dict.survey.mode.title}</legend>
            <RadioGroup
              className="mt-4"
              value={answers.mode}
              onValueChange={(value) => setAnswers((a) => ({ ...a, mode: value as ModeChoice }))}
            >
              <Radio value="full_time">{dict.catalog.studyMode.full_time}</Radio>
              <Radio value="part_time">{dict.catalog.studyMode.part_time}</Radio>
              <Radio value="distance">{dict.catalog.studyMode.distance}</Radio>
              <Radio value="any">{dict.survey.mode.any}</Radio>
            </RadioGroup>
          </fieldset>
        )}
      </div>

      <div className="mt-10 flex justify-between">
        <Button variant="flat" isDisabled={step === 0} onPress={() => setStep((s) => s - 1)}>
          {dict.survey.back}
        </Button>
        {step < STEP_COUNT - 1 ? (
          <Button color="primary" onPress={() => setStep((s) => s + 1)}>
            {dict.survey.next}
          </Button>
        ) : (
          <Button color="primary" onPress={submit}>
            {dict.survey.submit}
          </Button>
        )}
      </div>
    </main>
  );
}
