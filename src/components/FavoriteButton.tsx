"use client";

import { useSyncExternalStore } from "react";
import { isFavorite, subscribeToFavorites, toggleFavorite } from "@/lib/favorites";

export function FavoriteButton({
  programmeId,
  addLabel,
  removeLabel,
  className,
}: {
  programmeId: string;
  addLabel: string;
  removeLabel: string;
  className?: string;
}) {
  // useSyncExternalStore, не useState+useEffect: localStorage — внешнее
  // хранилище, а не React-состояние. На сервере снапшота нет — там всегда
  // "не в избранном" (getServerSnapshot), что и так безопасно: избранное
  // не влияет на то, что видит поисковик или первый отрисованный экран.
  const favorited = useSyncExternalStore(
    subscribeToFavorites,
    () => isFavorite(programmeId),
    () => false,
  );

  return (
    <button
      type="button"
      aria-pressed={favorited}
      aria-label={favorited ? removeLabel : addLabel}
      title={favorited ? removeLabel : addLabel}
      onClick={() => toggleFavorite(programmeId)}
      className={`shrink-0 text-xl leading-none transition-colors ${
        favorited ? "text-amber-500" : "text-zinc-300 hover:text-zinc-400"
      } ${className ?? ""}`}
    >
      {favorited ? "★" : "☆"}
    </button>
  );
}
