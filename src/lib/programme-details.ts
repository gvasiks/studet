// Диплом, квалификация и описание программы — чистая логика выбора, без
// обращения к базе (тот же приём, что outcomes.ts): её можно тестировать
// отдельно.
//
// Сведения приходят из двух источников и на двух языках:
//   NIID.lv — официальные латышские названия (pipeline/src/enrich_niid_details.py);
//   lu.lv   — английские страницы программ ЛУ (pipeline/src/enrich_lu_details.py).
// Переводить название диплома сами мы не вправе, поэтому показываем то, что
// есть, и помечаем язык: атрибутом lang (WCAG 3.1.2) и строкой для человека.

export type ProgrammeDetailsSource = {
  degree_awarded_lv?: string | null;
  degree_awarded_en?: string | null;
  qualification_lv?: string | null;
  diploma_document_lv?: string | null;
  description_lv?: string | null;
  description_en?: string | null;
  details_source_url?: string | null;
  details_extracted_at?: string | null;
};

export type ProgrammeDetails = {
  /** Язык показанных названий и описания. */
  lang: "lv" | "en";
  degree: string | null;
  qualification: string | null;
  document: string | null;
  /** Абзацы описания; пустой массив — описания нет. */
  paragraphs: string[];
  /** Сайт-источник без «www.»: «niid.lv», «lu.lv». null — адреса нет. */
  sourceHost: string | null;
  sourceUrl: string | null;
  extractedAt: string | null;
};

function splitParagraphs(text: string | null | undefined): string[] {
  if (!text) return [];
  return text
    .split(/\n\s*\n/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
}

/** «https://www.niid.lv/niid_search/program/543» -> «niid.lv». */
export function sourceHost(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return null;
  }
}

// Латышский набор (NIID) и английский (ЛУ) на практике не пересекаются: у
// программы есть один из них. Если когда-нибудь окажутся оба, берётся тот,
// что на языке страницы.
export function pickDetails(record: ProgrammeDetailsSource, locale: string): ProgrammeDetails | null {
  const latvian = {
    lang: "lv" as const,
    degree: record.degree_awarded_lv ?? null,
    qualification: record.qualification_lv ?? null,
    document: record.diploma_document_lv ?? null,
    paragraphs: splitParagraphs(record.description_lv),
  };
  const english = {
    lang: "en" as const,
    degree: record.degree_awarded_en ?? null,
    qualification: null,
    document: null,
    paragraphs: splitParagraphs(record.description_en),
  };
  const hasAny = (set: typeof latvian | typeof english) =>
    Boolean(set.degree || set.qualification || set.document || set.paragraphs.length > 0);

  const preferred = locale === "en" ? [english, latvian] : [latvian, english];
  const chosen = preferred.find(hasAny);
  if (!chosen) return null;

  return {
    ...chosen,
    sourceHost: sourceHost(record.details_source_url),
    sourceUrl: record.details_source_url ?? null,
    extractedAt: record.details_extracted_at ?? null,
  };
}
