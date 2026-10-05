import { languageOf, type Language, type Locale } from "@/i18n/config";
import type lv from "@/i18n/dictionaries/lv.json";

export type Dictionary = typeof lv;

// Словарь выбирается по языку, а не по сегменту адреса: у /en-lv и будущего
// /en-lt один английский словарь.
const dictionaries: Record<Language, () => Promise<Dictionary>> = {
  lv: () => import("@/i18n/dictionaries/lv.json").then((module) => module.default),
  en: () => import("@/i18n/dictionaries/en.json").then((module) => module.default),
};

export async function getDictionary(locale: Locale): Promise<Dictionary> {
  return dictionaries[languageOf(locale)]();
}
