import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Inter } from "next/font/google";
import { isLocale, languageOf, locales } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { isSiteClosed, SITE_URL } from "@/lib/site";
import { Analytics } from "@/components/Analytics";
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
    // Закрытая выкладка до запуска: noindex на каждой странице. У страниц со
    // своим robots (избранное, внутренняя проверка) остаётся их значение —
    // оно тоже noindex.
    ...(isSiteClosed() ? { robots: { index: false, follow: false } } : {}),
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
      lang={languageOf(locale)}
      className={`${inter.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        <Providers>{children}</Providers>
        {/* Счётчик посещений: ничего не рисует, считает только на рабочем сайте */}
        <Analytics />
      </body>
    </html>
  );
}
