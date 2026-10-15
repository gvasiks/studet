// Последний конкурс эстонской программы — чистая логика, без обращения к
// базе: её можно тестировать отдельно (тот же приём, что outcomes.ts).
//
// Государственный портал Эстонии хранит у программы её последний конкурс, а
// не только открытый: на 2026-10-13 из 546 конкурсов срок подачи ещё не
// прошёл у 16. Поэтому срок показывается как действующий, только пока он не
// прошёл; прошедший — как факт о прошлом приёме (решение владельца
// 2026-10-13: «показываем дату прошлого приёма»).
//
// Условия конкурса (форма обучения, место, начало занятий, финансирование и
// цена) читаются со страницы конкурса в SAIS отдельным загрузчиком
// (pipeline/src/ee_load_admission_details.py). Их может не быть: страница
// ещё не прочитана или SAIS её уже удалил (так с конкурсами старше года).
// Правило конкурса (доли экзаменов, пороги) — ee-rule.ts.

import type { EeRule } from "./ee-rule";

export type EeLoad = "full" | "part" | "unspecified";
export type EePeriod = "semester" | "year" | "credit" | "other";

export type EePrice = {
  amount: number;
  currency: string;
  period: EePeriod;
  /** Период как на странице («semester», «aastamakse», «1 EAP»). */
  periodText: string | null;
  /** Для кого цена, как на странице («Kõik», «Sügissemester»); null — не сказано. */
  target: string | null;
};

// Вариант нагрузки со своим финансированием: у одного конкурса их бывает
// несколько (полная нагрузка бесплатно, неполная платно).
export type EeFunding = { load: EeLoad; paid: boolean; prices: EePrice[] };

export type EeAdmission = {
  /** Страница конкурса в системе подачи SAIS. */
  saisUrl: string;
  /** Начало и конец подачи заявлений; null — портал даты не называет. */
  opensAt: string | null;
  closesAt: string | null;
  /** Страница программы на портале, откуда это взято. */
  sourceUrl: string;
  extractedAt: string;
  /** Название конкурса в SAIS; null — страница конкурса не прочитана или удалена. */
  title: string | null;
  /** Форма обучения как на странице: «päevane õpe», «sessioonõpe»; две — через запятую. */
  studyForm: string | null;
  /** Место учёбы как на странице: «Tartu», «Reola küla, Tartumaa». */
  location: string | null;
  /** Начало занятий, «ГГГГ-ММ-ДД». */
  startsOn: string | null;
  funding: EeFunding[];
  /** Когда страница конкурса была прочитана. */
  detailsFetchedAt: string | null;
  /** Правило конкурса; null — не разобрано (ee-rule.ts). */
  rule: EeRule | null;
  /** Страница вуза, откуда взяты пороги (ut.ee); null — всё правило со страницы SAIS. */
  ruleSourceUrl: string | null;
  ruleExtractedAt: string | null;
};

// current — подача открыта или ещё впереди; past — срок прошёл; undated —
// конкурс есть, но конца подачи портал не называет (сказать «открыт» нельзя).
export type EeAdmissionState = "current" | "past" | "undated";

export function admissionState(admission: Pick<EeAdmission, "closesAt">, now: Date): EeAdmissionState {
  if (admission.closesAt === null) return "undated";
  return new Date(admission.closesAt).getTime() >= now.getTime() ? "current" : "past";
}

// Сроки портала — моменты времени по эстонским часам: подача открывается в
// полночь и закрывается в 23:59. Сервер сайта живёт по UTC, и без часового
// пояса начало «5 октября 00:00» показалось бы как 4 октября.
export function tallinnDate(moment: string, language: string): string {
  return new Date(moment).toLocaleDateString(language, { timeZone: "Europe/Tallinn" });
}

// Дата без времени («2026-09-01») — день как записан, без сдвига на часовой
// пояс сервера или посетителя.
export function plainDate(day: string, language: string): string {
  return new Date(`${day.slice(0, 10)}T00:00:00Z`).toLocaleDateString(language, { timeZone: "UTC" });
}

// Формы обучения, для которых в словарях есть перевод. Закрытого списка у
// SAIS нет: незнакомая форма показывается как на странице, по-эстонски.
export type EeStudyFormKey = "daytime" | "session";

export function studyFormKey(studyForm: string | null): EeStudyFormKey | null {
  if (studyForm === "päevane õpe") return "daytime";
  if (studyForm === "sessioonõpe") return "session";
  return null;
}

// У конкурса бывает две формы обучения сразу — в базе они через запятую.
export function studyForms(studyForm: string | null): string[] {
  return (studyForm ?? "")
    .split(",")
    .map((form) => form.trim())
    .filter(Boolean);
}

const LOADS: readonly string[] = ["full", "part", "unspecified"];
const PERIODS: readonly string[] = ["semester", "year", "credit", "other"];

// Финансирование лежит в базе как JSON: тип его содержимого никто не
// гарантирует, поэтому каждая запись проверяется, а непонятная отбрасывается
// (лучше не показать цену, чем показать мусор).
export function parseFunding(value: unknown): EeFunding[] {
  if (!Array.isArray(value)) return [];
  const result: EeFunding[] = [];
  for (const entry of value) {
    if (typeof entry !== "object" || entry === null) continue;
    const { load, paid, prices } = entry as Record<string, unknown>;
    if (typeof load !== "string" || !LOADS.includes(load) || typeof paid !== "boolean") continue;
    const cleanPrices: EePrice[] = [];
    for (const price of Array.isArray(prices) ? prices : []) {
      if (typeof price !== "object" || price === null) continue;
      const { amount, currency, period, period_text: periodText, target } = price as Record<string, unknown>;
      if (typeof amount !== "number" || !Number.isFinite(amount) || amount <= 0) continue;
      if (typeof currency !== "string" || currency === "") continue;
      cleanPrices.push({
        amount,
        currency,
        period: typeof period === "string" && PERIODS.includes(period) ? (period as EePeriod) : "other",
        periodText: typeof periodText === "string" && periodText !== "" ? periodText : null,
        target: typeof target === "string" && target !== "" ? target : null,
      });
    }
    result.push({ load: load as EeLoad, paid, prices: cleanPrices });
  }
  return result;
}

// Срок подачи для карточки эстонской программы: конец подачи, если он есть
// в перечне действующих и ещё не прошёл. Перечень живёт в памяти сервера
// пять минут, поэтому срок сверяется с часами ещё раз.
export function openDeadline(deadlines: Readonly<Record<string, string>>, programmeId: string, now: Date): string | null {
  const closesAt = deadlines[programmeId];
  if (closesAt === undefined) return null;
  return new Date(closesAt).getTime() >= now.getTime() ? closesAt : null;
}
