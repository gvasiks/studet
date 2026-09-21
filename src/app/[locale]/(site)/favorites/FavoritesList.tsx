"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { enumLabel, getProgrammesByIds, localizedName, type ProgrammeWithUniversity } from "@/lib/catalog";
import { getFavoriteIds, subscribeToFavorites, toggleFavorite } from "@/lib/favorites";
import { ArrowRightIcon, StarIcon, XIcon } from "@/components/icons";

type Row = { label: string; render: (programme: ProgrammeWithUniversity) => string };

const FOCUS = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

export function FavoritesList({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  // null — ещё не прочитали localStorage (первая отрисовка на сервере его
  // не видит); [] — прочитали, и там пусто. Различие нужно, чтобы не
  // мигнуть пустым состоянием на долю секунды при каждой загрузке.
  const [programmes, setProgrammes] = useState<ProgrammeWithUniversity[] | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const ids = getFavoriteIds();
      if (ids.length === 0) {
        if (!cancelled) setProgrammes([]);
        return;
      }
      const data = await getProgrammesByIds(ids);
      if (!cancelled) setProgrammes(data);
    }

    load();
    const unsubscribe = subscribeToFavorites(load);
    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, []);

  if (programmes === null) return null;

  // Пустое состояние видит большинство пришедших: на него ведёт пункт меню,
  // а звёздочку до этого никто не нажимал. Раньше это был абзац с кнопкой —
  // теперь звезда объясняет, чем отмечают, а карточка держит форму страницы.
  if (programmes.length === 0) {
    return (
      <div className="surface mt-8 px-6 py-14 text-center sm:px-10">
        <span
          aria-hidden="true"
          className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-brand-soft text-brand"
        >
          <StarIcon size={24} />
        </span>
        <p className="mx-auto mt-5 max-w-[46ch] leading-relaxed text-zinc-600">{dict.favorites.empty}</p>
        <Link
          href={`/${locale}/programmes`}
          className={`mt-6 inline-flex h-11 items-center gap-2 rounded-full bg-brand px-6 text-sm font-medium text-white transition-colors hover:bg-brand-dark ${FOCUS}`}
        >
          {dict.home.catalogCta}
          <ArrowRightIcon size={15} />
        </Link>
      </div>
    );
  }

  const rows: Row[] = [
    { label: dict.programme.degreeLevel, render: (p) => enumLabel(dict.catalog.degreeLevel, p.degree_level) },
    { label: dict.programme.language, render: (p) => enumLabel(dict.catalog.language, p.language_of_instruction) },
    { label: dict.programme.studyMode, render: (p) => enumLabel(dict.catalog.studyMode, p.study_mode) },
    {
      label: dict.programme.duration,
      render: (p) => (p.duration_years !== null ? `${p.duration_years} ${dict.catalog.years}` : "—"),
    },
    { label: dict.programme.city, render: (p) => (p.city ? enumLabel(dict.catalog.city, p.city) : "—") },
    { label: dict.programme.funding, render: (p) => enumLabel(dict.catalog.funding, p.funding_type) },
    {
      label: dict.programme.tuitionFee,
      render: (p) => (p.tuition_fee_amount !== null ? `${p.tuition_fee_amount} ${p.tuition_fee_currency}` : "—"),
    },
    {
      label: dict.programme.budgetPlaces,
      render: (p) => (p.budget_places !== null ? String(p.budget_places) : "—"),
    },
  ];

  // Первая колонка прилипает к левому краю: при четырёх программах таблица
  // уезжает по горизонтали, и без этого читаешь значения, не видя, что это
  // за строка. Ради прилипания фон колонки задаётся явно — иначе под ней
  // просвечивают значения.
  const STICKY = "sticky left-0 z-10 bg-white";

  return (
    <div className="surface mt-8 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr>
              <th scope="col" className={`${STICKY} w-44 border-b border-zinc-200 p-4 sm:p-6`}>
                <span className="sr-only">{dict.favorites.title}</span>
              </th>
              {programmes.map((programme) => (
                <th
                  key={programme.id}
                  scope="col"
                  className="min-w-[230px] border-b border-l border-zinc-100 border-b-zinc-200 p-4 align-top sm:p-6"
                >
                  <div className="flex items-start justify-between gap-2">
                    <Link
                      href={`/${locale}/programmes/${programme.university.slug}/${programme.slug}`}
                      className={`min-w-0 font-semibold leading-snug tracking-tight text-zinc-900 hover:text-brand ${FOCUS}`}
                    >
                      {localizedName(programme, locale)}
                    </Link>
                    {/* Убрать из сравнения — иконка с подписью для скринридера:
                        раньше это была серая строка текста с символом ✕, самый
                        заметный элемент в шапке после названия. */}
                    <button
                      type="button"
                      onClick={() => toggleFavorite(programme.id)}
                      aria-label={dict.favorites.removeFromCompare}
                      title={dict.favorites.removeFromCompare}
                      className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg text-zinc-400 transition-colors hover:bg-zinc-100 hover:text-zinc-700 ${FOCUS}`}
                    >
                      <XIcon size={14} />
                    </button>
                  </div>
                  <p className="mt-1.5 text-xs font-normal leading-snug text-zinc-500">
                    {localizedName(programme.university, locale)}
                  </p>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label} className="border-b border-zinc-100 last:border-b-0">
                <th
                  scope="row"
                  className={`${STICKY} px-4 py-3.5 align-top text-xs font-medium uppercase tracking-wide text-zinc-500 sm:px-6`}
                >
                  {row.label}
                </th>
                {programmes.map((programme) => (
                  <td
                    key={programme.id}
                    className="border-l border-zinc-100 px-4 py-3.5 align-top tabular-nums text-zinc-900 sm:px-6"
                  >
                    {row.render(programme)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
