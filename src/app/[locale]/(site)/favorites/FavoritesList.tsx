"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { enumLabel, getProgrammesByIds, localizedName, type ProgrammeWithUniversity } from "@/lib/catalog";
import { matchRounds, type ApplicationRound } from "@/lib/deadlines";
import { getFavoriteIds, subscribeToFavorites } from "@/lib/favorites";
import { interpolate } from "@/lib/outcomes";
import { ProgrammeCard } from "@/components/ProgrammeCard";
import { ArrowRightIcon, CheckIcon, StarIcon, XIcon } from "@/components/icons";

type Row = { label: string; render: (programme: ProgrammeWithUniversity) => string };

const FOCUS = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

// Больше четырёх колонок таблица сравнения не читается ни на телефоне,
// ни на ноутбуке — поэтому сравнивать можно не больше четырёх за раз.
const MAX_COMPARE = 4;

export function FavoritesList({
  locale,
  dict,
  calculatorIds,
  applicationRounds,
}: {
  locale: Locale;
  dict: Dictionary;
  /** id программ с подтверждённой формулой — для кнопки калькулятора на карточке. */
  calculatorIds: string[];
  /** Подтверждённые сроки подачи — для чипа «до …» на карточке. */
  applicationRounds: ApplicationRound[];
}) {
  // null — ещё не прочитали localStorage (первая отрисовка на сервере его
  // не видит); [] — прочитали, и там пусто. Различие нужно, чтобы не
  // мигнуть пустым состоянием на долю секунды при каждой загрузке.
  const [programmes, setProgrammes] = useState<ProgrammeWithUniversity[] | null>(null);
  // null — человек ещё ничего не выбирал: сравниваем первые MAX_COMPARE.
  const [chosenIds, setChosenIds] = useState<string[] | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const ids = getFavoriteIds();
      if (ids.length === 0) {
        if (!cancelled) setProgrammes([]);
        return;
      }
      const data = await getProgrammesByIds(ids);
      // База отдаёт в своём порядке — возвращаем порядок, в котором человек
      // добавлял программы: от него зависит, какие четыре сравниваются
      // по умолчанию.
      data.sort((a, b) => ids.indexOf(a.id) - ids.indexOf(b.id));
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

  // Выбор для сравнения. Программу могли убрать из списка звездой — такие
  // id отбрасываем, чтобы лимит считался только по тому, что видно.
  const compareIds = (chosenIds ?? programmes.slice(0, MAX_COMPARE).map((p) => p.id)).filter((id) =>
    programmes.some((p) => p.id === id),
  );
  const compared = programmes.filter((p) => compareIds.includes(p.id));
  const limitReached = compareIds.length >= MAX_COMPARE;

  function toggleCompare(id: string) {
    setChosenIds(compareIds.includes(id) ? compareIds.filter((other) => other !== id) : [...compareIds, id]);
  }

  const calculatorSet = new Set(calculatorIds);

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
    <>
      {/* Те же карточки, что в каталоге, плюс галочка «сравнить». */}
      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {programmes.map((programme) => {
          const selected = compareIds.includes(programme.id);
          const nextRound = matchRounds(
            applicationRounds,
            programme.university_id,
            programme.degree_level,
            programme.language_of_instruction,
          ).find((round) => round.closesOn !== null);

          return (
            <ProgrammeCard
              key={programme.id}
              locale={locale}
              dict={dict}
              programme={programme}
              hasCalculator={calculatorSet.has(programme.id)}
              deadline={
                nextRound
                  ? `${dict.programme.deadlinesCloses} ${new Date(nextRound.closesOn!).toLocaleDateString(locale)}`
                  : null
              }
              footer={
                <label
                  className={`inline-flex items-center gap-2 text-sm font-medium ${
                    !selected && limitReached ? "cursor-not-allowed text-zinc-500" : "cursor-pointer text-zinc-900"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selected}
                    // Пятую выбрать нельзя; снять выбранную можно всегда.
                    disabled={!selected && limitReached}
                    onChange={() => toggleCompare(programme.id)}
                    className="peer sr-only"
                  />
                  {/* Рамка zinc-500: контур чекбокса — элемент интерфейса,
                      нужен контраст 3:1 к фону (WCAG 1.4.11). */}
                  <span className="grid h-5 w-5 shrink-0 place-items-center rounded-md border-[1.5px] border-zinc-500 bg-white text-white peer-checked:border-brand peer-checked:bg-brand peer-disabled:border-zinc-300 peer-disabled:bg-zinc-100 peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-brand [&>svg]:opacity-0 peer-checked:[&>svg]:opacity-100">
                    <CheckIcon size={13} />
                  </span>
                  {dict.favorites.compare}
                  <span className="sr-only">: {localizedName(programme, locale)}</span>
                </label>
              }
            />
          );
        })}
      </div>

      <section aria-labelledby="compare-heading" className="mt-12">
        <h2 id="compare-heading" className="text-2xl font-bold tracking-tight text-zinc-900">
          {dict.favorites.compareTitle}
        </h2>
        {/* aria-live: при выборе галочки счётчик меняется — скринридер это озвучит. */}
        <p className="mt-2 text-sm leading-relaxed text-zinc-600" aria-live="polite">
          {interpolate(dict.favorites.compareLimit, { count: compareIds.length, max: MAX_COMPARE })}
        </p>

        {compared.length === 0 ? (
          <p className="surface mt-5 px-6 py-10 text-center text-zinc-600">{dict.favorites.compareEmpty}</p>
        ) : (
          <div className="surface mt-5 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-sm">
                <thead>
                  <tr>
                    <th scope="col" className={`${STICKY} w-44 border-b border-zinc-200 p-4 sm:p-6`}>
                      <span className="sr-only">{dict.favorites.compareTitle}</span>
                    </th>
                    {compared.map((programme) => (
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
                          {/* Убирает только из сравнения — в списке программа
                              остаётся (из списка убирает звезда на карточке). */}
                          <button
                            type="button"
                            onClick={() => toggleCompare(programme.id)}
                            aria-label={`${dict.favorites.removeFromCompare}: ${localizedName(programme, locale)}`}
                            title={dict.favorites.removeFromCompare}
                            className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-700 ${FOCUS}`}
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
                      {compared.map((programme) => (
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
        )}
      </section>
    </>
  );
}
