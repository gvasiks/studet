"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { countryOf, type Locale } from "@/i18n/config";
import { hasFeature, type Feature } from "@/lib/country";
import { getFavoriteIds, subscribeToFavorites } from "@/lib/favorites";
import { MenuIcon, StarIcon, XIcon } from "@/components/icons";
import type { Tone } from "@/components/LocaleSwitcher";

type Labels = {
  catalog: string;
  survey: string;
  match: string;
  favorites: string;
  glossary: string;
  rights: string;
  menu: string;
  main: string;
};

function useFavoritesCount(): number {
  return useSyncExternalStore(
    subscribeToFavorites,
    () => getFavoriteIds().length,
    () => 0,
  );
}

function CountBadge({ count }: { count: number }) {
  if (count === 0) return null;
  return (
    <span className="grid h-5 min-w-5 place-items-center rounded-full bg-brand px-1.5 text-[11px] font-semibold text-white">
      {count}
    </span>
  );
}

// Клиентский компонент — нужен и usePathname() (подсветить текущий
// раздел), и счётчик избранного из localStorage (useSyncExternalStore),
// и открытие меню на узком экране.
//
// На светлых страницах "Мой список" — один из пунктов навигации; на
// главной (тёмный вариант) он вынесен вправо отдельной кнопкой,
// см. FavoritesLink.
//
// Шесть пунктов строкой помещаются только от lg (1024 px). Уже — кнопка
// «Izvēlne» и выпадающий список (шаблон disclosure: кнопка с
// aria-expanded и aria-controls, закрывается по Esc, по клику мимо и
// при выборе пункта).
export function HeaderNav({
  locale,
  labels,
  tone = "light",
  className,
}: {
  locale: Locale;
  labels: Labels;
  tone?: Tone;
  className?: string;
}) {
  const pathname = usePathname();
  const favoritesCount = useFavoritesCount();
  const dark = tone === "dark";
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: PointerEvent) {
      if (!menuRef.current?.contains(event.target as Node)) setOpen(false);
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

  const favoritesItem = { href: `/${locale}/favorites`, label: labels.favorites, badge: favoritesCount, feature: "favorites" as Feature };
  // feature: null — раздел есть у каждой страны; остальные показываются
  // только там, где раздел готов (src/lib/country.ts).
  const allItems: { href: string; label: string; badge: number; feature: Feature | null }[] = [
    { href: `/${locale}/programmes`, label: labels.catalog, badge: 0, feature: null },
    { href: `/${locale}/survey`, label: labels.survey, badge: 0, feature: "survey" },
    { href: `/${locale}/match`, label: labels.match, badge: 0, feature: "match" },
    favoritesItem,
    { href: `/${locale}/glossary`, label: labels.glossary, badge: 0, feature: "glossary" },
    { href: `/${locale}/rights`, label: labels.rights, badge: 0, feature: "rights" },
  ];
  const country = countryOf(locale);
  const menuItems = allItems.filter((item) => item.feature === null || hasFeature(country, item.feature));
  // На главной от lg «Мой список» — отдельная кнопка справа (FavoritesLink),
  // в строке его нет. В выпадающем меню он есть всегда.
  const items = dark ? menuItems.filter((item) => item !== favoritesItem) : menuItems;
  const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);

  return (
    <nav aria-label={labels.main} className={className}>
      {/* Широкий экран: строка пунктов */}
      <ul className="hidden items-center gap-1 lg:flex">
        {items.map((item) => {
          const active = isActive(item.href);
          const palette = dark
            ? active
              ? "bg-white/10 text-white"
              : "text-slate-300 hover:bg-white/5 hover:text-white"
            : active
              ? "bg-zinc-200 text-zinc-900"
              : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900";
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`inline-flex h-9 items-center gap-2 whitespace-nowrap rounded-full px-3.5 text-sm font-medium transition-colors ${palette}`}
              >
                {item.label}
                <CountBadge count={item.badge} />
              </Link>
            </li>
          );
        })}
      </ul>

      {/* Узкий экран: кнопка и выпадающий список */}
      <div ref={menuRef} className="relative lg:hidden">
        <button
          ref={buttonRef}
          type="button"
          aria-expanded={open}
          aria-controls="site-menu"
          onClick={() => setOpen((value) => !value)}
          className={`inline-flex h-9 items-center gap-2 rounded-full px-3.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 ${
            dark
              ? "border border-white/15 bg-white/5 text-white hover:bg-white/10 focus-visible:outline-white"
              : "bg-zinc-100 text-zinc-900 hover:bg-zinc-200 focus-visible:outline-brand"
          }`}
        >
          {open ? <XIcon size={16} /> : <MenuIcon size={16} />}
          {/* На самых узких экранах — только значок; подпись остаётся для
              экранного диктора. */}
          <span className="sr-only sm:not-sr-only">{labels.menu}</span>
          <CountBadge count={favoritesCount} />
        </button>
        <ul
          id="site-menu"
          hidden={!open}
          className="absolute right-0 top-full z-40 mt-2 w-64 max-w-[calc(100vw-2rem)] rounded-2xl bg-white p-1.5 shadow-lg ring-1 ring-black/5"
        >
          {menuItems.map((item) => {
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  onClick={() => setOpen(false)}
                  className={`flex h-10 items-center justify-between gap-2 rounded-xl px-3 text-sm ${
                    active ? "bg-zinc-100 font-semibold text-zinc-900" : "text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900"
                  }`}
                >
                  {item.label}
                  <CountBadge count={item.badge} />
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}

export function FavoritesLink({ locale, label }: { locale: Locale; label: string }) {
  const count = useFavoritesCount();

  return (
    <Link
      href={`/${locale}/favorites`}
      // Уже lg «Мой список» — пункт выпадающего меню, отдельная кнопка не нужна.
      className="hidden h-9 items-center gap-2 rounded-full border lg:inline-flex border-white/15 bg-white/5 px-3.5 text-sm font-medium text-white transition-colors hover:bg-white/10"
    >
      <StarIcon size={14} />
      {label}
      <CountBadge count={count} />
    </Link>
  );
}
