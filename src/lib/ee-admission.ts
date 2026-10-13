// Последний конкурс эстонской программы — чистая логика, без обращения к
// базе: её можно тестировать отдельно (тот же приём, что outcomes.ts).
//
// Государственный портал Эстонии хранит у программы её последний конкурс, а
// не только открытый: на 2026-10-13 из 546 конкурсов срок подачи ещё не
// прошёл у 16. Поэтому срок показывается как действующий, только пока он не
// прошёл; прошедший — как факт о прошлом приёме (решение владельца
// 2026-10-13: «показываем дату прошлого приёма»).

export type EeAdmission = {
  /** Страница конкурса в системе подачи SAIS. */
  saisUrl: string;
  /** Начало и конец подачи заявлений; null — портал даты не называет. */
  opensAt: string | null;
  closesAt: string | null;
  /** Страница программы на портале, откуда это взято. */
  sourceUrl: string;
  extractedAt: string;
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
