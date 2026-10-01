import type { ReactNode } from "react";
import Link from "next/link";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import { ArrowRightIcon, BuildingIcon, CalendarIcon, ClockIcon, GlobeIcon, MapPinIcon } from "@/components/icons";
import { FavoriteButton } from "@/components/FavoriteButton";
import { enumLabel, localizedName } from "@/lib/names";
import type { ProgrammeWithUniversity } from "@/lib/catalog";

// Карточка программы — одна и та же в каталоге и в «Моём списке».
// Без "use client": в каталоге её рисует сервер, в «Моём списке» она
// попадает в клиентский компонент как обычная разметка.
export function ProgrammeCard({
  locale,
  dict,
  programme,
  deadline,
  hasCalculator,
  footer,
}: {
  locale: Locale;
  dict: Dictionary;
  programme: ProgrammeWithUniversity;
  deadline: string | null;
  /** Есть действующая подтверждённая формула — можно посчитать балл. */
  hasCalculator: boolean;
  /** Необязательный блок внизу карточки (галочка «сравнить» в «Моём списке»). */
  footer?: ReactNode;
}) {
  const programmeHref = `/${locale}/programmes/${programme.university.slug}/${programme.slug}`;
  const levelLabel = programme.degree_level in dict.catalog.tabs
    ? dict.catalog.tabs[programme.degree_level as keyof typeof dict.catalog.tabs]
    : enumLabel(dict.catalog.degreeLevel, programme.degree_level);

  return (
    <article className="surface group relative flex flex-col p-5 transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <span className="rounded-full bg-brand-soft px-2.5 py-1 text-xs font-semibold leading-none text-brand-dark">
          {levelLabel}
        </span>
        <FavoriteButton
          programmeId={programme.id}
          addLabel={dict.favorites.add}
          removeLabel={dict.favorites.remove}
          className="-mr-1.5 -mt-1.5"
        />
      </div>

      <h2 className="mt-3 text-[17px] font-semibold leading-snug text-zinc-900">
        {/* Растянутая ссылка: кликабельна вся карточка, а звезда выше по z-index */}
        <Link
          href={programmeHref}
          className="after:absolute after:inset-0 after:rounded-3xl after:content-[''] focus-visible:outline-none focus-visible:after:outline-2 focus-visible:after:outline-brand"
        >
          {localizedName(programme, locale)}
        </Link>
      </h2>
      <p className="mt-1.5 flex items-start gap-1.5 text-[13px] leading-snug text-zinc-600">
        <BuildingIcon size={14} className="mt-0.5 shrink-0" />
        {localizedName(programme.university, locale)}
      </p>

      <div className="mt-auto pt-4">
        <div className="flex flex-wrap gap-2 border-t border-zinc-100 pt-4">
          <Chip icon={<GlobeIcon size={13} />}>
            {enumLabel(dict.catalog.language, programme.language_of_instruction)}
          </Chip>
          {/* город программы, а не вуза: у колледжей с филиалами (Juridiskā
              koledža, LU P.Stradiņa) одна и та же программа идёт в разных
              городах, и без города карточки неотличимы */}
          <Chip icon={<MapPinIcon size={13} />}>
            {enumLabel(dict.catalog.city, programme.city ?? programme.university.city)}
          </Chip>
          {programme.duration_years !== null && (
            <Chip icon={<ClockIcon size={13} />}>
              {programme.duration_years} {dict.catalog.years}
            </Chip>
          )}
          {deadline && <Chip icon={<CalendarIcon size={13} />}>{deadline}</Chip>}
        </div>
        {/* relative z-10 — над растянутой ссылкой карточки, как звезда.
            Ссылка стоит внутри карточки с названием программы, так что её
            цель понятна из контекста (WCAG 2.4.4). */}
        {hasCalculator && (
          <Link
            href={`${programmeHref}/calculator`}
            className="relative z-10 mt-3 inline-flex h-8 items-center gap-1.5 rounded-full bg-brand-soft px-3 text-xs font-semibold text-brand-dark hover:bg-brand hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
          >
            {dict.catalog.calculatorCta}
            <ArrowRightIcon size={13} />
          </Link>
        )}
        {footer && <div className="relative z-10 mt-3">{footer}</div>}
      </div>
    </article>
  );
}

function Chip({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <span className="inline-flex h-7 items-center gap-1.5 rounded-full bg-zinc-100 px-2.5 text-xs font-medium text-zinc-700">
      {icon}
      {children}
    </span>
  );
}
