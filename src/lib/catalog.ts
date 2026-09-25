import { cache } from "react";
import { supabase } from "@/lib/supabase";
import { fieldCodesForInterests, type InterestKey } from "@/lib/fields";

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
  duration_years: number | null;
  accreditation_valid_until: string | null;
  description_lv: string | null;
  description_en: string | null;
  source_url: string | null;
  verified_at: string | null;
};

// Без description_lv/description_en: ни список каталога, ни карточка
// избранного их не показывают (только сама страница программы, через
// getProgramme ниже) — на 899 строках каталога это была самая тяжёлая
// пара колонок в запросе без всякой пользы (ревью performance-tester,
// 2026-09-24). CATALOG_LIST_COLUMNS ниже — та же мысль на уровне SQL.
export type ProgrammeWithUniversity = Omit<Programme, "description_lv" | "description_en"> & {
  university: Pick<University, "slug" | "name_lv" | "name_en" | "city">;
};

const CATALOG_LIST_COLUMNS =
  "id, university_id, slug, name_lv, name_en, degree_level, language_of_instruction, study_mode, " +
  "city, funding_type, tuition_fee_amount, tuition_fee_currency, budget_places, duration_years, " +
  "accreditation_valid_until, source_url, verified_at";

// Переехали в names.ts (без обращения к базе — тестируются отдельно);
// реэкспорт, чтобы существующие импорты из "@/lib/catalog" не менялись.
export { localizedName, enumLabel } from "@/lib/names";

/** Сколько программ в каталоге всего — для бейджа в шапке страницы. */
export const getProgrammeCount = cache(async (): Promise<number> => {
  const { count, error } = await supabase.from("programme").select("id", { count: "exact", head: true });
  if (error) throw error;
  return count ?? 0;
});

export type ProgrammeFilters = {
  interests?: InterestKey[];
  budgetOnly?: boolean;
  cities?: string[];
  language?: string;
  mode?: string;
  university?: string;
};

// Единственный список городов каталога — раньше дублировался в
// SurveyWizard.tsx, из-за чего Rēzekne один раз добавили только в одном
// месте. Здесь и в форме анкеты, и в фильтре на /programmes.
export const CITY_KEYS = ["riga", "daugavpils", "valmiera", "ventspils", "jelgava", "liepaja", "rezekne", "jurmala", "gulbene", "malnava"];

export const listProgrammes = cache(
  async (filters: ProgrammeFilters = {}): Promise<ProgrammeWithUniversity[]> => {
    // university!inner — нужен, чтобы можно было фильтровать по
    // university.slug ниже (PostgREST требует inner-join для фильтрации
    // встроенного ресурса). У программы university_id обязателен, так что
    // на набор результатов без фильтра по вузу это не влияет.
    // Фильтр по интересам (пункт 16 ревью) идёт через направление
    // программы. programme_field!inner — только когда фильтр задан, иначе
    // программы без разметки выпали бы из обычного каталога. Неподтверждённая
    // разметка здесь допустима: это подсказка для поиска, а не факт, на
    // который человек опирается (блок с доходами требует verified_at).
    const interestCodes =
      filters.interests && filters.interests.length > 0 ? fieldCodesForInterests(filters.interests) : null;
    let query = supabase
      .from("programme")
      .select(
        interestCodes
          ? `${CATALOG_LIST_COLUMNS}, university!inner(slug, name_lv, name_en, city), programme_field!inner(field_code)`
          : `${CATALOG_LIST_COLUMNS}, university!inner(slug, name_lv, name_en, city)`,
      );

    if (interestCodes) {
      query = query.in("programme_field.field_code", interestCodes);
    }
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
    if (filters.university) {
      query = query.eq("university.slug", filters.university);
    }

    const { data, error } = await query.order("degree_level").order("name_en");

    if (error) throw error;
    // Через unknown: строка select собирается условно, и разборщик типов
    // supabase-js не может вывести форму строки из неё.
    return data as unknown as ProgrammeWithUniversity[];
  },
);

// Не обёрнута в cache() — та предназначена для дедупликации запросов внутри
// одного серверного рендера (React Server Components), а этот вызов идёт
// с клиента (страница /favorites читает список из localStorage браузера).
export async function getProgrammesByIds(ids: string[]): Promise<ProgrammeWithUniversity[]> {
  if (ids.length === 0) return [];

  const { data, error } = await supabase
    .from("programme")
    .select(`${CATALOG_LIST_COLUMNS}, university!inner(slug, name_lv, name_en, city)`)
    .in("id", ids);

  if (error) throw error;
  return data as unknown as ProgrammeWithUniversity[];
}

export const listUniversities = cache(
  async (): Promise<Pick<University, "slug" | "name_lv" | "name_en">[]> => {
    const { data, error } = await supabase
      .from("university")
      .select("slug, name_lv, name_en")
      .order("name_en");

    if (error) throw error;
    return data;
  },
);

export const getProgramme = cache(
  async (
    universitySlug: string,
    programmeSlug: string,
  ): Promise<(Programme & { university: University }) | null> => {
    // Один запрос вместо двух последовательных (вуз, потом программа) —
    // это самая приоритетная для роста страница (правило 4 CLAUDE.md:
    // весь канал роста — поиск, и приходят сразу на карточку), лишний
    // круг до Supabase на каждый визит был чистой потерей (ревью
    // performance-tester, 2026-09-24). university!inner — тот же приём,
    // что и в listProgrammes, чтобы фильтровать по university.slug.
    const { data, error } = await supabase
      .from("programme")
      .select("*, university!inner(*)")
      .eq("university.slug", universitySlug)
      .eq("slug", programmeSlug)
      .maybeSingle();

    if (error) throw error;
    if (!data) return null;

    return data as unknown as Programme & { university: University };
  },
);
