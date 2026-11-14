// Минимальный результат теста по английскому у программы на английском
// (docs/PLAN-FOREIGNERS.md, шаг 4; таблица english_requirement). Языковое
// требование — поле правила 6: сюда приходят только подтверждённые строки.

export type EnglishRequirement = {
  /** id программы или null — требование вуза для всего уровня. */
  programmeId: string | null;
  ieltsMin: number | null;
  toeflIbtMin: number | null;
  /** Минимум по шкале TOEFL iBT 1–6 (с 21.01.2026), если вуз его называет. */
  toeflIbtBand: number | null;
  note: string | null;
  sourceUrl: string;
  verifiedAt: string;
};

type Row = {
  programme_id: string | null;
  ielts_min: number | string | null;
  toefl_ibt_min: number | null;
  toefl_ibt_band: number | string | null;
  note: string | null;
  source_url: string;
  verified_at: string | null;
};

const num = (value: number | string | null): number | null => (value === null ? null : Number(value));

export function parseEnglishRequirements(rows: Row[]): EnglishRequirement[] {
  return rows
    .filter((row) => row.verified_at && (row.ielts_min !== null || row.toefl_ibt_min !== null))
    .map((row) => ({
      programmeId: row.programme_id,
      ieltsMin: num(row.ielts_min),
      toeflIbtMin: row.toefl_ibt_min,
      toeflIbtBand: num(row.toefl_ibt_band),
      note: row.note,
      sourceUrl: row.source_url,
      verifiedAt: row.verified_at!,
    }));
}

/** Строка программы важнее строки вуза: у ЛУ требования различаются по программам. */
export function pickEnglishRequirement(rows: EnglishRequirement[], programmeId: string): EnglishRequirement | null {
  return rows.find((row) => row.programmeId === programmeId) ?? rows.find((row) => row.programmeId === null) ?? null;
}
