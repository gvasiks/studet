import Image from "next/image";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import heroBg from "../../../../public/images/hero-bg.webp";

// Тёмная сцена главной: фон, шапка и подвал — одно целое (макет главной),
// поэтому картинка лежит в раскладке, а не на странице.
export default async function HomeLayout({
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
    <div className="relative flex min-h-dvh flex-1 flex-col overflow-hidden bg-slate-950">
      <Image src={heroBg} alt="" fill priority sizes="100vw" className="object-cover" />
      {/* Тёмная подложка слева — гарантирует контраст текста, даже если
          на широком экране светлая (фиолетовая) часть картинки съедет влево. */}
      <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/70 to-transparent" />
      <SiteHeader locale={locale} dict={dict} tone="dark" />
      {children}
      <SiteFooter locale={locale} dict={dict} tone="dark" />
    </div>
  );
}
