import type { Language } from "@/i18n/config";
import type { ProgrammeWithUniversity } from "./catalog";
import type { CatalogState, LevelKey } from "./catalog-query";
import { LEVEL_KEYS, PAGE_SIZE } from "./catalog-query";
import { localizedName } from "./names";

// Без диакритики и регистра: "riga" находит "Rīga", "sikdatnes" —
// "sīkdatnes". Аудитория пишет то с латышской раскладкой, то без неё.
export function normalize(text: string): string {
  return text.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

// Все слова запроса должны встретиться (в любом порядке) в названии
// программы или вуза, на любом из двух языков. Ищем только по словам
// из названий, не по сокращениям вузов ("RTU").
export function matchesQuery(programme: ProgrammeWithUniversity, query: string): boolean {
  const tokens = normalize(query).split(/\s+/).filter(Boolean);
  if (tokens.length === 0) return true;

  const haystack = normalize(
    [
      programme.name_lv,
      programme.name_lt,
      programme.name_et,
      programme.name_en,
      programme.university.name_lv,
      programme.university.name_lt,
      programme.university.name_et,
      programme.university.name_en,
    ]
      .filter(Boolean)
      .join(" "),
  );
  return tokens.every((token) => haystack.includes(token));
}

// Длительность и плата. Программа БЕЗ значения остаётся в списке: «не
// указано» — не то же самое, что «долго» или «дорого» (у 212 из 489
// программ бакалавриата и колледжей плата не собрана, и скрыть их значило
// бы выдать пробел в данных за свойство программы). Об этом сказано в
// подсказке под фильтром.
export function withinLimits(programme: ProgrammeWithUniversity, state: CatalogState): boolean {
  if (state.maxYears && programme.duration_years !== null && programme.duration_years > state.maxYears) {
    return false;
  }
  if (state.maxFee && programme.tuition_fee_amount !== null && programme.tuition_fee_amount > state.maxFee) {
    return false;
  }
  return true;
}

export function countByLevel(programmes: ProgrammeWithUniversity[]): Record<LevelKey, number> {
  const counts = Object.fromEntries(LEVEL_KEYS.map((key) => [key, 0])) as Record<LevelKey, number>;
  for (const programme of programmes) {
    if (programme.degree_level in counts) counts[programme.degree_level as LevelKey] += 1;
  }
  return counts;
}

export function sortProgrammes(
  programmes: ProgrammeWithUniversity[],
  sort: CatalogState["sort"],
  language: Language,
): ProgrammeWithUniversity[] {
  const collator = new Intl.Collator(language, { sensitivity: "base", numeric: true });
  const byName = (a: ProgrammeWithUniversity, b: ProgrammeWithUniversity) =>
    collator.compare(localizedName(a, language), localizedName(b, language));

  const sorted = [...programmes];
  if (sort === "name_desc") return sorted.sort((a, b) => byName(b, a));
  if (sort === "university") {
    return sorted.sort(
      (a, b) =>
        collator.compare(localizedName(a.university, language), localizedName(b.university, language)) || byName(a, b),
    );
  }
  return sorted.sort(byName);
}

export type CatalogView = {
  /** Сколько программ подошло под фильтры и поиск (до отбора по уровню). */
  matched: number;
  /** Счётчики для табов уровня — по тому же набору, что и `matched`. */
  levelCounts: Record<LevelKey, number>;
  /** Сколько подошло с учётом выбранного уровня — это число "Atrastas N". */
  total: number;
  /** Карточки текущей страницы. */
  visible: ProgrammeWithUniversity[];
  /** Текущая страница (номер из адреса, но не дальше последней) и их число. */
  page: number;
  pages: number;
  /** Какие по счёту программы на странице: «25–48 из 812». */
  from: number;
  to: number;
};

// Порядок: длительность и плата -> поиск -> счётчики по уровням (они не
// зависят от выбранного таба, иначе остальные табы показывали бы нули) ->
// уровень -> сортировка -> страница. Фильтры базы (город, язык,
// направление...) уже применены до вызова.
export function buildCatalogView(
  programmes: ProgrammeWithUniversity[],
  state: CatalogState,
  language: Language,
): CatalogView {
  const limited =
    state.maxYears || state.maxFee ? programmes.filter((programme) => withinLimits(programme, state)) : programmes;
  const searched = state.q ? limited.filter((programme) => matchesQuery(programme, state.q)) : limited;
  const levelCounts = countByLevel(searched);
  const atLevel = state.level ? searched.filter((programme) => programme.degree_level === state.level) : searched;
  const sorted = sortProgrammes(atLevel, state.sort, language);

  const pages = Math.max(1, Math.ceil(atLevel.length / PAGE_SIZE));
  const page = Math.min(state.page, pages);
  const start = (page - 1) * PAGE_SIZE;
  const visible = sorted.slice(start, start + PAGE_SIZE);

  return {
    matched: searched.length,
    levelCounts,
    total: atLevel.length,
    visible,
    page,
    pages,
    from: visible.length > 0 ? start + 1 : 0,
    to: start + visible.length,
  };
}

/**
 * Номера страниц для навигации: первая, последняя, текущая и её соседи, а
 * между ними пропуск («gap») — «1 … 4 5 6 … 34». При семи страницах и
 * меньше — все подряд.
 */
export function pageList(page: number, pages: number): (number | "gap")[] {
  if (pages <= 7) return Array.from({ length: pages }, (_, index) => index + 1);
  const shown = new Set([1, pages, page - 1, page, page + 1].filter((n) => n >= 1 && n <= pages));
  const sorted = [...shown].sort((a, b) => a - b);
  const result: (number | "gap")[] = [];
  sorted.forEach((n, index) => {
    if (index > 0 && n - sorted[index - 1] > 1) result.push(n - sorted[index - 1] === 2 ? n - 1 : "gap");
    result.push(n);
  });
  return result;
}
