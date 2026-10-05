import { languageOf, type Language, type Locale } from "@/i18n/config";
import { mergeDictionary } from "@/i18n/merge";
import type lv from "@/i18n/dictionaries/lv.json";

export type Dictionary = typeof lv;

// Словарь выбирается по языку, а не по сегменту адреса. Латышский и
// литовский словари написаны каждый для своей страны; английский —
// общий, и у стран, кроме Латвии, поверх него накладывается файл отличий.
const dictionaries: Record<Language, () => Promise<Dictionary>> = {
  lv: () => import("@/i18n/dictionaries/lv.json").then((module) => module.default),
  en: () => import("@/i18n/dictionaries/en.json").then((module) => module.default),
  lt: () => import("@/i18n/dictionaries/lt.json").then((module) => module.default),
};

// Только строки, которые в этой стране звучат иначе (название сайта,
// что именно покрыто, тексты о праве). Всё остальное берётся из en.json.
const overrides: Partial<Record<Locale, () => Promise<unknown>>> = {
  "en-lt": () => import("@/i18n/dictionaries/en-lt.json").then((module) => module.default),
};

export async function getDictionary(locale: Locale): Promise<Dictionary> {
  const base = await dictionaries[languageOf(locale)]();
  const override = overrides[locale];
  return override ? mergeDictionary(base, await override()) : base;
}
