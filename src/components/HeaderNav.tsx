"use client";

import { useSyncExternalStore } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/i18n/config";
import { getFavoriteIds, subscribeToFavorites } from "@/lib/favorites";
import { StarIcon } from "@/components/icons";
import type { Tone } from "@/components/LocaleSwitcher";

type Labels = { catalog: string; survey: string; favorites: string; main: string };

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
// раздел), и счётчик избранного из localStorage (useSyncExternalStore).
//
// На светлых страницах "Мой список" — третий пункт навигации; на
// главной (тёмный вариант) он вынесен вправо отдельной кнопкой,
// см. FavoritesLink.
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

  const items = [
    { href: `/${locale}/programmes`, label: labels.catalog, badge: 0 },
    { href: `/${locale}/survey`, label: labels.survey, badge: 0 },
    ...(dark ? [] : [{ href: `/${locale}/favorites`, label: labels.favorites, badge: favoritesCount }]),
  ];

  return (
    <nav aria-label={labels.main} className={className}>
      <ul className="flex items-center gap-1">
        {items.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
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
                className={`inline-flex h-9 items-center gap-2 rounded-full px-3.5 text-sm font-medium transition-colors ${palette}`}
              >
                {item.label}
                <CountBadge count={item.badge} />
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export function FavoritesLink({ locale, label }: { locale: Locale; label: string }) {
  const count = useFavoritesCount();

  return (
    <Link
      href={`/${locale}/favorites`}
      className="inline-flex h-9 items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3.5 text-sm font-medium text-white transition-colors hover:bg-white/10"
    >
      <StarIcon size={14} />
      {label}
      <CountBadge count={count} />
    </Link>
  );
}
