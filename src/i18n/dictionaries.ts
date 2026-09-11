import type { Locale } from "@/i18n/config";
import type lv from "@/i18n/dictionaries/lv.json";

export type Dictionary = typeof lv;

const dictionaries: Record<Locale, () => Promise<Dictionary>> = {
  lv: () => import("@/i18n/dictionaries/lv.json").then((module) => module.default),
  en: () => import("@/i18n/dictionaries/en.json").then((module) => module.default),
};

export async function getDictionary(locale: Locale): Promise<Dictionary> {
  return dictionaries[locale]();
}
