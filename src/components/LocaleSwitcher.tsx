"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { countryOf, languageOf, languages, localesOfCountry, type Locale } from "@/i18n/config";

export type Tone = "light" | "dark";

// Нужен usePathname(), чтобы при переключении языка остаться на той же
// странице (та же programme/university slug работает под обоими локалями,
// менять нужно только первый сегмент пути). Серверный компонент этого не
// умеет без прокидывания текущего пути через каждую страницу.
//
// Переключает язык интерфейса, страна каталога остаётся той же. Языки
// стоят в одном порядке на всех страницах (languages в config.ts).
// Страна выбирается отдельно, в подвале (CountrySwitcher).
//
// Ссылки, а не кнопки: переключатель языка — это навигация (другой
// адрес, другой индексируемый документ), не действие на странице.
export function LocaleSwitcher({ locale, tone = "light" }: { locale: Locale; tone?: Tone }) {
  const pathname = usePathname();
  const rest = pathname.split("/").slice(2).join("/");
  const dark = tone === "dark";

  return (
    <nav
      aria-label="Language"
      className={`flex items-center rounded-full p-[3px] ${dark ? "bg-white/10" : "bg-zinc-200"}`}
    >
      {/* Поля кнопок на узком экране уже (px-2.5): с тремя языками шапка
          иначе не помещается в 320 px. */}
      {[...localesOfCountry(countryOf(locale))]
        .sort((a, b) => languages.indexOf(languageOf(a)) - languages.indexOf(languageOf(b)))
        .map((code) => {
        const active = code === locale;
        return (
          <Link
            key={code}
            href={`/${code}${rest ? `/${rest}` : ""}`}
            aria-current={active ? "page" : undefined}
            className={`inline-flex h-[30px] items-center rounded-full px-2.5 text-[13px] sm:px-3.5 ${
              active
                ? `bg-white font-semibold text-zinc-900 shadow-pill`
                : `font-medium ${dark ? "text-slate-300 hover:text-white" : "text-zinc-600 hover:text-zinc-900"}`
            }`}
          >
            {languageOf(code).toUpperCase()}
          </Link>
        );
      })}
    </nav>
  );
}
