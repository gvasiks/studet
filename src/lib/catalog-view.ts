import type { Language } from "@/i18n/config";
import type { ProgrammeWithUniversity } from "./catalog";
import type { CatalogState, LevelKey } from "./catalog-query";
import { LEVEL_KEYS } from "./catalog-query";
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
      programme.name_en,
      programme.university.name_lv,
      programme.university.name_lt,
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
  visible: ProgrammeWithUniversity[];
};

// Порядок: длительность и плата -> поиск -> счётчики по уровням (они не
// зависят от выбранного таба, иначе остальные табы показывали бы нули) ->
// уровень -> сортировка -> "показать ещё". Фильтры базы (город, язык,
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

  return {
    matched: searched.length,
    levelCounts,
    total: atLevel.length,
    visible: sorted.slice(0, state.limit),
  };
}
