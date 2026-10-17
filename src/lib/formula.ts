// Один общий вычислитель для всех вузов — правило 2 CLAUDE.md.
// Всё, чем вузы отличаются друг от друга, живёт в данных (formula_term,
// formula_gate, level_coefficient), не здесь.

export type ExamLevel = "augstakais" | "optimalais" | "vispaarigais";

export type ExamResult = {
  subject: string;
  percent: number;
  level: ExamLevel;
};

// Вариант слагаемого ce_average: subject = "leveled" — среднее по CE
// "с учётом коэффициента уровня каждого экзамена" (Daugavpils, LBTU:
// "visu CE kopvērtējumu vidējā vērtība (ņemot vērā katra CE līmeņa
// koeficientu)"). Без него (subject = null) — среднее сырых процентов,
// как у ЛУ и Ventspils.
export const AVERAGE_WITH_LEVEL = "leveled";

export type FormulaTerm = {
  kind: "ce" | "ce_average" | "certificate" | "entrance_exam";
  subject: string | null;
  coefficient: number;
  // "Ja nav CE …, tad 0" / "ja iestājpārbaudījums netiek kārtots, tad 0":
  // слагаемое можно не иметь, оно тогда равно нулю, а программа остаётся
  // доступной. calculateScore считает так же (нет данных — 0); флаг нужен
  // тем, кто решает, чего "не хватает" (обратный поиск).
  optional?: boolean;
};

// Ключ для extras — один формула может нести несколько отдельных
// certificate/entrance_exam слагаемых (RTU Rīgas Biznesa skola: тест
// английского + собеседование + тест математики, три разных числа,
// не одно). subject здесь — не CE-предмет, а метка конкретного
// испытания ("interview", "math_test" и т.п.); null — старый случай
// одного безымянного испытания на формулу (Вентспилс).
export function extraKey(term: Pick<FormulaTerm, "kind" | "subject">): string {
  return `${term.kind}:${term.subject ?? "default"}`;
}

export type FormulaGate = {
  subject: string;
  minPercent: number;
};

export type ScoreLine = {
  term: FormulaTerm;
  // null: не хватило данных для этого слагаемого (не сдавал предмет,
  // не указан балл аттестата и т.п.) — считается как 0, но видно почему.
  input: number | null;
  points: number;
  // Из чего получился input — для записи разбора «72 % × 0,75 × 1,5»
  // (lineFormula): процент экзамена (у среднего — средний процент) и
  // коэффициент его уровня. null, где их нет (аттестат, испытание вуза,
  // нет данных).
  percent: number | null;
  levelCoefficient: number | null;
};

export type ScoreResult = {
  total: number;
  lines: ScoreLine[];
  failedGates: FormulaGate[];
};

export function calculateScore(
  terms: FormulaTerm[],
  gates: FormulaGate[],
  examResults: ExamResult[],
  levelCoefficients: Record<ExamLevel, number>,
  extras: Record<string, number> = {},
): ScoreResult {
  const bySubject = new Map(examResults.map((result) => [result.subject, result]));

  const lines: ScoreLine[] = terms.map((term) => {
    if (term.kind === "ce") {
      const result = term.subject ? bySubject.get(term.subject) : undefined;
      if (!result) return { term, input: null, points: 0, percent: null, levelCoefficient: null };
      const levelCoefficient = levelCoefficients[result.level];
      const input = result.percent * levelCoefficient;
      return { term, input, points: input * term.coefficient, percent: result.percent, levelCoefficient };
    }

    if (term.kind === "ce_average") {
      if (examResults.length === 0) return { term, input: null, points: 0, percent: null, levelCoefficient: null };
      const withLevel = term.subject === AVERAGE_WITH_LEVEL;
      const average =
        examResults.reduce((sum, r) => sum + r.percent * (withLevel ? levelCoefficients[r.level] : 1), 0) /
        examResults.length;
      return { term, input: average, points: average * term.coefficient, percent: average, levelCoefficient: null };
    }

    const raw = extras[extraKey(term)];
    if (raw === undefined) return { term, input: null, points: 0, percent: null, levelCoefficient: null };
    return { term, input: raw, points: raw * term.coefficient, percent: null, levelCoefficient: null };
  });

  const failedGates = gates.filter((gate) => {
    const result = bySubject.get(gate.subject);
    return !result || result.percent < gate.minPercent;
  });

  return {
    total: lines.reduce((sum, line) => sum + line.points, 0),
    lines,
    failedGates,
  };
}

/**
 * Как получились баллы слагаемого — для разбора под калькулятором и в
 * /match (аудит 2026-10-04: был виден только итог «81.00» без того, из чего
 * он сложился). CE: «72 % × 0,75 × 1,5» (процент × уровень × вес);
 * среднее: «68,5 % × 0,2»; аттестат и испытание вуза: «8,2 × 10».
 * null — данных для слагаемого нет. Числа — с десятичным знаком языка.
 */
export function lineFormula(line: ScoreLine, language: string): string | null {
  if (line.input === null) return null;
  const number = (value: number) => value.toLocaleString(language, { maximumFractionDigits: 2 });
  const percent = (value: number) => (language === "en" ? `${number(value)}%` : `${number(value)} %`);
  const parts =
    line.percent === null
      ? [number(line.input)]
      : line.levelCoefficient === null
        ? [percent(line.percent)]
        : [percent(line.percent), number(line.levelCoefficient)];
  return [...parts, number(line.term.coefficient)].join(" × ");
}
