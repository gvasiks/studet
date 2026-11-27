// Версии одного учебного плана у эстонских программ — чистая логика, без
// обращения к базе (запросы — ee-variant-queries.ts).
//
// Государственный портал хранит несколько записей одной программы одного
// учреждения: старую и новую версию учебного плана (например, две
// «Audiovisuaalne meedia» в Таллинском университете). На карточках они
// выглядели одинаково — 76 групп на 2026-11-23. Решение владельца 2026-11-23
// («Специализация и конкурс»): у таких записей показывать
//   - специализацию с портала, если она у записей группы разная;
//   - конкурс SAIS (год последнего или «нет»), если он у записей разный.
// У программ без двойника ничего не добавляется. Совпадающее у всех записей
// группы не показывается: оно их не различает.
// Решение владельца 2026-11-27 («Показать дату записи»): если ни специализация,
// ни конкурс группу не различают, показывается год, когда запись появилась на
// портале (у старых — 2018, первая загрузка портала). Это не год учебного плана.

export type EeVariantSource = {
  id: string;
  university_id: string;
  name_et: string | null;
  degree_level: string;
  language_of_instruction: string;
};

/** Последний конкурс программы в SAIS: год или null, если портал не называет дат. */
export type EeAdmissionYear = { year: number | null };

export type EeVariant = {
  /** Специализация, как на портале; нет поля — специализация группу не различает. */
  specialization?: string;
  /** Конкурс SAIS: год (null — без даты) или "none" — у записи конкурса нет. Нет поля — не различает. */
  admission?: EeAdmissionYear | "none";
  /** Год записи на портале — только если специализация и конкурс группу не различают. */
  portalYear?: number;
};

// Год по эстонским часам: подача, открытая 1 января в 00:00 по Таллину, по
// UTC начинается ещё 31 декабря.
const YEAR = new Intl.DateTimeFormat("en", { year: "numeric", timeZone: "Europe/Tallinn" });

export function tallinnYear(moment: string): number {
  return Number(YEAR.format(new Date(moment)));
}

export function admissionYear(opensAt: string | null, closesAt: string | null): number | null {
  const moment = opensAt ?? closesAt;
  return moment === null ? null : tallinnYear(moment);
}

export function eeVariants(
  programmes: readonly EeVariantSource[],
  specializations: ReadonlyMap<string, string>,
  admissions: ReadonlyMap<string, EeAdmissionYear>,
  portalYears: ReadonlyMap<string, number> = new Map(),
): Map<string, EeVariant> {
  const groups = new Map<string, EeVariantSource[]>();
  for (const programme of programmes) {
    if (!programme.name_et) continue;
    const key = [programme.university_id, programme.name_et, programme.degree_level, programme.language_of_instruction].join("\u0000");
    groups.set(key, [...(groups.get(key) ?? []), programme]);
  }

  const result = new Map<string, EeVariant>();
  for (const group of groups.values()) {
    if (group.length < 2) continue;
    const specs = group.map((p) => specializations.get(p.id) ?? "");
    const differentSpecs = new Set(specs.map((s) => s.toLowerCase())).size > 1;
    const admissionKeys = group.map((p) => {
      const admission = admissions.get(p.id);
      return admission === undefined ? "none" : String(admission.year);
    });
    const differentAdmissions = new Set(admissionKeys).size > 1;
    const years = group.map((p) => portalYears.get(p.id));
    const differentYears = !differentSpecs && !differentAdmissions && new Set(years).size > 1;

    group.forEach((programme, index) => {
      const variant: EeVariant = {};
      if (differentSpecs && specs[index]) variant.specialization = specs[index];
      if (differentAdmissions) variant.admission = admissions.get(programme.id) ?? "none";
      if (differentYears && years[index] !== undefined) variant.portalYear = years[index];
      if (Object.keys(variant).length > 0) result.set(programme.id, variant);
    });
  }
  return result;
}

// Портал иногда пишет в специализацию целый перечень (до 544 знаков на
// 2026-11-24). На карточке каталога он занял бы полкарточки, поэтому там
// показывается начало — до 80 знаков, по границе слова, с многоточием
// (решение владельца 2026-11-24). На странице программы — полностью.
export const CARD_SPECIALIZATION_CHARS = 80;

export function shorten(text: string, limit: number): string {
  if (text.length <= limit) return text;
  const cut = text.slice(0, limit);
  const space = cut.lastIndexOf(" ");
  // Слово длиннее предела режем как есть, иначе — по последнему пробелу.
  const head = space > 0 ? cut.slice(0, space) : cut;
  return `${head.replace(/[\s,;]+$/, "")}…`;
}

/**
 * Подписи для карточки и страницы программы, по строке на различие.
 * specializationLimit — сколько знаков специализации показать (карточка);
 * без него специализация выводится полностью (страница программы).
 */
export function variantLines(
  variant: EeVariant | undefined,
  texts: { specialization: string; admission: string; admissionUndated: string; noAdmission: string; portalYear: string },
  specializationLimit?: number,
): string[] {
  if (!variant) return [];
  const lines: string[] = [];
  if (variant.specialization) {
    const name =
      specializationLimit === undefined ? variant.specialization : shorten(variant.specialization, specializationLimit);
    lines.push(texts.specialization.replace("{name}", name));
  }
  if (variant.admission === "none") lines.push(texts.noAdmission);
  else if (variant.admission) {
    lines.push(
      variant.admission.year === null
        ? texts.admissionUndated
        : texts.admission.replace("{year}", String(variant.admission.year)),
    );
  }
  if (variant.portalYear !== undefined) lines.push(texts.portalYear.replace("{year}", String(variant.portalYear)));
  return lines;
}

/** Тексты для variantLines из раздела catalog словаря. */
export function variantTexts(catalog: {
  variantSpecialization: string;
  variantAdmission: string;
  variantAdmissionUndated: string;
  variantNoAdmission: string;
  variantPortalYear: string;
}) {
  return {
    specialization: catalog.variantSpecialization,
    admission: catalog.variantAdmission,
    admissionUndated: catalog.variantAdmissionUndated,
    noAdmission: catalog.variantNoAdmission,
    portalYear: catalog.variantPortalYear,
  };
}
