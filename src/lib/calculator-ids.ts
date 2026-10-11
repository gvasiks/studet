import type { Country } from "@/i18n/config";
import { getProgrammeIdsWithFormula } from "@/lib/formula-queries";
import { getLtProgrammeIdsWithFormula } from "@/lib/lt-score-queries";
import { remember } from "@/lib/server-memo";

// Сколько перечень живёт в памяти сервера (server-memo.ts). Он нужен каждой
// карточке каталога, а у Литвы за ним стоит чтение всех строк приёма (два
// запроса подряд). Подтверждённая сегодня формула даст кнопку на карточке в
// течение пяти минут; сама страница расчёта читает базу напрямую.
const CALCULATOR_IDS_MEMORY_MS = 5 * 60 * 1000;

// Для каких программ страны есть расчёт балла — кнопка на карточках
// каталога и «моего списка». Формулы у стран устроены по-разному и лежат в
// разных таблицах: в Латвии своя у каждой программы и подтверждена
// человеком, в Литве общая на страну и сверена с официальным калькулятором.
// У Эстонии расчёта балла пока нет (docs/PLAN-ESTONIA.md, фаза 7).
// Множество общее для всех запросов — только читать (.has), не менять.
export function getCalculatorProgrammeIds(country: Country): Promise<Set<string>> {
  return remember(`calculator-ids:${country}`, CALCULATOR_IDS_MEMORY_MS, async () => {
    if (country === "EE") return new Set<string>();
    return country === "LT" ? getLtProgrammeIdsWithFormula() : getProgrammeIdsWithFormula();
  });
}
