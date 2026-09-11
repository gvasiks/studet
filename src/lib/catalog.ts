import { cache } from "react";
import { supabase } from "@/lib/supabase";
import type { Locale } from "@/i18n/config";

export type University = {
  id: string;
  slug: string;
  name_lv: string;
  name_en: string | null;
  kind: string;
  city: string;
  website_url: string | null;
  source_url: string | null;
  verified_at: string | null;
};

export type Programme = {
  id: string;
  university_id: string;
  slug: string;
  name_lv: string | null;
  name_en: string | null;
  degree_level: string;
  language_of_instruction: string;
  study_mode: string;
  city: string | null;
  funding_type: string;
  tuition_fee_amount: number | null;
  tuition_fee_currency: string;
  budget_places: number | null;
  application_deadline: string | null;
  duration_years: number | null;
  accreditation_valid_until: string | null;
  description_lv: string | null;
  description_en: string | null;
  source_url: string | null;
  verified_at: string | null;
};

export type ProgrammeWithUniversity = Programme & {
  university: Pick<University, "slug" | "name_lv" | "name_en" | "city">;
};

// Латышское название приоритетнее (аудитория А — основная), но пока конвейер
// читает только английский раздел сайтов, поэтому падаем на то, что есть.
export function localizedName(
  entity: { name_lv: string | null; name_en: string | null },
  locale: Locale,
): string {
  const primary = locale === "lv" ? entity.name_lv : entity.name_en;
  return primary ?? entity.name_en ?? entity.name_lv ?? "";
}

export function enumLabel(map: Record<string, string>, key: string): string {
  return map[key] ?? key;
}

export type ProgrammeFilters = {
  budgetOnly?: boolean;
  cities?: string[];
  language?: string;
  mode?: string;
};

export const listProgrammes = cache(
  async (filters: ProgrammeFilters = {}): Promise<ProgrammeWithUniversity[]> => {
    let query = supabase.from("programme").select("*, university(slug, name_lv, name_en, city)");

    if (filters.budgetOnly) {
      query = query.in("funding_type", ["budget", "both"]);
    }
    // Фильтр смотрит только на programme.city, не на university.city — пока
    // у всех наших записей город указан явно на уровне программы, этого
    // достаточно. Если появятся программы без своего city, нужно будет
    // учитывать город вуза как запасной вариант.
    if (filters.cities && filters.cities.length > 0) {
      query = query.in("city", filters.cities);
    }
    if (filters.language) {
      query = query.eq("language_of_instruction", filters.language);
    }
    if (filters.mode) {
      query = query.eq("study_mode", filters.mode);
    }

    const { data, error } = await query.order("degree_level").order("name_en");

    if (error) throw error;
    return data as ProgrammeWithUniversity[];
  },
);

export const getProgramme = cache(
  async (
    universitySlug: string,
    programmeSlug: string,
  ): Promise<(Programme & { university: University }) | null> => {
    const { data: university, error: universityError } = await supabase
      .from("university")
      .select("*")
      .eq("slug", universitySlug)
      .maybeSingle();

    if (universityError) throw universityError;
    if (!university) return null;

    const { data: programme, error: programmeError } = await supabase
      .from("programme")
      .select("*")
      .eq("university_id", university.id)
      .eq("slug", programmeSlug)
      .maybeSingle();

    if (programmeError) throw programmeError;
    if (!programme) return null;

    return { ...programme, university };
  },
);
