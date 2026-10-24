import { cache } from "react";
import type { Country } from "@/i18n/config";
import { supabase } from "@/lib/supabase";
import { filterProgrammes } from "@/lib/catalog-filter";
import { fieldCodesForInterests, type InterestKey } from "@/lib/fields";
import { ltFieldCodesForInterests } from "@/lib/lt-fields";
import { eeInterestOf } from "@/lib/ee-fields";
import { remember } from "@/lib/server-memo";

export type University = {
  id: string;
  slug: string;
  // Название на языке страны: name_lv у латвийских, name_lt у литовских,
  // name_et у эстонских.
  name_lv: string | null;
  name_lt: string | null;
  name_et: string | null;
  name_en: string | null;
  kind: string;
  city: string;
  // ISO 3166-1 alpha-2. В общем списке двух стран по ней карточка узнаёт, в
  // каком разделе сайта лежит страница программы.
  country: Country;
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
  name_et: string | null;
  name_en: string | null;
  degree_level: string;
  language_of_instruction: string;
  // null — источник не сообщает (эстонские программы: формы обучения нет в
  // данных государственного портала).
  study_mode: string | null;
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
  description_et: string | null;
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
  // С государственного портала Эстонии (pipeline/src/sources/ee_haridusportaal.py).
  degree_awarded_et: string | null;
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
export type ProgrammeWithUniversity = Omit<
  Programme,
  "description_lv" | "description_lt" | "description_et" | "description_en"
> & {
  university: Pick<University, "slug" | "name_lv" | "name_lt" | "name_et" | "name_en" | "kind" | "city" | "country">;
};

const CATALOG_LIST_COLUMNS =
  "id, university_id, slug, name_lv, name_lt, name_et, name_en, degree_level, language_of_instruction, study_mode, " +
  "city, funding_type, tuition_fee_amount, tuition_fee_currency, budget_places, duration_years, " +
  "accreditation_valid_until, source_url, verified_at";

// Колонки карточки программы и вуза — перечислены явно, не «*»: служебные
// колонки (verified_by и др.) публичному ключу закрыты (миграция
// 20261024120000_hide_service_columns.sql), и «*» получил бы ошибку прав.
// Новая колонка в типе Programme/University должна появиться и здесь.
const PROGRAMME_PAGE_COLUMNS =
  CATALOG_LIST_COLUMNS +
  ", description_lv, description_lt, description_et, description_en, degree_awarded_lv, degree_awarded_en, " +
  "degree_awarded_lt, degree_awarded_et, qualification_lv, diploma_document_lv, details_source_url, details_extracted_at";
const UNIVERSITY_COLUMNS = "id, slug, name_lv, name_lt, name_et, name_en, kind, city, country, website_url, source_url, verified_at";

// kind — для фильтра «государственный или частный»: он применяется к списку
// в памяти, а не в запросе.
const UNIVERSITY_LIST_COLUMNS = "slug, name_lv, name_lt, name_et, name_en, kind, city, country";

// Сколько список программ, вузов и направлений живёт в памяти сервера
// (server-memo.ts). Каталог обновляется сбором раз в неделю, так что пять
// минут задержки после сбора или подтверждения в Studio не заметны, а
// страница перестаёт скачивать весь список на каждый щелчок по фильтру.
const CATALOG_MEMORY_MS = 5 * 60 * 1000;

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
export async function getProgrammeCount(country: Country): Promise<number> {
  return (await allProgrammes(country)).length;
}

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

// Весь каталог страны одним списком — из памяти сервера. Фильтров в запросе
// нет: все они применяются потом к готовому списку (catalog-filter.ts).
// До 2026-10-11 список с фильтрами запрашивался у базы при каждом показе
// каталога — полтора мегабайта на две страны ради двенадцати карточек.
// university!inner — чтобы отобрать по стране вуза.
function allProgrammes(country: Country): Promise<ProgrammeWithUniversity[]> {
  return remember(`programmes:${country}`, CATALOG_MEMORY_MS, async () => {
    const rows: ProgrammeWithUniversity[] = [];
    for (let from = 0; ; from += PAGE_ROWS) {
      // id — последним ключом порядка: без однозначного порядка строка на
      // границе страниц могла бы попасть в обе или ни в одну.
      const { data, error } = await supabase
        .from("programme")
        .select(`${CATALOG_LIST_COLUMNS}, university!inner(${UNIVERSITY_LIST_COLUMNS})`)
        .eq("university.country", country)
        .order("degree_level")
        .order("name_en")
        .order("id")
        .range(from, from + PAGE_ROWS - 1);
      if (error) throw error;
      // Через unknown: разборщик типов supabase-js не выводит форму строки
      // из собранной строки select.
      rows.push(...(data as unknown as ProgrammeWithUniversity[]));
      if (data.length < PAGE_ROWS) break;
    }
    return rows;
  });
}

// Направление каждой программы страны: id программы -> код. Нужно фильтру по
// интересам (пункт 16 ревью). Неподтверждённая разметка здесь допустима: это
// подсказка для поиска, а не факт, на который человек опирается (блок с
// доходами требует verified_at). У Литвы направление лежит в своей таблице и
// со своими кодами (lt_programme_field, классификатор общего приёма) — см.
// lt-fields.ts. Строк около тысячи у каждой страны, поэтому читаем страницами.
// У Эстонии «кодом» служит сама категория интересов: она зависит не только
// от направления, но и от группы программ внутри него (экономика), поэтому
// вычисляется сразу при чтении — см. ee-fields.ts.
function programmeFieldCodes(country: Country): Promise<Map<string, string>> {
  const table = country === "LT" ? "lt_programme_field" : "programme_field";
  return remember(`field-codes:${country}`, CATALOG_MEMORY_MS, async () => {
    const codes = new Map<string, string>();
    if (country === "EE") {
      for (let from = 0; ; from += PAGE_ROWS) {
        const { data, error } = await supabase
          .from("ee_programme_field")
          .select("programme_id, field_code, detailed_name")
          .order("programme_id")
          .range(from, from + PAGE_ROWS - 1);
        if (error) throw error;
        for (const row of data) {
          const interest = eeInterestOf(row.field_code as string, row.detailed_name as string | null);
          if (interest) codes.set(row.programme_id as string, interest);
        }
        if (data.length < PAGE_ROWS) break;
      }
      return codes;
    }
    for (let from = 0; ; from += PAGE_ROWS) {
      const { data, error } = await supabase
        .from(table)
        .select("programme_id, field_code")
        .order("programme_id")
        .range(from, from + PAGE_ROWS - 1);
      if (error) throw error;
      for (const row of data) codes.set(row.programme_id as string, row.field_code as string);
      if (data.length < PAGE_ROWS) break;
    }
    return codes;
  });
}

// Программы страны, подходящие под фильтры. Возвращается новый массив:
// список в памяти общий для всех запросов, менять его нельзя.
export async function listProgrammes(
  country: Country,
  filters: ProgrammeFilters = {},
): Promise<ProgrammeWithUniversity[]> {
  const byInterest = filters.interests !== undefined && filters.interests.length > 0;
  // У Эстонии в памяти уже лежит категория интересов (см. выше).
  const codesFor =
    country === "EE"
      ? (keys: InterestKey[]): string[] => keys
      : country === "LT"
        ? ltFieldCodesForInterests
        : fieldCodesForInterests;
  const [programmes, fieldCodeById] = await Promise.all([
    allProgrammes(country),
    byInterest ? programmeFieldCodes(country) : new Map<string, string>(),
  ]);
  const interestCodes = byInterest ? new Set(codesFor(filters.interests!)) : null;
  return filterProgrammes(programmes, filters, interestCodes, fieldCodeById);
}

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

export type UniversityOption = Pick<University, "slug" | "name_lv" | "name_lt" | "name_et" | "name_en"> & {
  /** Сколько программ вуза видно в каталоге — для списка «Augstskola». */
  programmeCount: number;
};

// Вузы страны с числом программ — для фильтра и главной. Из памяти сервера,
// как и список программ; возвращается копия, чтобы вызывающий мог её
// сортировать.
export async function listUniversities(country: Country): Promise<UniversityOption[]> {
  const universities = await remember(`universities:${country}`, CATALOG_MEMORY_MS, async () => {
    // programme(id) и длина списка — не programme(count): count(*) требует
    // права на всю таблицу, а у публичного ключа с 2026-10-24 право на
    // programme выдано по колонкам (миграция 20261024120000). RLS программы
    // действует и здесь: скрытые программы (missed_runs >= 2) в число не
    // попадают, как и в сам каталог.
    const { data, error } = await supabase
      .from("university")
      .select("slug, name_lv, name_lt, name_et, name_en, programme(id)")
      .eq("country", country)
      .order("name_en");

    if (error) throw error;
    const rows = data as unknown as (Pick<University, "slug" | "name_lv" | "name_lt" | "name_et" | "name_en"> & {
      programme: { id: string }[];
    })[];
    return rows.map(({ programme, ...university }) => ({
      ...university,
      programmeCount: programme.length,
    }));
  });
  return [...universities];
}

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
      .select(`${PROGRAMME_PAGE_COLUMNS}, university!inner(${UNIVERSITY_COLUMNS})`)
      .eq("university.country", country)
      .eq("university.slug", universitySlug)
      .eq("slug", programmeSlug)
      .maybeSingle();

    if (error) throw error;
    if (!data) return null;

    return data as unknown as Programme & { university: University };
  },
);
