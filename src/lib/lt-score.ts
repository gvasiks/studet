// Литовский конкурсный балл — чистый расчёт, без обращения к базе и без
// интерфейса (тот же приём, что formula.ts у латвийского балла).
//
// Правило одно на всю страну, а не своё у каждого вуза: балл складывается
// из четырёх составляющих, у каждой вес и предмет или список предметов на
// выбор. Какие предметы и веса у программы — данные (таблица формул из
// открытого файла официального калькулятора LAMA BPO, разбор —
// pipeline/src/lt_formulas.py). Здесь — только как из оценок и формулы
// получается число.
//
// ЧТО УМЕЕТ ЭТА ВЕРСИЯ. Государственные экзамены (VBE) выпускников 2026 года
// и позже:
//   - оценка экзамена по стобалльной шкале переводится в шкалу до 10
//     делением на десять;
//   - у литовского языка и математики, сданных по общему курсу (B), значение
//     берётся с коэффициентом 0,7;
//   - в каждую составляющую идёт предмет, выгодный поступающему; один
//     предмет в двух составляющих не повторяется;
//   - нет подходящей оценки — составляющая равна нулю.
//
// ЧЕГО НЕТ: годовых оценок вместо экзамена, дополнительных баллов
// (олимпиады, служба), экзаменов 2025 года и раньше (у них свои поправки),
// оценки профессиональной квалификации. Всё это есть в правилах и появится
// после сверки с официальным калькулятором.
//
// ОТКУДА ПРАВИЛА. Приказ министра образования № V-1216 от 2025-11-26,
// приложение 5; принципы составления балла, утверждённые конференцией
// ректоров (LURK, 2025-11-28). Текст приложения 5 прочитан не напрямую, а в
// цитатах из материалов приёмной службы — подробности и список
// непроверенного в docs/checks/LT-PHASE3-SCORE-RULES.md. До сверки с
// официальным калькулятором расчёт посетителям не показывается.

/** Одна составляющая формулы, как её отдаёт разбор файла калькулятора. */
export type LtComponent = {
  position: number;
  weight: number;
  /** one_of — один предмет из списка; average — среднее всех перечисленных. */
  mode: "one_of" | "average";
  subjects: readonly string[];
};

export type LtFormula = readonly LtComponent[];

/** Результат по одному предмету. */
export type LtExam = {
  /** Оценка по стобалльной шкале. */
  score: number;
  /** Курс: только у литовского языка и математики. Без указания — расширенный (A). */
  course?: "A" | "B";
};

/** Ключ — предмет (как в формуле), значение — результат. */
export type LtExams = Readonly<Record<string, LtExam | undefined>>;

export type LtScoreItem = {
  position: number;
  weight: number;
  /** Какие предметы пошли в составляющую; пусто — подходящей оценки нет. */
  used: string[];
  /** Значение по шкале до 10; null — составляющая равна нулю. */
  value: number | null;
  contribution: number;
};

export type LtScore = {
  /** Основная часть балла, без дополнительных баллов; округлена до сотых. */
  total: number;
  items: LtScoreItem[];
};

// Предметы с двумя курсами: общий курс (B) считается с понижением.
const TWO_COURSE_SUBJECTS = new Set(["lithuanian", "mathematics"]);
const B_COURSE_FACTOR = 0.7;

// Оценка ниже этой в шкалу балла не переводится: формула пересчёта в
// приказе дана для 30–100. Что именно делает официальный расчёт с оценкой
// ниже 30, не проверено — здесь такая оценка не засчитывается.
export const MIN_COUNTED_SCORE = 30;

// Иностранных языков у выпускника может быть два. В формулах они названы
// «иностранный язык» и «второй иностранный язык»; подходит любой из
// введённых, но один и тот же язык дважды не считается.
const FOREIGN_LANGUAGES = ["foreign_language", "second_foreign_language"];

// В каком порядке предметы стоят в форме расчёта: сначала два обязательных
// экзамена, потом остальные.
const INPUT_ORDER = [
  "lithuanian", "mathematics", "history", "foreign_language", "second_foreign_language",
  "biology", "chemistry", "physics", "geography", "informatics", "economics", "philosophy",
  "engineering", "minority_language",
];

/**
 * Предметы, по которым у формулы есть смысл спрашивать оценку. Если формула
 * называет хотя бы один иностранный язык, в форме стоят оба поля: подойти
 * может любой из двух языков выпускника. Оценка профессиональной
 * квалификации (competence_assessment) не спрашивается — этот расчёт её не
 * учитывает.
 */
export function ltInputSubjects(formula: LtFormula): string[] {
  const named = new Set(formula.flatMap((component) => component.subjects));
  if (FOREIGN_LANGUAGES.some((language) => named.has(language))) {
    for (const language of FOREIGN_LANGUAGES) named.add(language);
  }
  return INPUT_ORDER.filter((subject) => named.has(subject));
}

/** Значение одного экзамена по шкале до 10; null — не засчитывается. */
export function examValue(subject: string, exam: LtExam | undefined): number | null {
  if (!exam || !Number.isFinite(exam.score)) return null;
  if (exam.score < MIN_COUNTED_SCORE || exam.score > 100) return null;
  const base = exam.score / 10;
  return TWO_COURSE_SUBJECTS.has(subject) && exam.course === "B" ? base * B_COURSE_FACTOR : base;
}

// Какие введённые предметы подходят под название из формулы.
function inputsFor(formulaSubject: string): string[] {
  return FOREIGN_LANGUAGES.includes(formulaSubject) ? FOREIGN_LANGUAGES : [formulaSubject];
}

type Choice = { used: string[]; value: number | null };

function choicesFor(component: LtComponent, exams: LtExams, taken: ReadonlySet<string>): Choice[] {
  if (component.mode === "average") {
    // Среднее считается, только когда есть все перечисленные предметы.
    const values = component.subjects.map((subject) => (taken.has(subject) ? null : examValue(subject, exams[subject])));
    if (values.some((value) => value === null)) return [{ used: [], value: null }];
    const sum = (values as number[]).reduce((total, value) => total + value, 0);
    return [{ used: [...component.subjects], value: sum / values.length }];
  }

  const choices: Choice[] = [{ used: [], value: null }];
  const seen = new Set<string>();
  for (const formulaSubject of component.subjects) {
    for (const input of inputsFor(formulaSubject)) {
      if (seen.has(input) || taken.has(input)) continue;
      seen.add(input);
      const value = examValue(input, exams[input]);
      if (value !== null) choices.push({ used: [input], value });
    }
  }
  return choices;
}

function round2(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

/**
 * Основная часть балла. Предметы по составляющим распределяются так, чтобы
 * сумма была наибольшей: в правилах сказано «берётся оценка, выгодная
 * поступающему», а один предмет в двух составляющих не повторяется.
 * Составляющих не больше четырёх, предметов — полтора десятка, поэтому
 * перебираются все варианты.
 */
export function ltScore(formula: LtFormula, exams: LtExams): LtScore {
  const components = [...formula].sort((a, b) => a.position - b.position);
  let best: { sum: number; choices: Choice[] } | null = null;

  function walk(index: number, taken: Set<string>, sum: number, choices: Choice[]): void {
    if (index === components.length) {
      // При равной сумме остаётся первый найденный вариант: перебор идёт в
      // порядке предметов формулы, так что разбор балла получается один и
      // тот же при каждом расчёте.
      if (best === null || sum > best.sum + 1e-9) best = { sum, choices: [...choices] };
      return;
    }
    const component = components[index];
    for (const choice of choicesFor(component, exams, taken)) {
      for (const subject of choice.used) taken.add(subject);
      choices.push(choice);
      walk(index + 1, taken, sum + (choice.value ?? 0) * component.weight, choices);
      choices.pop();
      for (const subject of choice.used) taken.delete(subject);
    }
  }

  walk(0, new Set(), 0, []);

  const chosen = (best as { sum: number; choices: Choice[] } | null)?.choices ?? [];
  const items = components.map((component, index) => {
    const choice = chosen[index] ?? { used: [], value: null };
    return {
      position: component.position,
      weight: component.weight,
      used: choice.used,
      value: choice.value === null ? null : round2(choice.value),
      contribution: round2((choice.value ?? 0) * component.weight),
    };
  });
  const total = chosen.reduce((sum, choice, index) => sum + (choice.value ?? 0) * components[index].weight, 0);
  return { total: round2(total), items };
}
