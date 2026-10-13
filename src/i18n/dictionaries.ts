import { languageOf, type Language, type Locale } from "@/i18n/config";
import { mergeDictionary } from "@/i18n/merge";
import type lv from "@/i18n/dictionaries/lv.json";

export type Dictionary = typeof lv;

// Словарь выбирается по языку, а не по сегменту адреса. Базовый словарь
// каждого языка написан для одной страны: lv.json и en.json — для Латвии,
// lt.json — для Литвы, et.json — для Эстонии. Для другой страны поверх него
// накладывается файл отличий.
//
// В et.json — только короткие тексты интерфейса: у самой Эстонии словаря
// терминов, прав и политики ещё нет (docs/PLAN-ESTONIA.md, фаза 10), а
// латвийские и литовские лежат на эстонском в файлах отличий et-lv.json и
// et-lt.json. Чтобы у словаря была полная форма, под эстонский подложен
// английский: его длинные разделы под эстонским адресом не показываются
// (у Эстонии таких разделов нет, у Латвии и Литвы их целиком заменяет файл
// отличий), а полноту остального проверяет overrides.test.ts.
const dictionaries: Record<Language, () => Promise<Dictionary>> = {
  lv: () => import("@/i18n/dictionaries/lv.json").then((module) => module.default),
  en: () => import("@/i18n/dictionaries/en.json").then((module) => module.default),
  lt: () => import("@/i18n/dictionaries/lt.json").then((module) => module.default),
  et: async () => {
    const [english, estonian] = await Promise.all([
      import("@/i18n/dictionaries/en.json").then((module) => module.default),
      import("@/i18n/dictionaries/et.json").then((module) => module.default),
    ]);
    return mergeDictionary<Dictionary>(english, estonian);
  },
};

// Только строки, которые в этой стране звучат иначе (название сайта,
// что именно покрыто, тексты о праве). Всё остальное берётся из en.json.
const overrides: Partial<Record<Locale, () => Promise<unknown>>> = {
  "en-lt": () => import("@/i18n/dictionaries/en-lt.json").then((module) => module.default),
  "lv-lt": () => import("@/i18n/dictionaries/lv-lt.json").then((module) => module.default),
  "lt-lv": () => import("@/i18n/dictionaries/lt-lv.json").then((module) => module.default),
  "et-lv": () => import("@/i18n/dictionaries/et-lv.json").then((module) => module.default),
  "et-lt": () => import("@/i18n/dictionaries/et-lt.json").then((module) => module.default),
  // Эстония на остальных языках — файл отличий поверх словаря другой страны.
  "en-ee": () => import("@/i18n/dictionaries/en-ee.json").then((module) => module.default),
  "lv-ee": () => import("@/i18n/dictionaries/lv-ee.json").then((module) => module.default),
  "lt-ee": () => import("@/i18n/dictionaries/lt-ee.json").then((module) => module.default),
};

export async function getDictionary(locale: Locale): Promise<Dictionary> {
  const base = await dictionaries[languageOf(locale)]();
  const override = overrides[locale];
  return override ? mergeDictionary(base, await override()) : base;
}
