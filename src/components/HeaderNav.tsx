"use client";

import { useSyncExternalStore } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Locale } from "@/i18n/config";
import { getFavoriteIds, subscribeToFavorites } from "@/lib/favorites";

type Labels = { catalog: string; survey: string; favorites: string; main: string };

// Клиентский компонент — нужен и usePathname() (подсветить текущий
// раздел), и счётчик избранного из localStorage (тот же useSyncExternalStore,
// что был в FavoritesNavLink, который эта навигация заменила).
export function HeaderNav({ locale, labels, className }: { locale: Locale; labels: Labels; className?: string }) {
  const pathname = usePathname();
  const favoritesCount = useSyncExternalStore(
    subscribeToFavorites,
    () => getFavoriteIds().length,
    () => 0,
  );

  const items = [
    { href: `/${locale}/programmes`, label: labels.catalog, badge: 0 },
    { href: `/${locale}/survey`, label: labels.survey, badge: 0 },
    { href: `/${locale}/favorites`, label: labels.favorites, badge: favoritesCount },
  ];

  return (
    <nav aria-label={labels.main} className={className}>
      <ul className="flex items-center gap-1">
        {items.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`inline-flex h-9 items-center gap-2 rounded-full px-3.5 text-sm font-medium transition-colors ${
                  active ? "bg-zinc-200 text-zinc-900" : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
                }`}
              >
                {item.label}
                {item.badge > 0 && (
                  <span className="grid h-5 min-w-5 place-items-center rounded-full bg-brand px-1.5 text-[11px] font-semibold text-white">
                    {item.badge}
                  </span>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
