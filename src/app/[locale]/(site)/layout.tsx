import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";

// Светлая оболочка: каталог, программа, калькулятор, анкета, избранное.
export default async function SiteLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);

  return (
    <>
      <SiteHeader locale={locale} dict={dict} tone="light" />
      {children}
      <SiteFooter locale={locale} dict={dict} tone="light" />
    </>
  );
}
