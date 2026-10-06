import type { Country } from "@/i18n/config";
import { getProgrammeIdsWithFormula } from "@/lib/formula-queries";
import { getLtProgrammeIdsWithFormula } from "@/lib/lt-score-queries";

// Для каких программ страны есть расчёт балла — кнопка на карточках
// каталога и «моего списка». Формулы у стран устроены по-разному и лежат в
// разных таблицах: в Латвии своя у каждой программы и подтверждена
// человеком, в Литве общая на страну и сверена с официальным калькулятором.
export function getCalculatorProgrammeIds(country: Country): Promise<Set<string>> {
  return country === "LT" ? getLtProgrammeIdsWithFormula() : getProgrammeIdsWithFormula();
}
