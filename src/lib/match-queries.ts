import { cache } from "react";
import type { Locale } from "@/i18n/config";
import { supabase } from "@/lib/supabase";
import { localizedName } from "@/lib/names";
import { getLevelCoefficients } from "@/lib/formula-queries";
import type { ExamLevel, FormulaGate, FormulaTerm } from "@/lib/formula";
import { FIXTURE_FORMULAS, FIXTURE_LEVEL_COEFFICIENTS, FIXTURE_REQUIREMENTS } from "@/lib/match-fixture";
import type { MatchFormula, MatchRequirement } from "@/lib/match";

export type MatchData = {
  formulas: MatchFormula[];
  // Программы без формулы, но с подтверждёнными требованиями — уже без
  // programme_id из formulas (см. ниже), чтобы одна программа не попала
  // в обратный поиск дважды.
  requirements: MatchRequirement[];
  levelCoefficients: Record<ExamLevel, number>;
  // true — показаны выдуманные данные из match-fixture.ts (только `next dev`)
  isFixture: boolean;
};

// Выдуманные формулы — только локально: `next dev` с MATCH_FIXTURE=1.
// Условие по NODE_ENV намеренно жёсткое: в `next build` / `next start` его не
// обойти переменной окружения, иначе одна лишняя строка в настройках хостинга
// показала бы живым людям несуществующие программы с несуществующими
// коэффициентами.
function fixtureEnabled(): boolean {
  return process.env.NODE_ENV === "development" && process.env.MATCH_FIXTURE === "1";
}

// Только подтверждённые формулы: их отдаёт сама RLS-политика таблицы formula
// (анонимный ключ неподтверждённых не видит), .not("verified_at", ...) ниже
// — не защита, а пояснение того же условия. Программы, пропавшие с сайта
// вуза (missed_runs >= 2), скрыты политикой таблицы programme. Только
// вариант "ce": варианты для льготников и иностранцев — отдельная задача.
export const getMatchData = cache(async (locale: Locale): Promise<MatchData> => {
  if (fixtureEnabled()) {
    return {
      formulas: FIXTURE_FORMULAS,
      requirements: FIXTURE_REQUIREMENTS,
      levelCoefficients: FIXTURE_LEVEL_COEFFICIENTS,
      isFixture: true,
    };
  }

  const { data: rows, error } = await supabase
    .from("formula")
    .select(
      "id, programme_id, valid_from, source_url, verified_at, programme!inner(slug, name_lv, name_en, university!inner(slug, name_lv, name_en))",
    )
    .eq("variant", "ce")
    .is("valid_to", null)
    .not("verified_at", "is", null)
    .order("valid_from", { ascending: false });

  if (error) throw error;
  if (!rows || rows.length === 0) {
    const [requirements, levelCoefficients] = await Promise.all([
      getMatchRequirements(locale, new Set()),
      getLevelCoefficients(),
    ]);
    return { formulas: [], requirements, levelCoefficients, isFixture: false };
  }

  // На программу — самая свежая формула (rows уже по убыванию valid_from)
  const latestByProgramme = new Map<string, (typeof rows)[number]>();
  for (const row of rows) if (!latestByProgramme.has(row.programme_id)) latestByProgramme.set(row.programme_id, row);
  const chosen = [...latestByProgramme.values()];
  const ids = chosen.map((row) => row.id);

  const programmeIdsWithFormula = new Set(chosen.map((row) => row.programme_id));
  const [termsResult, gatesResult, levelCoefficients, requirements] = await Promise.all([
    supabase.from("formula_term").select("formula_id, kind, subject, coefficient, optional").in("formula_id", ids),
    supabase.from("formula_gate").select("formula_id, subject, min_percent").in("formula_id", ids),
    getLevelCoefficients(),
    getMatchRequirements(locale, programmeIdsWithFormula),
  ]);
  if (termsResult.error) throw termsResult.error;
  if (gatesResult.error) throw gatesResult.error;

  const termsByFormula = new Map<string, FormulaTerm[]>();
  for (const term of termsResult.data ?? []) {
    const list = termsByFormula.get(term.formula_id) ?? [];
    list.push({
      kind: term.kind as FormulaTerm["kind"],
      subject: term.subject,
      coefficient: Number(term.coefficient),
      optional: term.optional,
    });
    termsByFormula.set(term.formula_id, list);
  }
  const gatesByFormula = new Map<string, FormulaGate[]>();
  for (const gate of gatesResult.data ?? []) {
    const list = gatesByFormula.get(gate.formula_id) ?? [];
    list.push({ subject: gate.subject, minPercent: Number(gate.min_percent) });
    gatesByFormula.set(gate.formula_id, list);
  }

  const formulas: MatchFormula[] = chosen.map((row) => {
    const programme = row.programme as unknown as {
      slug: string;
      name_lv: string | null;
      name_en: string | null;
      university: { slug: string; name_lv: string; name_en: string | null };
    };
    return {
      formulaId: row.id,
      programmeSlug: programme.slug,
      programmeName: localizedName(programme, locale),
      universitySlug: programme.university.slug,
      universityName: localizedName(programme.university, locale),
      verifiedAt: row.verified_at as string,
      sourceUrl: row.source_url,
      terms: termsByFormula.get(row.id) ?? [],
      gates: gatesByFormula.get(row.id) ?? [],
    };
  });

  return { formulas, requirements, levelCoefficients, isFixture: false };
});

// Требования читаются отдельным запросом, не JOIN'ом от formula: у
// большинства программ требований пока нет вовсе (охват растёт по частям,
// план 2026-09-21, пункт 02), и связывать несвязанные наборы через JOIN
// только усложнило бы типы без выгоды. excludeProgrammeIds — программы,
// у которых уже есть формула: их требования избыточны (формула строже —
// в ней те же предметы плюс веса), не показываем программу дважды.
async function getMatchRequirements(locale: Locale, excludeProgrammeIds: Set<string>): Promise<MatchRequirement[]> {
  const { data: sets, error } = await supabase
    .from("programme_requirement_set")
    .select(
      "id, programme_id, source_url, verified_at, programme!inner(slug, name_lv, name_en, university!inner(slug, name_lv, name_en))",
    )
    .not("verified_at", "is", null);

  if (error) throw error;
  const rows = (sets ?? []).filter((row) => !excludeProgrammeIds.has(row.programme_id));
  if (rows.length === 0) return [];

  const { data: items, error: itemsError } = await supabase
    .from("programme_requirement")
    .select("requirement_set_id, subject, alternative_group")
    .in(
      "requirement_set_id",
      rows.map((row) => row.id),
    );
  if (itemsError) throw itemsError;

  // Строки одного requirement_set группируются по alternative_group: строки
  // с одинаковым (непустым) значением — одна группа "нужен хотя бы один из
  // них"; alternative_group=null — своя группа из одного предмета.
  const groupsBySet = new Map<string, Map<string, string[]>>();
  for (const item of items ?? []) {
    const bySet = groupsBySet.get(item.requirement_set_id) ?? new Map<string, string[]>();
    const key = item.alternative_group ?? `__solo_${item.subject}`;
    const group = bySet.get(key) ?? [];
    group.push(item.subject);
    bySet.set(key, group);
    groupsBySet.set(item.requirement_set_id, bySet);
  }

  return rows.map((row) => {
    const programme = row.programme as unknown as {
      slug: string;
      name_lv: string | null;
      name_en: string | null;
      university: { slug: string; name_lv: string; name_en: string | null };
    };
    return {
      requirementId: row.id,
      programmeSlug: programme.slug,
      programmeName: localizedName(programme, locale),
      universitySlug: programme.university.slug,
      universityName: localizedName(programme.university, locale),
      verifiedAt: row.verified_at as string,
      sourceUrl: row.source_url,
      subjectGroups: [...(groupsBySet.get(row.id)?.values() ?? [])],
    };
  });
}
