import type { Country, Language } from "@/i18n/config";

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

type CountryProfile = {
  features: readonly Feature[];
  /** Вкладки уровня в каталоге, в порядке показа. */
  levels: readonly LevelKey[];
  /** Города в фильтре; ключи — как в programme.city и в словаре catalog.city. */
  cities: readonly string[];
  /** Языки обучения в фильтре. */
  languages: readonly string[];
  /** Язык, на котором источники страны публикуют названия программ. */
  nativeLanguage: Language;
};

// Все уровни, которые вообще бывают в programme.degree_level. "integrated" —
// литовские цельные программы (vientisosios studijos): поступают после
// школы, заканчивают со степенью магистра.
export const LEVEL_KEYS = ["bachelor", "master", "doctoral", "college", "integrated"] as const;
export type LevelKey = (typeof LEVEL_KEYS)[number];

const profiles: Record<Country, CountryProfile> = {
  LV: {
    features: ["favorites", "survey", "match", "calculator", "glossary", "rights", "privacy", "verification"],
    levels: ["bachelor", "master", "doctoral", "college"],
    cities: ["riga", "daugavpils", "valmiera", "ventspils", "jelgava", "liepaja", "rezekne", "jurmala", "gulbene", "malnava"],
    languages: ["lv", "en"],
    nativeLanguage: "lv",
  },
  // Литва, фаза 2: только каталог, карточка и список избранного. Остальные
  // разделы включаются по мере готовности (docs/PLAN-LITHUANIA-2027.md):
  // расчёт балла — фаза 3, анкета — фаза 4, словарь, права и политика
  // конфиденциальности — фаза 5.
  LT: {
    features: ["favorites"],
    levels: ["bachelor", "college", "integrated"],
    cities: ["vilnius", "kaunas", "klaipeda", "siauliai", "panevezys", "utena", "alytus", "telsiai", "marijampole", "taurage"],
    languages: ["lt", "en", "ru"],
    nativeLanguage: "lt",
  },
};

export function countryProfile(country: Country): CountryProfile {
  return profiles[country];
}

export function hasFeature(country: Country, feature: Feature): boolean {
  return profiles[country].features.includes(feature);
}
