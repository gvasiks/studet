export type ApplicationRound = {
  universityId: string;
  degreeLevel: string | null;
  languageOfInstruction: string | null;
  label: string;
  opensOn: string | null;
  closesOn: string | null;
  note: string | null;
  sourceUrl: string | null;
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
