import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Inter } from "next/font/google";
import { isLocale, locales } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { LocaleSwitcher } from "@/components/LocaleSwitcher";
import { SiteFooter } from "@/components/SiteFooter";
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
  return { title: dict.meta.title };
}

export default async function LocaleLayout({
  children,
  params,
}: LayoutProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);

  return (
    <html
      lang={locale}
      className={`${inter.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        <header className="flex items-center justify-between px-6 py-4">
          <Link href={`/${locale}`} className="text-sm font-semibold tracking-tight text-zinc-900">
            Studet
          </Link>
          <LocaleSwitcher locale={locale} />
        </header>
        <Providers>{children}</Providers>
        <SiteFooter dict={dict} />
      </body>
    </html>
  );
}
