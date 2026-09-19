// Данные о выпускниках (ревью 2026-09, пункт 14) — чистая логика выбора
// строк, без обращения к базе (тот же приём, что formula.ts /
// formula-queries.ts: так её можно тестировать без клиента Supabase).

// Studiju_limenis из датасета ИЗМ -> наш degree_level. Расшифровка
// собрана сверкой с известными программами ЛУ, не по официальной легенде
// — подробности в pipeline/src/graduate_outcomes.py. Держать в
// синхроне с тем файлом.
export const LEVEL_CODES_BY_DEGREE: Record<string, string[]> = {
  college: ["41"],
  bachelor: ["42", "43", "48", "49"],
  master: ["45", "47"],
  doctoral: ["51"],
};

export const OUTCOMES_SOURCE_URL =
  "https://data.gov.lv/dati/lv/dataset/2017_2023-g-latvijas-augstakas-izglitibas-iestazu-absolventi-2020-2024-monitoringa-gados";

export type OutcomeRow = {
  graduationYear: number;
  taxYear: number;
  levelCode: string;
  graduates: number;
  employed: number;
  medianIncomeEur: number | null;
};

export type OutcomeSnapshot = {
  graduationYear: number;
  taxYear: number;
  yearsAfter: number;
  graduates: number;
  employed: number;
  medianIncomeEur: number | null;
};

// Сколько лет после выпуска берём для сравнения с самым свежим выпуском.
// Ревью просило динамику "через 1–3 года и через 10 лет"; десяти лет в
// датасете нет (данные с выпуска 2017), пять — самое дальнее, что есть
// для нескольких выпусков подряд.
const COMPARISON_YEARS_AFTER = 5;

// Для программы берутся только строки того же уровня обучения. Если на
// одном уровне у вуза в этом направлении несколько кодов уровня (у ЛУ
// бакалавриат разбит на 42 и 43 — профессиональный и академический),
// по каждому году выпуска берётся самая большая ячейка: складывать
// медианы нельзя, а больший набор всё же ближе к "типичной" программе
// направления. Поэтому в тексте блока сказано "выпускники направления",
// не "выпускники программы".
export function pickOutcomes(rows: OutcomeRow[], degreeLevel: string): OutcomeSnapshot[] {
  const levels = LEVEL_CODES_BY_DEGREE[degreeLevel];
  if (!levels) return [];

  const largestByYear = new Map<number, OutcomeRow>();
  for (const row of rows) {
    if (!levels.includes(row.levelCode)) continue;
    const current = largestByYear.get(row.graduationYear);
    if (!current || row.graduates > current.graduates) largestByYear.set(row.graduationYear, row);
  }
  if (largestByYear.size === 0) return [];

  const toSnapshot = (row: OutcomeRow): OutcomeSnapshot => ({
    graduationYear: row.graduationYear,
    taxYear: row.taxYear,
    yearsAfter: row.taxYear - row.graduationYear,
    graduates: row.graduates,
    employed: row.employed,
    medianIncomeEur: row.medianIncomeEur,
  });

  const latest = largestByYear.get(Math.max(...largestByYear.keys()))!;
  const snapshots = [toSnapshot(latest)];

  for (const row of largestByYear.values()) {
    if (row !== latest && row.taxYear - row.graduationYear === COMPARISON_YEARS_AFTER) {
      snapshots.push(toSnapshot(row));
    }
  }
  return snapshots.sort((a, b) => a.yearsAfter - b.yearsAfter);
}

export function employmentPercent(snapshot: Pick<OutcomeSnapshot, "graduates" | "employed">): number {
  return snapshot.graduates > 0 ? Math.round((snapshot.employed / snapshot.graduates) * 100) : 0;
}

export function interpolate(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) => (key in values ? String(values[key]) : match));
}
