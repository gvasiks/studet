import Link from "next/link";
import type { Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import {
  ArrowRightIcon,
  BuildingIcon,
  CalendarIcon,
  CheckIcon,
  ChevronsUpDownIcon,
  ClipboardCheckIcon,
  ClockIcon,
  GlobeIcon,
  SearchIcon,
  SortIcon,
} from "@/components/icons";
import { FavoriteButton } from "@/components/FavoriteButton";
import { CITY_KEYS, enumLabel, localizedName, type ProgrammeWithUniversity, type University } from "@/lib/catalog";
import { catalogQuery, LEVEL_KEYS, PAGE_SIZE, SORT_KEYS, type CatalogState } from "@/lib/catalog-query";
import type { CatalogView } from "@/lib/catalog-view";
import { INTEREST_KEYS } from "@/lib/fields";
import { interpolate } from "@/lib/outcomes";

// Поля фильтров — обычные нативные input/select, без JS: страница
// остаётся серверной (правило 4 CLAUDE.md). Состояние "включено"
// рисуется через peer-checked, а не через клиентское состояние.
const FOCUS_RING = "peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-brand";

function SelectField({
  label,
  name,
  defaultValue,
  children,
}: {
  label: string;
  name: string;
  defaultValue: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-[13px] font-medium leading-4 text-zinc-700">{label}</span>
      <span className="relative mt-1.5 block">
        <select
          name={name}
          defaultValue={defaultValue}
          className="h-10 w-full appearance-none rounded-xl bg-zinc-100 pl-3 pr-9 text-sm text-zinc-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
        >
          {children}
        </select>
        <ChevronsUpDownIcon className="pointer-events-none absolute right-3 top-3 text-zinc-500" />
      </span>
    </label>
  );
}

function CheckboxOption({ name, value, label, checked }: { name: string; value: string; label: string; checked: boolean }) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-sm text-zinc-900">
      <input type="checkbox" name={name} value={value} defaultChecked={checked} className="peer sr-only" />
      {/* Рамка zinc-500, не светлее: контур чекбокса — элемент интерфейса, для
          него нужен контраст 3:1 к фону (WCAG 1.4.11). */}
      <span
        className={`grid h-5 w-5 shrink-0 place-items-center rounded-md border-[1.5px] border-zinc-500 bg-white text-white peer-checked:border-brand peer-checked:bg-brand ${FOCUS_RING} [&>svg]:opacity-0 peer-checked:[&>svg]:opacity-100`}
      >
        <CheckIcon size={13} />
      </span>
      {label}
    </label>
  );
}

function ChipOption({ name, value, label, checked }: { name: string; value: string; label: string; checked: boolean }) {
  return (
    <label className="cursor-pointer">
      <input type="checkbox" name={name} value={value} defaultChecked={checked} className="peer sr-only" />
      {/* Галочка в выбранном чипе — чтобы состояние не держалось на одном
          цвете (голубой на сером почти не различим при дальтонизме). */}
      <span
        className={`inline-flex min-h-8 items-center gap-1.5 rounded-full bg-zinc-100 px-3 py-1 text-[13px] leading-tight text-zinc-800 hover:bg-zinc-200 peer-checked:bg-brand-soft peer-checked:font-medium peer-checked:text-brand-dark ${FOCUS_RING} [&_svg]:hidden peer-checked:[&_svg]:inline`}
      >
        <CheckIcon size={12} />
        {label}
      </span>
    </label>
  );
}

export function FilterSidebar({
  locale,
  dict,
  state,
  universities,
}: {
  locale: Locale;
  dict: Dictionary;
  state: CatalogState;
  universities: Pick<University, "slug" | "name_lv" | "name_en">[];
}) {
  const filters = dict.catalog.filters;

  return (
    <>
      {/* На телефоне панель свёрнута: чекбокс + label вместо клиентского
          JS. На lg и шире панель видна всегда. */}
      <input id="filters-toggle" type="checkbox" className="peer sr-only lg:hidden" />
      <label
        htmlFor="filters-toggle"
        className="surface flex h-12 cursor-pointer items-center justify-between px-5 text-sm font-semibold text-zinc-900 peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-brand lg:hidden"
      >
        {dict.catalog.openFilters}
        <ChevronsUpDownIcon className="text-zinc-500" />
      </label>

      <aside className="surface hidden space-y-5 p-6 peer-checked:block lg:sticky lg:top-24 lg:block">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-zinc-900">{filters.title}</h2>
          <Link
            href={`/${locale}/programmes`}
            className="inline-flex h-7 items-center rounded-full px-2.5 text-[13px] font-medium text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
          >
            {dict.catalog.clear}
          </Link>
        </div>

        <SelectField label={filters.university} name="university" defaultValue={state.university ?? ""}>
          <option value="">{filters.anyUniversity}</option>
          {universities.map((university) => (
            <option key={university.slug} value={university.slug}>
              {localizedName(university, locale)}
            </option>
          ))}
        </SelectField>

        <SelectField label={filters.language} name="language" defaultValue={state.language ?? ""}>
          <option value="">{filters.anyLanguage}</option>
          <option value="lv">{dict.catalog.language.lv}</option>
          <option value="en">{dict.catalog.language.en}</option>
        </SelectField>

        <SelectField label={filters.mode} name="mode" defaultValue={state.mode ?? ""}>
          <option value="">{filters.anyMode}</option>
          <option value="full_time">{dict.catalog.studyMode.full_time}</option>
          <option value="part_time">{dict.catalog.studyMode.part_time}</option>
          <option value="distance">{dict.catalog.studyMode.distance}</option>
        </SelectField>

        <fieldset>
          <legend className="text-[13px] font-medium leading-4 text-zinc-700">{filters.city}</legend>
          <div className="mt-2.5 grid grid-cols-2 gap-x-3 gap-y-2.5">
            {CITY_KEYS.map((city) => (
              <CheckboxOption
                key={city}
                name="city"
                value={city}
                label={enumLabel(dict.catalog.city, city)}
                checked={state.cities.includes(city)}
              />
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend className="text-[13px] font-medium leading-4 text-zinc-700">{filters.interest}</legend>
          <div className="mt-2.5 flex flex-wrap gap-2">
            {INTEREST_KEYS.map((key) => (
              <ChipOption
                key={key}
                name="interest"
                value={key}
                label={dict.survey.interests.categories[key]}
                checked={state.interests.includes(key)}
              />
            ))}
          </div>
        </fieldset>

        <div className="border-t border-zinc-200 pt-5">
          <label className="flex cursor-pointer items-center justify-between gap-3">
            <span>
              <span className="block text-sm font-medium text-zinc-900">{filters.budgetOnly}</span>
              <span className="block text-xs text-zinc-600">{filters.budgetOnlyHint}</span>
            </span>
            <input
              type="checkbox"
              role="switch"
              name="budget"
              value="1"
              defaultChecked={state.budgetOnly}
              className="peer sr-only"
            />
            {/* Дорожка zinc-500: выключенный переключатель на белом должен
                читаться с контрастом 3:1, светлее нельзя. */}
            <span
              className={`relative h-[26px] w-11 shrink-0 rounded-full bg-zinc-500 transition-colors after:absolute after:left-[3px] after:top-[3px] after:h-5 after:w-5 after:rounded-full after:bg-white after:shadow after:transition-transform peer-checked:bg-brand peer-checked:after:translate-x-[18px] ${FOCUS_RING}`}
            />
          </label>
        </div>

        {/* Сортировка и уровень при новом поиске не сбрасываются */}
        {state.sort !== "name" && <input type="hidden" name="sort" value={state.sort} />}
        {state.level && <input type="hidden" name="level" value={state.level} />}

        <button
          type="submit"
          className="h-11 w-full rounded-full bg-brand text-sm font-semibold text-white transition-colors hover:bg-brand-dark focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
        >
          {filters.apply}
        </button>
      </aside>
    </>
  );
}

export function SearchAndSort({ locale, dict, state }: { locale: Locale; dict: Dictionary; state: CatalogState }) {
  const base = `/${locale}/programmes`;

  return (
    <div className="flex gap-3">
      <label className="flex h-12 min-w-0 flex-1 items-center gap-3 rounded-2xl bg-white px-4 shadow-control focus-within:outline-2 focus-within:outline-brand">
        <SearchIcon size={18} className="shrink-0 text-zinc-500" />
        <input
          type="search"
          name="q"
          defaultValue={state.q}
          aria-label={dict.catalog.searchLabel}
          placeholder={dict.catalog.searchPlaceholder}
          className="min-w-0 flex-1 bg-transparent text-[15px] text-zinc-900 outline-none placeholder:text-zinc-500"
        />
      </label>

      {/* <details> — раскрывающийся список без JS; варианты — ссылки, они
          сохраняют остальные параметры каталога. */}
      <details className="relative">
        <summary className="flex h-12 cursor-pointer list-none items-center gap-2 rounded-2xl bg-white px-4 text-sm font-medium text-zinc-900 shadow-control focus-visible:outline-2 focus-visible:outline-brand [&::-webkit-details-marker]:hidden">
          <SortIcon />
          <span className="whitespace-nowrap">
            {dict.catalog.sortMenu.label}: {dict.catalog.sortMenu[state.sort]}
          </span>
        </summary>
        <ul className="absolute right-0 z-20 mt-2 w-52 rounded-2xl bg-white p-1.5 shadow-lg ring-1 ring-black/5">
          {SORT_KEYS.map((key) => (
            <li key={key}>
              <Link
                href={`${base}${catalogQuery(state, { sort: key })}`}
                aria-current={key === state.sort ? "true" : undefined}
                className={`flex h-9 items-center rounded-xl px-3 text-sm hover:bg-zinc-100 ${
                  key === state.sort ? "font-semibold text-brand-dark" : "text-zinc-800"
                }`}
              >
                {dict.catalog.sortMenu[key]}
              </Link>
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}

export function LevelTabs({
  locale,
  dict,
  state,
  view,
}: {
  locale: Locale;
  dict: Dictionary;
  state: CatalogState;
  view: CatalogView;
}) {
  const base = `/${locale}/programmes`;
  const tabs = [
    { key: null, label: dict.catalog.tabs.all, count: view.matched },
    ...LEVEL_KEYS.map((key) => ({ key, label: dict.catalog.tabs[key], count: view.levelCounts[key] })),
  ];
  // Латышский: форма единственного числа у чисел на 1, кроме 11 (21, 31...)
  const singular = locale === "lv" ? view.total % 10 === 1 && view.total % 100 !== 11 : view.total === 1;
  const [foundBefore, foundAfter] = (singular ? dict.catalog.foundOne : dict.catalog.found).split("{count}");

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <nav aria-label={dict.catalog.levelTabsLabel} className="max-w-full overflow-x-auto">
        <ul className="inline-flex flex-nowrap whitespace-nowrap rounded-full bg-zinc-200 p-1">
          {tabs.map((tab) => {
            const active = tab.key === state.level;
            return (
              <li key={tab.key ?? "all"}>
                <Link
                  href={`${base}${catalogQuery(state, { level: tab.key, limit: PAGE_SIZE })}`}
                  aria-current={active ? "page" : undefined}
                  className={`inline-flex h-9 items-center gap-2 rounded-full px-4 text-sm transition-colors ${
                    active ? "bg-white font-semibold text-zinc-900 shadow-pill" : "font-medium text-zinc-600 hover:text-zinc-900"
                  }`}
                >
                  {tab.label}
                  <span className={`text-xs ${active ? "font-semibold text-brand" : "text-zinc-600"}`}>{tab.count}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <p className="text-sm text-zinc-600" aria-live="polite">
        {foundBefore}
        <strong className="font-semibold text-zinc-900">{view.total}</strong>
        {foundAfter}
      </p>
    </div>
  );
}

export function ProgrammeCard({
  locale,
  dict,
  programme,
  deadline,
}: {
  locale: Locale;
  dict: Dictionary;
  programme: ProgrammeWithUniversity;
  deadline: string | null;
}) {
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
          href={`/${locale}/programmes/${programme.university.slug}/${programme.slug}`}
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
          {programme.duration_years !== null && (
            <Chip icon={<ClockIcon size={13} />}>
              {programme.duration_years} {dict.catalog.years}
            </Chip>
          )}
          {deadline && <Chip icon={<CalendarIcon size={13} />}>{deadline}</Chip>}
        </div>
      </div>
    </article>
  );
}

function Chip({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <span className="inline-flex h-7 items-center gap-1.5 rounded-full bg-zinc-100 px-2.5 text-xs font-medium text-zinc-700">
      {icon}
      {children}
    </span>
  );
}

export function SurveyCard({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  return (
    <Link
      href={`/${locale}/survey`}
      className="surface flex w-full items-center gap-4 p-5 transition-shadow hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand lg:w-[400px] lg:shrink-0"
    >
      <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-brand-soft text-brand-dark">
        <ClipboardCheckIcon size={22} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-[15px] font-semibold text-zinc-900">{dict.catalog.surveyTeaser}</span>
        <span className="block text-[13px] leading-snug text-zinc-600">{dict.catalog.surveyCardText}</span>
      </span>
      <span className="inline-flex h-10 items-center gap-2 rounded-full bg-brand px-4 text-sm font-medium text-white">
        {dict.catalog.surveyCardCta}
        <ArrowRightIcon />
      </span>
    </Link>
  );
}

export function LoadMore({
  locale,
  dict,
  state,
  view,
}: {
  locale: Locale;
  dict: Dictionary;
  state: CatalogState;
  view: CatalogView;
}) {
  const shown = view.visible.length;
  const percent = view.total > 0 ? Math.round((shown / view.total) * 100) : 0;

  return (
    <div className="mt-10 flex flex-col items-center gap-3">
      <div
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={view.total}
        aria-valuenow={shown}
        aria-label={interpolate(dict.catalog.shown, { shown, total: view.total })}
        className="h-1 w-60 overflow-hidden rounded-full bg-zinc-200"
      >
        <div className="h-full rounded-full bg-brand" style={{ width: `${percent}%` }} />
      </div>
      <p className="text-[13px] text-zinc-600">{interpolate(dict.catalog.shown, { shown, total: view.total })}</p>
      {shown < view.total && (
        <Link
          // scroll={false}: список дорастает вниз, а не прыгает в начало страницы
          scroll={false}
          href={`/${locale}/programmes${catalogQuery(state, { limit: state.limit + PAGE_SIZE })}`}
          className="inline-flex h-10 items-center rounded-full bg-zinc-200 px-5 text-sm font-medium text-zinc-900 transition-colors hover:bg-zinc-300 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
        >
          {dict.catalog.showMore}
        </Link>
      )}
    </div>
  );
}
