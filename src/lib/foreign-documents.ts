// Чек-лист документов для иностранных абитуриентов (docs/PLAN-FOREIGNERS.md,
// шаг 3). Таблица foreign_document_requirement: одна строка — документ,
// который вуз просит на этом уровне. У Латвии сюда приходят только
// подтверждённые строки (решение владельца 2026-11-14); у Литвы и Эстонии —
// и неподтверждённые, с пометкой «извлечено автоматически» (решение 2026-11-19).

// Совпадает с check в миграциях 20261114120000_foreign_document_requirement.sql,
// 20261114130000_foreign_document_aic_statement.sql и 20261120120000_foreign_documents_lt_ee.sql.
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
  // академическое признание иностранного образования вне Латвии: в Литве его
  // делает вуз или SKVC
  "recognition",
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

// by_university — то, что вуз делает сам (миграция 20261114140000): без отметок.
export const DOCUMENT_STAGES = ["application", "before_arrival", "by_university"] as const;
export type DocumentStage = (typeof DOCUMENT_STAGES)[number];

export type DocumentRequirement = {
  document: DocumentKey;
  appliesTo: DocumentCondition;
  stage: DocumentStage;
  /** Уточнение на языке источника (английском). */
  note: string | null;
  sortOrder: number;
  sourceUrl: string;
  /** null — строка извлечена автоматически и человеком не проверена (Литва, Эстония). */
  verifiedAt: string | null;
};

/**
 * Строки базы в типизированный вид; строки с неизвестным ключом отбрасываются.
 * Неподтверждённые строки проходят только с allowUnverified (страны, где факты
 * показываются с пометкой «извлечено автоматически»).
 */
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
  allowUnverified = false,
): DocumentRequirement[] {
  const out: DocumentRequirement[] = [];
  for (const row of rows) {
    if (!row.verified_at && !allowUnverified) continue;
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

/**
 * Источники списка без повторов и самая ранняя дата проверки — для подписи под
 * списком. Если хоть одна строка не проверена человеком, весь список
 * подписывается как извлечённый автоматически (automatic) и без даты.
 */
export function checklistSources(items: DocumentRequirement[]): { urls: string[]; verifiedAt: string | null; automatic: boolean } {
  const urls = [...new Set(items.map((item) => item.sourceUrl))];
  const automatic = items.some((item) => item.verifiedAt === null);
  const dates = items.map((item) => item.verifiedAt).filter((date): date is string => date !== null).sort();
  return { urls, verifiedAt: automatic ? null : (dates[0] ?? null), automatic };
}

/** Ключ отметок в localStorage браузера: список у вуза и уровня свой. */
export function checklistStorageKey(universitySlug: string, degreeLevel: string): string {
  return `studet:documents:${universitySlug}:${degreeLevel}`;
}
