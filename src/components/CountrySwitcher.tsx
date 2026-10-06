import Link from "next/link";
import { countries, countryOf, languageOf, localeFor, type Locale } from "@/i18n/config";
import type { Dictionary } from "@/i18n/dictionaries";
import type { Tone } from "@/components/LocaleSwitcher";

// Переход между каталогами стран. Переключатель языка в шапке меняет язык
// внутри одной страны (у литовского каталога нет латышской версии), поэтому
// страна выбирается отдельно — здесь, в подвале.
//
// Ссылка ведёт на главную другой страны, а не на «ту же страницу»: у
// программы одной страны нет пары в другой. Язык сохраняется, если он у
// той страны есть (английский), иначе открывается её основной.
//
// Пока открыта одна страна, блока нет вовсе.
export function CountrySwitcher({ locale, dict, tone }: { locale: Locale; dict: Dictionary; tone: Tone }) {
  if (countries.length < 2) return null;

  const current = countryOf(locale);
  const dark = tone === "dark";

  return (
    <nav aria-label={dict.nav.country} className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
      <span className={dark ? "text-slate-400" : "text-zinc-600"}>{dict.nav.country}:</span>
      <ul className="flex flex-wrap gap-x-3 gap-y-1">
        {countries.map((country) => (
          <li key={country}>
            {country === current ? (
              <span aria-current="true" className={`font-semibold ${dark ? "text-white" : "text-zinc-900"}`}>
                {dict.countries[country]}
              </span>
            ) : (
              <Link
                href={`/${localeFor(country, languageOf(locale))}`}
                className={`underline ${dark ? "text-slate-300 hover:text-white" : "text-zinc-700 hover:text-zinc-900"}`}
              >
                {dict.countries[country]}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}
