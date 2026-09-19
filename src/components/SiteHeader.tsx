import Link from "next/link";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { GraduationCapIcon } from "@/components/icons";
import { FavoritesLink, HeaderNav } from "@/components/HeaderNav";
import { LocaleSwitcher, type Tone } from "@/components/LocaleSwitcher";

// Два варианта из макетов: светлая липкая шапка на страницах сайта и
// прозрачная поверх тёмной сцены на главной.
export function SiteHeader({ locale, dict, tone }: { locale: Locale; dict: Dictionary; tone: Tone }) {
  const dark = tone === "dark";

  return (
    <header
      className={
        dark ? "relative z-20" : "sticky top-0 z-30 border-b border-black/5 bg-white/85 backdrop-blur"
      }
    >
      <div className="page-container flex min-h-[72px] flex-wrap items-center gap-x-6 gap-y-2 py-3 sm:py-0">
        <Link href={`/${locale}`} className="flex items-center gap-2.5" aria-label="Studet">
          <span className="grid h-8 w-8 place-items-center rounded-[10px] bg-brand text-white">
            <GraduationCapIcon size={18} />
          </span>
          <span className={`text-lg font-bold tracking-tight ${dark ? "text-white" : "text-zinc-900"}`}>Studet</span>
        </Link>
        {/* на телефоне навигация уходит во вторую строку, на широком — рядом с логотипом */}
        <HeaderNav
          locale={locale}
          tone={tone}
          className="order-last w-full overflow-x-auto sm:order-none sm:w-auto"
          labels={{
            catalog: dict.nav.catalog,
            survey: dict.nav.survey,
            favorites: dict.favorites.navLink,
            main: dict.nav.main,
          }}
        />
        <div className="ml-auto flex items-center gap-3">
          {dark && <FavoritesLink locale={locale} label={dict.favorites.navLink} />}
          <LocaleSwitcher locale={locale} tone={tone} />
        </div>
      </div>
    </header>
  );
}
