import { isInterestKey, type InterestKey } from "./fields";

// Состояние страницы каталога целиком живёт в URL: поиск, сортировка,
// уровень, фильтры, сколько карточек показано. Без клиентского состояния —
// страница остаётся серверной (правило 4 CLAUDE.md), а любой вид
// каталога можно отправить ссылкой.

export const SORT_KEYS = ["name", "name_desc", "university"] as const;
export type SortKey = (typeof SORT_KEYS)[number];

// Список уровней — в country.ts: какие из них показываются вкладками,
// зависит от страны.
export { LEVEL_KEYS, type LevelKey } from "./country";
import { LEVEL_KEYS, type LevelKey } from "./country";

// Пороги «не дольше N лет» и «не дороже N евро в год» — вопросы анкеты и
// фильтры каталога. Значения выбраны по данным каталога (2026-10-01): у
// бакалавриата и колледжей 250 программ до 3 лет и 438 до 4; плата до
// 3000 EUR — у 165, до 4000 — у 240.
export const DURATION_LIMITS = [3, 4] as const;
export type DurationLimit = (typeof DURATION_LIMITS)[number];

export const FEE_LIMITS = [3000, 4000] as const;
export type FeeLimit = (typeof FEE_LIMITS)[number];

// Кто основал вуз: значения поля university.kind в базе.
export const UNIVERSITY_KINDS = ["public", "private"] as const;
export type UniversityKind = (typeof UNIVERSITY_KINDS)[number];

export const PAGE_SIZE = 12;
// Потолок нужен, чтобы ?limit=999999 не превратился в запрос на весь
// каталог с рендером всех карточек разом.
const MAX_LIMIT = 600;

export type CatalogState = {
  q: string;
  sort: SortKey;
  level: LevelKey | null;
  limit: number;
  cities: string[];
  interests: InterestKey[];
  university?: string;
  language?: string;
  mode?: string;
  budgetOnly: boolean;
  /** Государственный или частный вуз; null — любой. */
  kind: UniversityKind | null;
  /** Не дольше стольких лет; null — без ограничения. */
  maxYears: DurationLimit | null;
  /** Не дороже стольких евро в год; null — без ограничения. */
  maxFee: FeeLimit | null;
};

type SearchParams = Record<string, string | string[] | undefined>;

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

// Города и интересы приходят в двух форматах: одной строкой через запятую
// (ссылка из анкеты, SurveyWizard.tsx) или несколькими одноимёнными
// параметрами (чекбоксы формы фильтра: city=riga&city=jelgava).
function listValues(value: string | string[] | undefined): string[] {
  if (!value) return [];
  const parts = Array.isArray(value) ? value : [value];
  return parts.flatMap((part) => part.split(",")).filter(Boolean);
}

// Значение из адреса принимается, только если оно есть в списке порогов:
// ?years=7 или ?fee=abc — это «без ограничения», а не ошибка.
function oneOf<T extends number>(allowed: readonly T[], value: string | undefined): T | null {
  const parsed = Number(value);
  return (allowed as readonly number[]).includes(parsed) ? (parsed as T) : null;
}

export function parseCatalogState(sp: SearchParams): CatalogState {
  const sort = firstValue(sp.sort);
  const level = firstValue(sp.level);
  const limit = Number(firstValue(sp.limit));
  const kind = firstValue(sp.kind);

  return {
    q: (firstValue(sp.q) ?? "").trim().slice(0, 100),
    sort: (SORT_KEYS as readonly string[]).includes(sort ?? "") ? (sort as SortKey) : "name",
    level: (LEVEL_KEYS as readonly string[]).includes(level ?? "") ? (level as LevelKey) : null,
    limit: Number.isFinite(limit) && limit >= PAGE_SIZE ? Math.min(Math.floor(limit), MAX_LIMIT) : PAGE_SIZE,
    cities: listValues(sp.city),
    interests: listValues(sp.interest).filter(isInterestKey),
    university: firstValue(sp.university) || undefined,
    language: firstValue(sp.language) || undefined,
    mode: firstValue(sp.mode) || undefined,
    budgetOnly: firstValue(sp.budget) === "1",
    kind: (UNIVERSITY_KINDS as readonly string[]).includes(kind ?? "") ? (kind as UniversityKind) : null,
    maxYears: oneOf(DURATION_LIMITS, firstValue(sp.years)),
    maxFee: oneOf(FEE_LIMITS, firstValue(sp.fee)),
  };
}

// Значения по умолчанию в ссылку не попадают — адреса остаются короткими,
// а "чистый" каталог совпадает с каноническим адресом страницы.
export function catalogQuery(state: CatalogState, overrides: Partial<CatalogState> = {}): string {
  const next = { ...state, ...overrides };
  const params = new URLSearchParams();

  if (next.q) params.set("q", next.q);
  if (next.sort !== "name") params.set("sort", next.sort);
  if (next.level) params.set("level", next.level);
  if (next.limit !== PAGE_SIZE) params.set("limit", String(next.limit));
  for (const city of next.cities) params.append("city", city);
  for (const interest of next.interests) params.append("interest", interest);
  if (next.university) params.set("university", next.university);
  if (next.language) params.set("language", next.language);
  if (next.mode) params.set("mode", next.mode);
  if (next.budgetOnly) params.set("budget", "1");
  if (next.kind) params.set("kind", next.kind);
  if (next.maxYears) params.set("years", String(next.maxYears));
  if (next.maxFee) params.set("fee", String(next.maxFee));

  const query = params.toString();
  return query ? `?${query}` : "";
}

/** Есть ли что сбрасывать кнопкой "Notīrīt": сортировка и число карточек — не фильтры. */
export function hasActiveFilters(state: CatalogState): boolean {
  return Boolean(
    state.q ||
      state.level ||
      state.cities.length ||
      state.interests.length ||
      state.university ||
      state.language ||
      state.mode ||
      state.budgetOnly ||
      state.kind ||
      state.maxYears ||
      state.maxFee,
  );
}
