"use client";

import { useSyncExternalStore } from "react";
import { StarIcon } from "@/components/icons";
import { isFavorite, subscribeToFavorites, toggleFavorite } from "@/lib/favorites";

export function FavoriteButton({
  programmeId,
  addLabel,
  removeLabel,
  size = 18,
  className,
}: {
  programmeId: string;
  addLabel: string;
  removeLabel: string;
  size?: number;
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
      // relative z-10: на карточке каталога вся площадь — растянутая
      // ссылка на программу, звезда должна оставаться над ней.
      className={`relative z-10 grid h-8 w-8 shrink-0 place-items-center rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand ${
        // Цвета темнее, чем в макете (#A1A1AA и #F5A524): у них контраст
        // с фоном 2.6:1 и 2:1 — ниже порога 3:1 для элементов интерфейса
        // (WCAG 1.4.11), а звезда и есть индикатор состояния.
        favorited ? "bg-amber-50 text-amber-600" : "text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700"
      } ${className ?? ""}`}
    >
      <StarIcon size={size} filled={favorited} />
    </button>
  );
}
