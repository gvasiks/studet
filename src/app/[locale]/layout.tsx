import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Inter } from "next/font/google";
import { isLocale, locales } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { SITE_URL } from "@/lib/site";
import { Providers } from "./providers";
import "../globals.css";

// latin-ext обязателен — без него диакритика латышского (ā, š, ž...)
// молча падает на системный шрифт вместо Inter.
const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext"],
});

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: LayoutProps<"/[locale]">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  return {
    metadataBase: new URL(SITE_URL),
    title: { default: dict.meta.title, template: `%s — ${dict.meta.title}` },
  };
}

// Шапка и подвал живут не здесь, а в раскладках групп маршрутов: (site) —
// светлые, для каталога и остальных страниц, (home) — тёмные, часть
// сцены главной. Здесь только то, что общее для всех: <html>, шрифт,
// провайдеры.
export default async function LocaleLayout({
  children,
  params,
}: LayoutProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  return (
    <html
      lang={locale}
      className={`${inter.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
