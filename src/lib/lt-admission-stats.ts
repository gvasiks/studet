// Цифры прошлого приёма литовской программы (таблица lt_admission_stat,
// её пишет pipeline/src/lt_load_admission_stats.py). Чистая логика без
// обращения к базе — читается и тестами.
//
// В таблице только суммы основного приёма по виду места. Ни числа мест, ни
// проходных баллов в источнике нет, поэтому блок на карточке — факты о
// прошлом приёме без оценки шансов (CLAUDE.md, «Балл и прошлогодний
// конкурс»).

// state — место за счёт государства, stipend — место со стипендией на
// обучение в негосударственной школе, paid — платное. Порядок показа.
export const LT_FUNDING_KINDS = ["state", "stipend", "paid"] as const;
export type LtFundingKind = (typeof LT_FUNDING_KINDS)[number];

export type LtAdmissionStat = {
  admissionYear: number;
  funding: LtFundingKind;
  /** Сколько раз программу внесли в заявление на место этого вида. */
  applications: number;
  /** Из них первым номером. */
  firstPriority: number;
  invited: number;
  signed: number;
  sourceUrl: string;
  extractedAt: string;
};

export type LtAdmissionYear = {
  year: number;
  rows: LtAdmissionStat[];
  sourceUrl: string;
  extractedAt: string;
};

/** Самый поздний год, который есть у программы, строки — в порядке видов места. null — чисел нет. */
export function latestAdmissionYear(stats: LtAdmissionStat[]): LtAdmissionYear | null {
  if (stats.length === 0) return null;
  const year = Math.max(...stats.map((stat) => stat.admissionYear));
  const rows = LT_FUNDING_KINDS.flatMap((funding) =>
    stats.filter((stat) => stat.admissionYear === year && stat.funding === funding),
  );
  if (rows.length === 0) return null;
  return { year, rows, sourceUrl: rows[0].sourceUrl, extractedAt: rows[0].extractedAt };
}
