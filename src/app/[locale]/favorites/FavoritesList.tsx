"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { enumLabel, getProgrammesByIds, localizedName, type ProgrammeWithUniversity } from "@/lib/catalog";
import { getFavoriteIds, subscribeToFavorites, toggleFavorite } from "@/lib/favorites";

type Row = { label: string; render: (programme: ProgrammeWithUniversity) => string };

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

  if (programmes.length === 0) {
    return (
      <div className="mt-10">
        <p className="text-zinc-600">{dict.favorites.empty}</p>
        <Link
          href={`/${locale}/programmes`}
          className="mt-4 inline-block rounded-full bg-brand px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-dark"
        >
          {dict.home.catalogCta}
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

  return (
    <div className="mt-8 overflow-x-auto">
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr>
            <th className="w-40" scope="col" />
            {programmes.map((programme) => (
              <th key={programme.id} scope="col" className="min-w-[220px] border-b border-zinc-200 px-4 pb-4 align-top">
                <button
                  type="button"
                  onClick={() => toggleFavorite(programme.id)}
                  className="mb-2 text-xs text-zinc-400 hover:text-zinc-600"
                >
                  {dict.favorites.removeFromCompare} ✕
                </button>
                <Link
                  href={`/${locale}/programmes/${programme.university.slug}/${programme.slug}`}
                  className="block font-medium text-zinc-900 hover:underline"
                >
                  {localizedName(programme, locale)}
                </Link>
                <p className="mt-1 text-xs text-zinc-500">{localizedName(programme.university, locale)}</p>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="border-b border-zinc-100">
              <th scope="row" className="py-3 pr-4 align-top text-xs font-medium uppercase tracking-wide text-zinc-500">
                {row.label}
              </th>
              {programmes.map((programme) => (
                <td key={programme.id} className="px-4 py-3 text-zinc-900">
                  {row.render(programme)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
