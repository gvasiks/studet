import Link from "next/link";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { GraduationCapIcon } from "@/components/icons";
import { FavoritesLink, HeaderNav } from "@/components/HeaderNav";
import { LocaleSwitcher, type Tone } from "@/components/LocaleSwitcher";
import { SITE_NAME } from "@/lib/site";

// Два варианта из макетов: светлая липкая шапка на страницах сайта и
// прозрачная поверх тёмной сцены на главной.
export function SiteHeader({ locale, dict, tone }: { locale: Locale; dict: Dictionary; tone: Tone }) {
  const dark = tone === "dark";

  return (
    <>
      <header
        className={
          dark ? "relative z-30" : "sticky top-0 z-30 border-b border-black/5 bg-white/85 backdrop-blur"
        }
      >
        <div className="page-container flex min-h-[72px] items-center gap-x-3 lg:gap-x-6">
          <Link href={`/${locale}`} className="flex items-center gap-2.5" aria-label={SITE_NAME}>
            <span className="grid h-8 w-8 place-items-center rounded-[10px] bg-brand text-white">
              <GraduationCapIcon size={18} />
            </span>
            <span className={`text-lg font-bold tracking-tight ${dark ? "text-white" : "text-zinc-900"}`}>{SITE_NAME}</span>
          </Link>
          {/* от lg — строка пунктов рядом с логотипом; уже — кнопка «Izvēlne»
              в самом конце строки, после переключателя языка */}
          <HeaderNav
            locale={locale}
            tone={tone}
            className="order-last lg:order-none"
            labels={{
              catalog: dict.nav.catalog,
              survey: dict.nav.survey,
              match: dict.nav.match,
              favorites: dict.favorites.navLink,
              glossary: dict.nav.glossary,
              rights: dict.nav.rights,
              menu: dict.nav.menu,
              main: dict.nav.main,
            }}
          />
          <div className="ml-auto flex items-center gap-3">
            {dark && <FavoritesLink locale={locale} label={dict.favorites.navLink} />}
            <LocaleSwitcher locale={locale} tone={tone} />
          </div>
        </div>
      </header>
      {/* План 2026-09-21, пункт 14: аудитория Б (иностранные абитуриенты)
          пока не обслуживается — сайт честно говорит об этом на английских
          страницах, а не молчит. Индексацию не закрываем (само по себе это
          не причина для noindex), просто не выдаём каталог и калькулятор за
          нечто большее, чем они есть сегодня. */}
      {locale === "en" && (
        <div
          role="region"
          aria-label="Coverage notice"
          className={dark ? "relative z-20 bg-amber-400/95" : "bg-amber-50"}
        >
          <p
            className={`page-container py-2 text-center text-xs leading-relaxed ${
              dark ? "text-amber-950" : "text-amber-900"
            }`}
          >
            {dict.coverage.notice}
          </p>
        </div>
      )}
    </>
  );
}
