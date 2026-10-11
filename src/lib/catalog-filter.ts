import type { ProgrammeFilters, ProgrammeWithUniversity } from "./catalog";

// Фильтры каталога, которые раньше уходили в запрос к базе: город, язык,
// форма, вуз, тип вуза, «только бюджет», интересы. Теперь список программ
// страны лежит в памяти сервера (server-memo.ts), и отбор идёт здесь — без
// обращения к базе на каждый щелчок. Чистая функция: тестируется без базы.
//
// Условия те же, что были в запросе:
// - город сравнивается с городом программы; программа без города под фильтр
//   по городу не попадает;
// - «только бюджет» — вид финансирования «бюджет» или «бюджет и платно»;
//   программа без этого сведения (вся Литва) под фильтр не попадает;
// - интересы — направление программы среди кодов выбранных интересов;
//   программа без разметки под фильтр по интересам не попадает.
export function filterProgrammes(
  programmes: readonly ProgrammeWithUniversity[],
  filters: ProgrammeFilters,
  /** Коды направлений выбранных интересов; null — интересы не выбраны. */
  interestCodes: ReadonlySet<string> | null,
  /** Направление программы: id программы -> код. Нужен только при interestCodes. */
  fieldCodeById: ReadonlyMap<string, string>,
): ProgrammeWithUniversity[] {
  const cities = filters.cities && filters.cities.length > 0 ? filters.cities : null;

  return programmes.filter((programme) => {
    if (interestCodes) {
      const code = fieldCodeById.get(programme.id);
      if (code === undefined || !interestCodes.has(code)) return false;
    }
    if (filters.budgetOnly && programme.funding_type !== "budget" && programme.funding_type !== "both") return false;
    if (cities && (programme.city === null || !cities.includes(programme.city))) return false;
    if (filters.language && programme.language_of_instruction !== filters.language) return false;
    if (filters.mode && programme.study_mode !== filters.mode) return false;
    if (filters.university && programme.university.slug !== filters.university) return false;
    if (filters.kind && programme.university.kind !== filters.kind) return false;
    return true;
  });
}
