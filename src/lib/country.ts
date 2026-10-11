import { countryOf, languageOf, type ContentLanguage, type Country, type Language, type Locale } from "@/i18n/config";

// Всё, чем каталог одной страны отличается от другой, кроме самих данных:
// какие разделы сайта для неё готовы и какие значения стоят в фильтрах.
// Тексты — в словарях; здесь только ключи.

// Раздел сайта, которого у страны может ещё не быть. Каталог, карточка
// программы и главная есть у всех.
export type Feature =
  | "favorites"
  | "survey"
  | "match"
  | "calculator"
  | "glossary"
  | "rights"
  | "privacy"
  | "verification";

// Фильтр каталога, для которого у страны может не быть данных. Город,
// язык, вуз и длительность есть у всех. Формы обучения нет у Эстонии:
// государственный портал её не сообщает.
export type CatalogFilter = "interest" | "fee" | "budget" | "mode";

// Экран анкеты. На одном экране бывает два близких вопроса: уровень и
// длительность, бюджет и плата, язык и форма обучения.
export type SurveyStep = "exams" | "interests" | "levelDuration" | "fundingFee" | "city" | "languageMode" | "kind";

type CountryProfile = {
  features: readonly Feature[];
  /** Фильтры каталога, под которые у страны есть данные. */
  filters: readonly CatalogFilter[];
  /**
   * Экраны анкеты в порядке показа. Вопроса, ответ на который каталог этой
   * страны применить не может, в списке быть не должно (проверяется тестом).
   */
  surveySteps: readonly SurveyStep[];
  /** Вкладки уровня в каталоге, в порядке показа. */
  levels: readonly LevelKey[];
  /** Города в фильтре; ключи — как в programme.city и в словаре catalog.city. */
  cities: readonly string[];
  /** Языки обучения в фильтре. */
  languages: readonly string[];
  /** Язык, на котором источники страны публикуют названия программ. */
  nativeLanguage: ContentLanguage;
  /**
   * Общий приём страны: все программы каталога взяты из его списка и
   * подаются через одну систему. url — куда вести человека, sourceUrl —
   * список программ, из которого это следует. null — канал у каждого вуза
   * свой и хранится в таблице application_channel.
   */
  generalAdmission: { url: string; sourceUrl: string } | null;
};

// Все уровни, которые вообще бывают в programme.degree_level. "integrated" —
// литовские цельные программы (vientisosios studijos): поступают после
// школы, заканчивают со степенью магистра.
export const LEVEL_KEYS = ["bachelor", "master", "doctoral", "college", "integrated"] as const;
export type LevelKey = (typeof LEVEL_KEYS)[number];

const profiles: Record<Country, CountryProfile> = {
  LV: {
    features: ["favorites", "survey", "match", "calculator", "glossary", "rights", "privacy", "verification"],
    filters: ["interest", "fee", "budget", "mode"],
    surveySteps: ["exams", "interests", "levelDuration", "fundingFee", "city", "languageMode", "kind"],
    levels: ["bachelor", "master", "doctoral", "college"],
    cities: ["riga", "daugavpils", "valmiera", "ventspils", "jelgava", "liepaja", "rezekne", "jurmala", "gulbene", "malnava"],
    languages: ["lv", "en"],
    nativeLanguage: "lv",
    generalAdmission: null,
  },
  // Литва: каталог, карточка, список избранного, расчёт балла, «куда я
  // прохожу» (фаза 3), анкета (фаза 4), словарь, права и политика
  // конфиденциальности (фаза 5, 2026-10-08) — на всех трёх языках.
  // Фильтров по плате и «только бюджет» нет: источник не сообщает ни цену,
  // ни вид финансирования программы (бюджетные места в Литве делятся по
  // направлениям, а не по программам). Интересы работают по направлению
  // программы из списка общего приёма (src/lib/lt-fields.ts).
  LT: {
    features: ["favorites", "survey", "match", "calculator", "glossary", "rights", "privacy"],
    filters: ["interest", "mode"],
    // Без экзаменов (вопрос ни на что не влияет, а оценки вводятся в «куда
    // я прохожу») и без бюджета с платой (данных нет).
    surveySteps: ["interests", "levelDuration", "city", "languageMode", "kind"],
    levels: ["bachelor", "college", "integrated"],
    cities: ["vilnius", "kaunas", "klaipeda", "siauliai", "panevezys", "utena", "alytus", "telsiai", "marijampole", "taurage"],
    languages: ["lt", "en", "ru"],
    nativeLanguage: "lt",
    // Ссылка на систему подачи у LAMA BPO привязана к году (…/bp2026/…),
    // поэтому ведём на постоянную страницу о поступлении: вход в систему и
    // порядок подачи — на ней.
    generalAdmission: {
      url: "https://lamabpo.lt/pirmosios-pakopos-ir-vientisosios-studijos/",
      sourceUrl: "https://lamabpo.lt/pirmosios-pakopos-ir-vientisosios-studijos/programu-sarasas/",
    },
  },
  // Эстония (с 2026-10-11, docs/PLAN-ESTONIA.md): пока каталог, карточка
  // программы и список сохранённых. Данные — список программ
  // государственного портала haridusportaal.edu.ee: в нём нет формы
  // обучения, цены и вида финансирования, поэтому таких фильтров нет.
  // Интересы работают по направлению программы с того же портала
  // (ISCED-F, src/lib/ee-fields.ts). Анкеты, расчёта балла, словаря и прав
  // пока нет.
  EE: {
    features: ["favorites"],
    filters: ["interest"],
    surveySteps: [],
    levels: ["bachelor", "master", "doctoral", "college", "integrated"],
    // Город — из адреса учреждения: у вузов с филиалами это город головного
    // здания (см. сборщик). Реола, Мыдрику и Вяймела — посёлки, где стоят
    // лётная академия и две прикладные высшие школы.
    cities: ["tallinn", "tartu", "reola", "modriku", "vaimela"],
    languages: ["et", "en", "ru"],
    nativeLanguage: "et",
    // Заявления в Эстонии подаются через государственную систему SAIS, но
    // что так у всех учреждений каталога, не проверено — блок «где подать»
    // появится вместе со сроками приёма (фаза 6).
    generalAdmission: null,
  },
};

export function countryProfile(country: Country): CountryProfile {
  return profiles[country];
}

// Фильтры каталога, когда в одном списке программы нескольких стран.
// - Фильтр «по данным» (интересы, плата, только бюджет) остаётся, только если
//   данные есть у КАЖДОЙ выбранной страны: «только бюджет» по списку двух
//   стран молча убрал бы все литовские программы, у которых вид
//   финансирования не известен вовсе.
// - Уровни и языки — объединение; города остаются по странам, чтобы в форме
//   их можно было подписать.
export type CatalogProfile = {
  filters: CatalogFilter[];
  levels: LevelKey[];
  languages: string[];
  citiesByCountry: { country: Country; cities: readonly string[] }[];
};

export function catalogProfile(shown: readonly Country[]): CatalogProfile {
  const list = shown.map((country) => profiles[country]);
  const allFilters: CatalogFilter[] = ["interest", "fee", "budget", "mode"];
  return {
    filters: allFilters.filter((filter) => list.every((profile) => profile.filters.includes(filter))),
    levels: LEVEL_KEYS.filter((level) => list.some((profile) => profile.levels.includes(level))),
    languages: [...new Set(list.flatMap((profile) => profile.languages))],
    citiesByCountry: shown.map((country) => ({ country, cities: profiles[country].cities })),
  };
}

// Анкета — для выпускников школ: магистратура и докторантура им недоступны.
export function schoolLeaverLevels(country: Country): LevelKey[] {
  return profiles[country].levels.filter((level) => level !== "master" && level !== "doctoral");
}

// Разделы из длинных текстов могут быть написаны не на всех языках: тогда
// язык здесь перечисляется явно, а под остальными адресами раздел закрыт.
// Латвийские словарь, права и политика конфиденциальности переведены на
// все три языка (литовский перевод — 2026-10-06, lt-lv.json), поэтому их
// здесь нет. Страница проверки — внутренний инструмент на латышском.
// Раздел, которого здесь нет, доступен на всех языках.
const writtenIn: Record<Country, Partial<Record<Feature, readonly Language[]>>> = {
  LV: {
    verification: ["lv", "en"],
  },
  LT: {},
  EE: {},
};

// Раздел открыт под адресом, если он готов у страны и написан на языке
// адреса. Иначе его страница отдаёт 404, а ссылка убирается из меню.
export function hasFeature(locale: Locale, feature: Feature): boolean {
  const country = countryOf(locale);
  if (!profiles[country].features.includes(feature)) return false;
  const languages = writtenIn[country][feature];
  return languages === undefined || languages.includes(languageOf(locale));
}
