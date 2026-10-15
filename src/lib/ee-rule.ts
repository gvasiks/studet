// Правило конкурса эстонской программы (ee_admission.rule) — чистая логика,
// без обращения к базе. Разбирает его pipeline/src/ee_rules.py: пока только
// у бакалавриата и цельного обучения Тартуского университета и TalTech
// (docs/PLAN-ESTONIA.md, раздел 9).
//
// Две модели:
// - weighted (Тартуский университет): балл — сумма результатов по шкале
//   0–100, умноженных на доли; вариантов формулы бывает несколько,
//   засчитывается лучший. Пороги «для подачи» и «гарантирует место»,
//   надбавки за широкую математику и медаль — со страниц ut.ee.
// - thresholds (TalTech): балла нет, есть минимумы по госэкзаменам «для
//   подачи» и «гарантирует место» и число мест.
//
// Правило — факт без подтверждения человеком (решение владельца 2026-10-11).
// Форма проверяется строго: что-то незнакомое — правило не показывается
// вовсе, а не показывается наполовину.

export type EeExam = "estonian" | "math";

/** Составляющая балла: госэкзамен или другое (испытание вуза, письмо) — название по-эстонски. */
export type EeRulePart = ({ exam: EeExam } | { other: string }) & { weight: number };

export type EeEnglishLevel = "B2" | "C1";

export type EeWeightedRule = {
  model: "weighted";
  variants: EeRulePart[][];
  applyMin: number | null;
  guaranteeMin: number | null;
  wideMathBonus: number | null;
  medalBonus: number | null;
  english: EeEnglishLevel | null;
};

export type EeThresholdSet = {
  math: number;
  estonian: number;
  estonianSecond: number;
  english: EeEnglishLevel | null;
};

export type EeThresholdRule = {
  model: "thresholds";
  apply: EeThresholdSet | null;
  guarantee: EeThresholdSet;
  places: number | null;
  /** false — места получают все, кто выше порога, рейтинга нет. */
  ranking: boolean;
};

export type EeRule = EeWeightedRule | EeThresholdRule;

type Raw = Record<string, unknown>;

const isObject = (value: unknown): value is Raw => typeof value === "object" && value !== null && !Array.isArray(value);
const isPoints = (value: unknown): value is number =>
  typeof value === "number" && Number.isInteger(value) && value >= 0 && value <= 100;
const pointsOrNull = (value: unknown): number | null | undefined =>
  value === null || value === undefined ? null : isPoints(value) ? value : undefined;
const englishOf = (value: unknown): EeEnglishLevel | null | undefined =>
  value === undefined || value === null ? null : value === "B2" || value === "C1" ? value : undefined;

function partOf(value: unknown): EeRulePart | null {
  if (!isObject(value) || !isPoints(value.weight) || value.weight === 0) return null;
  if (value.exam === "estonian" || value.exam === "math") return { exam: value.exam, weight: value.weight };
  if (typeof value.other === "string" && value.other.trim() !== "") return { other: value.other, weight: value.weight };
  return null;
}

function weightedOf(value: Raw): EeWeightedRule | null {
  if (!Array.isArray(value.variants) || value.variants.length === 0) return null;
  const variants: EeRulePart[][] = [];
  for (const rawVariant of value.variants) {
    if (!Array.isArray(rawVariant) || rawVariant.length === 0) return null;
    const parts = rawVariant.map(partOf);
    if (parts.some((part) => part === null)) return null;
    const variant = parts as EeRulePart[];
    if (variant.reduce((sum, part) => sum + part.weight, 0) !== 100) return null;
    variants.push(variant);
  }
  const applyMin = pointsOrNull(value.apply_min);
  const guaranteeMin = pointsOrNull(value.guarantee_min);
  const wideMathBonus = pointsOrNull(value.wide_math_bonus);
  const medalBonus = pointsOrNull(value.medal_bonus);
  const requirements = value.requirements ?? {};
  if (!isObject(requirements)) return null;
  const english = englishOf(requirements.english);
  if ([applyMin, guaranteeMin, wideMathBonus, medalBonus, english].includes(undefined)) return null;
  return {
    model: "weighted",
    variants,
    applyMin: applyMin as number | null,
    guaranteeMin: guaranteeMin as number | null,
    wideMathBonus: wideMathBonus as number | null,
    medalBonus: medalBonus as number | null,
    english: english as EeEnglishLevel | null,
  };
}

function thresholdSetOf(value: unknown): EeThresholdSet | null {
  if (!isObject(value)) return null;
  const english = englishOf(value.english);
  if (!isPoints(value.math) || !isPoints(value.estonian) || !isPoints(value.estonian_second) || english === undefined) {
    return null;
  }
  return { math: value.math, estonian: value.estonian, estonianSecond: value.estonian_second, english };
}

function thresholdsOf(value: Raw): EeThresholdRule | null {
  const guarantee = thresholdSetOf(value.guarantee);
  if (guarantee === null || typeof value.ranking !== "boolean") return null;
  const apply = value.apply === null || value.apply === undefined ? null : thresholdSetOf(value.apply);
  if (apply === null && value.apply !== null && value.apply !== undefined) return null;
  const places = value.places === null || value.places === undefined ? null : value.places;
  if (places !== null && !(typeof places === "number" && Number.isInteger(places) && places > 0)) return null;
  // с рейтингом нужны порог для подачи и число мест; без рейтинга их нет
  if (value.ranking ? apply === null || places === null : apply !== null || places !== null) return null;
  return { model: "thresholds", apply, guarantee, places: places as number | null, ranking: value.ranking };
}

export function parseRule(value: unknown): EeRule | null {
  if (!isObject(value)) return null;
  if (value.model === "weighted") return weightedOf(value);
  if (value.model === "thresholds") return thresholdsOf(value);
  return null;
}
