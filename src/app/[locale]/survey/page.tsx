import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { SurveyWizard } from "./SurveyWizard";

export default async function SurveyPage({ params }: PageProps<"/[locale]/survey">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);

  return <SurveyWizard locale={locale} dict={dict} />;
}
