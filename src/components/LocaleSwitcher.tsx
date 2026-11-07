"use client";

import { Suspense, useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import {
  countryOf,
  homeLocaleFor,
  languageOf,
  languages,
  locales,
  localesOfCountry,
  type Language,
  type Locale,
} from "@/i18n/config";
import { ChevronsUpDownIcon, GlobeIcon } from "@/components/icons";

export type Tone = "light" | "dark";

// Выпадающий список языков (решение владельца 2026-11-07: языков будет
// больше, кнопки в ряд не масштабируются). Шаблон тот же, что у меню
// «Izvēlne» в HeaderNav: кнопка с aria-expanded и aria-controls, список
// ссылок; закрывается по Esc, по клику мимо и при выборе пункта.
//
// Куда ведёт язык:
// - на главной — в страну этого языка, пока она открыта (LT → /lt, ET → /et;
//   английский — в текущую страну): homeLocaleFor в config.ts;
// - на остальных страницах — та же страница той же страны на другом языке
//   (решение 2026-10-06), иначе человек на латвийской программе, выбрав LT,
//   потерял бы страницу.
//
// Нужен usePathname(): чтобы остаться на той же странице, меняется только
// первый сегмент пути. Ссылки, а не кнопки: другой язык — другой адрес и
// другой индексируемый документ.
type Props = { locale: Locale; label: string; names: Record<Language, string>; tone?: Tone };

// Параметры адреса (фильтры каталога) переносятся в ссылку на другой язык —
// иначе переключение языка сбрасывало выбранные фильтры (аудит 2026-10-04).
// useSearchParams требует границы Suspense, иначе Next.js не может отдать
// страницу статикой; пока параметры не прочитаны, ссылки — без них.
export function LocaleSwitcher(props: Props) {
  return (
    <Suspense fallback={<Switcher {...props} query="" placeholder />}>
      <SwitcherWithQuery {...props} />
    </Suspense>
  );
}

function SwitcherWithQuery(props: Props) {
  const query = useSearchParams().toString();
  return <Switcher {...props} query={query ? `?${query}` : ""} />;
}

function Switcher({
  locale,
  label,
  names,
  tone = "light",
  query,
  placeholder = false,
}: Props & { query: string; placeholder?: boolean }) {
  const pathname = usePathname();
  const rest = pathname.split("/").slice(2).join("/");
  const dark = tone === "dark";
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  // Пока useSearchParams не прочитан, React держит в странице вторую,
  // скрытую копию переключателя на том же месте дерева — useId у них
  // совпадает, поэтому у запасной копии свой суффикс: id не повторяется.
  const menuId = `${useId()}${placeholder ? "-placeholder" : ""}`;

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: PointerEvent) {
      if (!boxRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        buttonRef.current?.focus();
      }
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const country = countryOf(locale);
  const isHome = rest === "";
  // Языки в одном порядке на всех страницах (languages в config.ts); только
  // те, у которых есть открытый адрес.
  const options = languages
    .filter((language) => locales.some((candidate) => languageOf(candidate) === language))
    .map((language) => {
      const target = isHome
        ? homeLocaleFor(language, country)
        : localesOfCountry(country).find((candidate) => languageOf(candidate) === language);
      return target ? { language, href: `/${target}${rest ? `/${rest}` : ""}${query}` } : null;
    })
    .filter((option) => option !== null);
  const current = languageOf(locale);

  return (
    <div ref={boxRef} className="relative">
      <button
        ref={buttonRef}
        type="button"
        aria-expanded={open}
        aria-controls={menuId}
        // Видна только буква кода — экранный диктор слышит «Valoda: Latviešu».
        aria-label={`${label}: ${names[current]}`}
        onClick={() => setOpen((value) => !value)}
        className={`inline-flex h-9 items-center gap-1.5 rounded-full px-3 text-[13px] font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 ${
          dark
            ? "border border-white/15 bg-white/5 text-white hover:bg-white/10 focus-visible:outline-white"
            : "bg-zinc-100 text-zinc-900 hover:bg-zinc-200 focus-visible:outline-brand"
        }`}
      >
        <GlobeIcon size={15} className={dark ? "text-slate-300" : "text-zinc-500"} />
        {current.toUpperCase()}
        <ChevronsUpDownIcon size={13} className={dark ? "text-slate-400" : "text-zinc-400"} />
      </button>
      <ul
        id={menuId}
        hidden={!open}
        aria-label={label}
        className="absolute right-0 top-full z-40 mt-2 w-44 rounded-2xl bg-white p-1.5 shadow-lg ring-1 ring-black/5"
      >
        {options.map(({ language, href }) => {
          const active = language === current;
          return (
            <li key={language}>
              <Link
                href={href}
                lang={language}
                hrefLang={language}
                aria-current={active ? "page" : undefined}
                onClick={() => setOpen(false)}
                className={`flex h-10 items-center justify-between gap-2 rounded-xl px-3 text-sm ${
                  active ? "bg-zinc-100 font-semibold text-zinc-900" : "text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900"
                }`}
              >
                {names[language]}
                <span className="text-xs font-medium text-zinc-400">{language.toUpperCase()}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
