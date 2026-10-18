// Прошлогодний конкурс латвийской программы (statistika.vupp.lv; строки
// пишет pipeline/src/vupp_stats.py, связь программы с кодом приёма
// подтверждает владелец — programme_vupp_link). Чистая логика без обращения
// к базе — читается и тестами.
//
// Только факты о прошедшем приёме: места, заявления, с 1-м приоритетом,
// предварительно прошли конкурс. Проходных баллов портал не публикует,
// поэтому ни процентов, ни «проходишь» (CLAUDE.md, «Балл и прошлогодний
// конкурс»).

export type VuppStat = {
  admissionYear: number;
  /** Код приёма вуза: «207B7», «RMBS0». */
  programmeCode: string;
  /** Название на портале — латышское, как в источнике. */
  programmeName: string;
  /** Как на портале: «Pilna laika (dienas)». */
  studyMode: string;
  /** Как на портале: «Budžets», «Maksa». */
  funding: string;
  city: string;
  /** null — портал числа не дал. */
  places: number | null;
  /** Вместо числа мест «*» — «neierobežots vietu skaits». */
  placesUnlimited: boolean;
  applications: number | null;
  firstPriority: number | null;
  passed: number | null;
  /** Заголовок среза: «2. kārtas apstiprinātie pieteikumi…». */
  stage: string;
  portalUpdatedOn: string | null;
  sourceUrl: string;
  extractedAt: string;
};

/** Строки одного названия на портале. У программы с подпрограммами
 * названий несколько (биология ЛУ: «…Bioloģija», «…Biomedicīna»); очная и
 * заочная форма у РТУ — разные коды с одним названием, это одна группа. */
export type VuppGroup = { name: string; rows: VuppStat[] };

export type VuppYear = {
  year: number;
  /** После какого тура срез; null — заголовок портала не разобран. */
  round: number | null;
  portalUpdatedOn: string | null;
  sourceUrl: string;
  extractedAt: string;
  groups: VuppGroup[];
};

// Значения портала -> ключи словаря. Незнакомое значение показывается как
// есть, по-латышски: лучше непереведённое слово, чем выдуманный перевод.
const FUNDING_KEYS: Record<string, VuppFundingKey> = { Budžets: "budget", Maksa: "paid" };
const MODE_KEYS: Record<string, VuppModeKey> = {
  "Pilna laika (dienas)": "fullDay",
  "Pilna laika (vakara)": "fullEvening",
  "Nepilna laika (klātiene vai vakara)": "partEvening",
  "Nepilna laika (neklātiene)": "partExtramural",
  "Nepilna laika (tālmācība)": "partDistance",
};
export type VuppFundingKey = "budget" | "paid";
export type VuppModeKey = "fullDay" | "fullEvening" | "partEvening" | "partExtramural" | "partDistance";

const FUNDING_ORDER: VuppFundingKey[] = ["budget", "paid"];
const MODE_ORDER: VuppModeKey[] = ["fullDay", "fullEvening", "partEvening", "partExtramural", "partDistance"];

export function vuppFundingKey(funding: string): VuppFundingKey | null {
  return FUNDING_KEYS[funding] ?? null;
}

export function vuppModeKey(mode: string): VuppModeKey | null {
  return MODE_KEYS[mode] ?? null;
}

/** «2. kārtas apstiprinātie pieteikumi…» -> 2. */
export function vuppRound(stage: string): number | null {
  const match = /^(\d+)\.\s*kārtas/.exec(stage);
  return match ? Number(match[1]) : null;
}

function rank(index: number): number {
  return index === -1 ? Number.MAX_SAFE_INTEGER : index;
}

function compareRows(a: VuppStat, b: VuppStat): number {
  const funding =
    rank(FUNDING_ORDER.indexOf(vuppFundingKey(a.funding)!)) - rank(FUNDING_ORDER.indexOf(vuppFundingKey(b.funding)!));
  if (funding !== 0) return funding;
  const mode = rank(MODE_ORDER.indexOf(vuppModeKey(a.studyMode)!)) - rank(MODE_ORDER.indexOf(vuppModeKey(b.studyMode)!));
  if (mode !== 0) return mode;
  return a.city.localeCompare(b.city, "lv");
}

/** Название группы строки. Филиал ЛУ на портале — отдельное название
 * («Pirmsskolas skolotājs (Cēsis)» в строке города Cēsis), но это та же
 * программа, а город и так стоит в строке: пометка снимается, и филиалы
 * идут одной таблицей с Ригой. */
export function vuppGroupName(row: VuppStat): string {
  const suffix = ` (${row.city})`;
  return row.programmeName.endsWith(suffix) ? row.programmeName.slice(0, -suffix.length) : row.programmeName;
}

/** Самый поздний год программы: строки по названиям, внутри — бюджет,
 * потом платные; очная форма раньше заочной. null — цифр нет. */
export function latestVuppYear(stats: VuppStat[]): VuppYear | null {
  if (stats.length === 0) return null;
  const year = Math.max(...stats.map((stat) => stat.admissionYear));
  const rows = stats.filter((stat) => stat.admissionYear === year);
  const byName = new Map<string, VuppStat[]>();
  for (const row of rows) {
    const name = vuppGroupName(row);
    byName.set(name, [...(byName.get(name) ?? []), row]);
  }
  const groups = [...byName.entries()]
    .sort(([a], [b]) => a.localeCompare(b, "lv"))
    .map(([name, groupRows]) => ({ name, rows: [...groupRows].sort(compareRows) }));
  const first = rows[0];
  return {
    year,
    round: vuppRound(first.stage),
    portalUpdatedOn: first.portalUpdatedOn,
    sourceUrl: first.sourceUrl,
    extractedAt: first.extractedAt,
    groups,
  };
}
