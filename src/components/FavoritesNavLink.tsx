"use client";

import { useSyncExternalStore } from "react";
import Link from "next/link";
import type { Locale } from "@/i18n/config";
import { getFavoriteIds, subscribeToFavorites } from "@/lib/favorites";

export function FavoritesNavLink({ locale, label }: { locale: Locale; label: string }) {
  const count = useSyncExternalStore(
    subscribeToFavorites,
    () => getFavoriteIds().length,
    () => 0,
  );

  return (
    <Link href={`/${locale}/favorites`} className="text-sm font-medium text-zinc-600 hover:text-zinc-900">
      {label}
      {count > 0 && (
        <span className="ml-1.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-zinc-900 px-1.5 text-xs font-semibold text-white">
          {count}
        </span>
      )}
    </Link>
  );
}
