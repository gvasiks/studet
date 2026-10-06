import { cache } from "react";
import type { Country } from "@/i18n/config";
import { supabase } from "@/lib/supabase";
import { fieldCodesForInterests, type InterestKey } from "@/lib/fields";
import { ltFieldCodesForInterests } from "@/lib/lt-fields";

export type University = {
  id: string;
  slug: string;
  // Название на языке страны: name_lv у латвийских, name_lt у литовских.
  name_lv: string | null;
  name_lt: string | null;
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
  name_lt: string | null;
  name_en: string | null;
  degree_level: string;
  language_of_instruction: string;
  study_mode: string;
  city: string | null;
  // null — источник не сообщает (литовские программы: бюджетные места
  // делятся по направлениям, не по программам).
  funding_type: string | null;
  tuition_fee_amount: number | null;
  tuition_fee_currency: string;
  budget_places: number | null;
  duration_years: number | null;
  accreditation_valid_until: string | null;
  description_lv: string | null;
  description_lt: string | null;
  description_en: string | null;
  source_url: string | null;
  verified_at: string | null;
  // Со страницы программы в NIID.lv (pipeline/src/enrich_niid_details.py).
  // Официальные латышские названия — без английской пары. Заполнены только
  // у программ, чей источник — NIID; у остальных null.
  degree_awarded_lv: string | null;
  // С английской страницы программы на lu.lv (enrich_lu_details.py).
  degree_awarded_en: string | null;
  // Из карточки государственного реестра Литвы (pipeline/src/sources/lt_lamabpo.py).
  degree_awarded_lt: string | null;
  qualification_lv: string | null;
  diploma_document_lv: string | null;
  details_source_url: string | null;
  details_extracted_at: string | null;
};

// Без description_lv/description_en: ни список каталога, ни карточка
// избранного их не показывают (только сама страница программы, через
// getProgramme ниже) — на 899 строках каталога это была самая тяжёлая
// пара колонок в запросе без всякой пользы (ревью performance-tester,
// 2026-09-24). CATALOG_LIST_COLUMNS ниже — та же мысль на уровне SQL.
export type ProgrammeWithUniversity = Omit<Programme, "description_lv" | "description_lt" | "description_en"> & {
  university: Pick<University, "slug" | "name_lv" | "name_lt" | "name_en" | "city">;
};

const CATALOG_LIST_COLUMNS =
  "id, university_id, slug, name_lv, name_lt, name_en, degree_level, language_of_instruction, study_mode, " +
  "city, funding_type, tuition_fee_amount, tuition_fee_currency, budget_places, duration_years, " +
  "accreditation_valid_until, source_url, verified_at";

const UNIVERSITY_LIST_COLUMNS = "slug, name_lv, name_lt, name_en, city";

// PostgREST отдаёт не больше 1000 строк за запрос и не сообщает, что
// остальное отрезано. В литовском каталоге строк больше тысячи, поэтому
// список читается страницами.
const PAGE_ROWS = 1000;

// Переехали в names.ts (без обращения к базе — тестируются отдельно);
// реэкспорт, чтобы существующие импорты из "@/lib/catalog" не менялись.
export { localizedName, enumLabel } from "@/lib/names";

// Каждая функция ниже принимает страну первым параметром — обязательным,
// чтобы новый запрос нельзя было написать «на все страны» по забывчивости.
// Страна хранится у вуза (university.country), страница берёт её из адреса:
// countryOf(locale), см. src/i18n/config.ts.

/** Сколько программ в каталоге страны — для бейджа в шапке страницы. */
export const getProgrammeCount = cache(async (country: Country): Promise<number> => {
  const { count, error } = await supabase
    .from("programme")
    .select("id, university!inner(country)", { count: "exact", head: true })
    .eq("university.country", country);
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
  /** university.kind: 'public' | 'private' */
  kind?: string;
};

// Список городов каталога — в профиле страны (src/lib/country.ts): один
// на форму анкеты и на фильтр /programmes.

export const listProgrammes = cache(
  async (country: Country, filters: ProgrammeFilters = {}): Promise<ProgrammeWithUniversity[]> => {
    // university!inner — нужен, чтобы можно было фильтровать по
    // university.slug ниже (PostgREST требует inner-join для фильтрации
    // встроенного ресурса). У программы university_id обязателен, так что
    // на набор результатов без фильтра по вузу это не влияет.
    // Фильтр по интересам (пункт 16 ревью) идёт через направление
    // программы. programme_field!inner — только когда фильтр задан, иначе
    // программы без разметки выпали бы из обычного каталога. Неподтверждённая
    // разметка здесь допустима: это подсказка для поиска, а не факт, на
    // который человек опирается (блок с доходами требует verified_at).
    // У Литвы направление лежит в своей таблице и со своими кодами
    // (lt_programme_field, классификатор общего приёма) — см. lt-fields.ts.
    const fieldTable = country === "LT" ? "lt_programme_field" : "programme_field";
    const codesFor = country === "LT" ? ltFieldCodesForInterests : fieldCodesForInterests;
    const interestCodes = filters.interests && filters.interests.length > 0 ? codesFor(filters.interests) : null;
    // Запрос собирается заново для каждой страницы: один и тот же объект
    // запроса повторно не используется.
    const buildQuery = () => {
      let query = supabase
        .from("programme")
        .select(
          interestCodes
            ? `${CATALOG_LIST_COLUMNS}, university!inner(${UNIVERSITY_LIST_COLUMNS}), ${fieldTable}!inner(field_code)`
            : `${CATALOG_LIST_COLUMNS}, university!inner(${UNIVERSITY_LIST_COLUMNS})`,
        )
        .eq("university.country", country);

      if (interestCodes) {
        query = query.in(`${fieldTable}.field_code`, interestCodes);
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
      // Тот же inner-join, что и для university.slug: фильтр по полю вуза.
      if (filters.kind) {
        query = query.eq("university.kind", filters.kind);
      }

      // id — последним ключом: без однозначного порядка строка на границе
      // страниц могла бы попасть в обе или ни в одну.
      return query.order("degree_level").order("name_en").order("id");
    };

    const rows: ProgrammeWithUniversity[] = [];
    for (let from = 0; ; from += PAGE_ROWS) {
      const { data, error } = await buildQuery().range(from, from + PAGE_ROWS - 1);
      if (error) throw error;
      // Через unknown: строка select собирается условно, и разборщик типов
      // supabase-js не может вывести форму строки из неё.
      rows.push(...(data as unknown as ProgrammeWithUniversity[]));
      if (data.length < PAGE_ROWS) break;
    }
    return rows;
  },
);

// Не обёрнута в cache() — та предназначена для дедупликации запросов внутри
// одного серверного рендера (React Server Components), а этот вызов идёт
// с клиента (страница /favorites читает список из localStorage браузера).
// Список в браузере один на весь сайт, поэтому программы другой страны
// здесь отсеиваются: под этим адресом у них нет страницы.
export async function getProgrammesByIds(country: Country, ids: string[]): Promise<ProgrammeWithUniversity[]> {
  if (ids.length === 0) return [];

  const { data, error } = await supabase
    .from("programme")
    .select(`${CATALOG_LIST_COLUMNS}, university!inner(${UNIVERSITY_LIST_COLUMNS})`)
    .eq("university.country", country)
    .in("id", ids);

  if (error) throw error;
  return data as unknown as ProgrammeWithUniversity[];
}

export type UniversityOption = Pick<University, "slug" | "name_lv" | "name_lt" | "name_en"> & {
  /** Сколько программ вуза видно в каталоге — для списка «Augstskola». */
  programmeCount: number;
};

export const listUniversities = cache(async (country: Country): Promise<UniversityOption[]> => {
  // programme(count) — PostgREST считает встроенные строки сам, одним
  // запросом. RLS программы действует и здесь: скрытые программы
  // (missed_runs >= 2) в число не попадают, как и в сам каталог.
  const { data, error } = await supabase
    .from("university")
    .select("slug, name_lv, name_lt, name_en, programme(count)")
    .eq("country", country)
    .order("name_en");

  if (error) throw error;
  // Через unknown: разборщик типов supabase-js не выводит форму count.
  const rows = data as unknown as (Pick<University, "slug" | "name_lv" | "name_lt" | "name_en"> & {
    programme: { count: number }[];
  })[];
  return rows.map(({ programme, ...university }) => ({
    ...university,
    programmeCount: programme[0]?.count ?? 0,
  }));
});

export const getProgramme = cache(
  async (
    country: Country,
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
      .eq("university.country", country)
      .eq("university.slug", universitySlug)
      .eq("slug", programmeSlug)
      .maybeSingle();

    if (error) throw error;
    if (!data) return null;

    return data as unknown as Programme & { university: University };
  },
);
