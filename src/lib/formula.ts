// Один общий вычислитель для всех вузов — правило 2 CLAUDE.md.
// Всё, чем вузы отличаются друг от друга, живёт в данных (formula_term,
// formula_gate, level_coefficient), не здесь.

export type ExamLevel = "augstakais" | "optimalais" | "vispaarigais";

export type ExamResult = {
  subject: string;
  percent: number;
  level: ExamLevel;
};

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
      if (!result) return { term, input: null, points: 0 };
      const input = result.percent * levelCoefficients[result.level];
      return { term, input, points: input * term.coefficient };
    }

    if (term.kind === "ce_average") {
      if (examResults.length === 0) return { term, input: null, points: 0 };
      const average = examResults.reduce((sum, r) => sum + r.percent, 0) / examResults.length;
      return { term, input: average, points: average * term.coefficient };
    }

    const raw = extras[extraKey(term)];
    if (raw === undefined) return { term, input: null, points: 0 };
    return { term, input: raw, points: raw * term.coefficient };
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
