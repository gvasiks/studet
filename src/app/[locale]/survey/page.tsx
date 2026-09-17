import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import { SurveyWizard } from "./SurveyWizard";

export async function generateMetadata({ params }: PageProps<"/[locale]/survey">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  return {
    title: dict.survey.title,
    description: dict.survey.intro,
    alternates: buildAlternates("/survey", locale),
  };
}

export default async function SurveyPage({ params }: PageProps<"/[locale]/survey">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);

  return <SurveyWizard locale={locale} dict={dict} />;
}
