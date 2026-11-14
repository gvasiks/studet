// Чек-лист документов для иностранных абитуриентов (docs/PLAN-FOREIGNERS.md,
// шаг 3). Таблица foreign_document_requirement: одна строка — документ,
// который вуз просит на этом уровне. Сюда приходят только подтверждённые
// строки (решение владельца 2026-11-14).

// Совпадает с check в миграциях 20261114120000_foreign_document_requirement.sql
// и 20261114130000_foreign_document_aic_statement.sql.
export const DOCUMENT_KEYS = [
  "passport",
  "photo",
  "secondary_diploma",
  "bachelor_diploma",
  "transcript",
  "enrolment_letter",
  "english_translation",
  "legalisation",
  "aic_statement",
  "english_certificate",
  "motivation_letter",
  "cv",
  "recommendation_letters",
  "criminal_record",
  "minor_documents",
  "proof_of_funds",
  "application_fee_receipt",
] as const;
export type DocumentKey = (typeof DOCUMENT_KEYS)[number];

export const DOCUMENT_CONDITIONS = [
  "all",
  "docs_issued_outside_eu",
  "non_eu_citizens",
  "visa_required",
  "under_18",
  "final_year",
] as const;
export type DocumentCondition = (typeof DOCUMENT_CONDITIONS)[number];

export const DOCUMENT_STAGES = ["application", "before_arrival"] as const;
export type DocumentStage = (typeof DOCUMENT_STAGES)[number];

export type DocumentRequirement = {
  document: DocumentKey;
  appliesTo: DocumentCondition;
  stage: DocumentStage;
  /** Уточнение на языке источника (английском). */
  note: string | null;
  sortOrder: number;
  sourceUrl: string;
  verifiedAt: string;
};

/** Строки базы в типизированный вид; строки с неизвестным ключом отбрасываются. */
export function parseRequirements(
  rows: {
    document: string;
    applies_to: string;
    stage: string;
    note: string | null;
    sort_order: number;
    source_url: string;
    verified_at: string | null;
  }[],
): DocumentRequirement[] {
  const out: DocumentRequirement[] = [];
  for (const row of rows) {
    if (!row.verified_at) continue;
    if (!(DOCUMENT_KEYS as readonly string[]).includes(row.document)) continue;
    if (!(DOCUMENT_CONDITIONS as readonly string[]).includes(row.applies_to)) continue;
    if (!(DOCUMENT_STAGES as readonly string[]).includes(row.stage)) continue;
    out.push({
      document: row.document as DocumentKey,
      appliesTo: row.applies_to as DocumentCondition,
      stage: row.stage as DocumentStage,
      note: row.note,
      sortOrder: row.sort_order,
      sourceUrl: row.source_url,
      verifiedAt: row.verified_at,
    });
  }
  return out;
}

/** Документы по этапам, в порядке источника; пустые этапы пропускаются. */
export function groupByStage(items: DocumentRequirement[]): { stage: DocumentStage; items: DocumentRequirement[] }[] {
  return DOCUMENT_STAGES.map((stage) => ({
    stage,
    items: items.filter((item) => item.stage === stage).sort((a, b) => a.sortOrder - b.sortOrder),
  })).filter((group) => group.items.length > 0);
}

/** Источники списка без повторов и самая ранняя дата проверки — для подписи под списком. */
export function checklistSources(items: DocumentRequirement[]): { urls: string[]; verifiedAt: string | null } {
  const urls = [...new Set(items.map((item) => item.sourceUrl))];
  const dates = items.map((item) => item.verifiedAt).sort();
  return { urls, verifiedAt: dates[0] ?? null };
}

/** Ключ отметок в localStorage браузера: список у вуза и уровня свой. */
export function checklistStorageKey(universitySlug: string, degreeLevel: string): string {
  return `studet:documents:${universitySlug}:${degreeLevel}`;
}
