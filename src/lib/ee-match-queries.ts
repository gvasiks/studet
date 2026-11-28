import { supabase } from "@/lib/supabase";
import type { Language } from "@/i18n/config";
import { listProgrammes } from "@/lib/catalog";
import { getEeVariants } from "@/lib/ee-variant-queries";
import type { EeVariant } from "@/lib/ee-variants";
import { parseRule, type EeThresholdRule } from "@/lib/ee-rule";
import { localizedName } from "@/lib/names";
import { remember } from "@/lib/server-memo";

// Данные эстонского «куда можно поступить» (ee-match.ts): программы, у
// которых есть правило следующего учебного года с порогами госэкзаменов
// (ee_next_rule, модель thresholds — пока TalTech 2027/28). Только видимые
// в каталоге программы: список берётся из listProgrammes("EE").

export type EeMatchProgramme = {
  id: string;
  slug: string;
  name: string;
  universitySlug: string;
  universityName: string;
  city: string | null;
  rule: EeThresholdRule;
  newCurriculum: boolean;
  variant: EeVariant | null;
};

export type EeMatchData = {
  programmes: EeMatchProgramme[];
  academicYear: string | null;
  decidedOn: string | null;
  sourceUrl: string | null;
  sourceTitle: string | null;
};

type RuleRow = {
  programme_id: string;
  academic_year: string;
  rule: unknown;
  new_curriculum: boolean;
  source_url: string;
  source_title: string;
  decided_on: string;
};

// PGRST205 / 42P01 — таблицы ещё нет (миграция 20261127130000 не применена).
const MISSING_TABLE = new Set(["PGRST205", "42P01"]);

function nextRules(): Promise<RuleRow[]> {
  return remember("ee-next-rules", 5 * 60 * 1000, async () => {
    const { data, error } = await supabase
      .from("ee_next_rule")
      .select("programme_id, academic_year, rule, new_curriculum, source_url, source_title, decided_on")
      .order("programme_id");
    if (error && MISSING_TABLE.has(error.code)) return [];
    if (error) throw error;
    return data as RuleRow[];
  });
}

export async function getEeMatchData(language: Language): Promise<EeMatchData> {
  const [rows, programmes, variants] = await Promise.all([nextRules(), listProgrammes("EE"), getEeVariants()]);
  // Последний учебный год, если их несколько.
  const year = rows.reduce<string | null>((latest, row) => (latest === null || row.academic_year > latest ? row.academic_year : latest), null);
  const current = rows.filter((row) => row.academic_year === year);
  const byId = new Map(programmes.map((programme) => [programme.id, programme]));

  const result: EeMatchProgramme[] = [];
  for (const row of current) {
    const rule = parseRule(row.rule);
    const programme = byId.get(row.programme_id);
    if (!programme || rule?.model !== "thresholds") continue;
    result.push({
      id: programme.id,
      slug: programme.slug,
      name: localizedName(programme, language),
      universitySlug: programme.university.slug,
      universityName: localizedName(programme.university, language),
      city: programme.city,
      rule,
      newCurriculum: row.new_curriculum,
      variant: variants[programme.id] ?? null,
    });
  }
  const first = current[0];
  return {
    programmes: result,
    academicYear: year,
    decidedOn: first?.decided_on ?? null,
    sourceUrl: first?.source_url ?? null,
    sourceTitle: first?.source_title ?? null,
  };
}
