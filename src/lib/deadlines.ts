import { httpUrl } from "@/lib/application-channel";

export type ApplicationRound = {
  universityId: string;
  degreeLevel: string | null;
  languageOfInstruction: string | null;
  label: string;
  opensOn: string | null;
  closesOn: string | null;
  note: string | null;
  sourceUrl: string | null;
  // когда человек подтвердил срок (правило 6); публичный запрос отдаёт только подтверждённые
  verifiedAt: string;
};

// Раунд относится к программе, если университет совпадает, а
// degree_level/language_of_instruction либо не заданы (= действуют для
// всех), либо совпадают с полями программы. У одной программы может
// быть несколько подходящих раундов (пример: Turība EN — Autumn и
// Winter intake одновременно) — это не ошибка, а честное отражение
// того, что подать документы можно в любое из окон.
export function matchRounds(
  rounds: ApplicationRound[],
  universityId: string,
  degreeLevel: string,
  languageOfInstruction: string,
): ApplicationRound[] {
  return rounds.filter(
    (round) =>
      round.universityId === universityId &&
      (round.degreeLevel === null || round.degreeLevel === degreeLevel) &&
      (round.languageOfInstruction === null || round.languageOfInstruction === languageOfInstruction),
  );
}

// Источники сроков программы для строки «проверено … Источник» (правило 5):
// одна запись на пару «адрес + день проверки», в порядке появления. Адрес —
// только http(s), иначе ссылки нет (тот же httpUrl, что у «Kur pieteikties»).
export function roundSources(rounds: ApplicationRound[]): { sourceUrl: string | null; verifiedAt: string }[] {
  const seen = new Map<string, { sourceUrl: string | null; verifiedAt: string }>();
  for (const round of rounds) {
    const sourceUrl = httpUrl(round.sourceUrl);
    const key = `${sourceUrl ?? ""}|${round.verifiedAt.slice(0, 10)}`;
    if (!seen.has(key)) seen.set(key, { sourceUrl, verifiedAt: round.verifiedAt });
  }
  return [...seen.values()];
}
