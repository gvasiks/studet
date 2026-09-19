import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Inter } from "next/font/google";
import { isLocale, locales } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { GraduationCapIcon } from "@/components/icons";
import { HeaderNav } from "@/components/HeaderNav";
import { LocaleSwitcher } from "@/components/LocaleSwitcher";
import { SiteFooter } from "@/components/SiteFooter";
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
        <header className="sticky top-0 z-30 border-b border-black/5 bg-white/85 backdrop-blur">
          <div className="page-container flex min-h-[72px] flex-wrap items-center gap-x-6 gap-y-2 py-3 sm:py-0">
            <Link href={`/${locale}`} className="flex items-center gap-2.5" aria-label="Studet">
              <span className="grid h-8 w-8 place-items-center rounded-[10px] bg-brand text-white">
                <GraduationCapIcon size={18} />
              </span>
              <span className="text-lg font-bold tracking-tight text-zinc-900">Studet</span>
            </Link>
            {/* на телефоне навигация уходит во вторую строку, на широком — рядом с логотипом */}
            <HeaderNav
              locale={locale}
              className="order-last w-full overflow-x-auto sm:order-none sm:w-auto"
              labels={{
                catalog: dict.nav.catalog,
                survey: dict.nav.survey,
                favorites: dict.favorites.navLink,
                main: dict.nav.main,
              }}
            />
            <div className="ml-auto">
              <LocaleSwitcher locale={locale} />
            </div>
          </div>
        </header>
        <Providers>{children}</Providers>
        <SiteFooter dict={dict} />
      </body>
    </html>
  );
}
