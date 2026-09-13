import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";

export default async function HomePage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);

  return (
    <main className="relative flex-1">
      {/* Stopka grāmatu ar atvērtu grāmatu virsū — tikai dekoratīva ilustrācija.
          Fiksētas proporcijas (aspect-ratio sakrīt ar viewBox) un
          preserveAspectRatio="xMidYMid meet" (nevis "slice") apzināti —
          iepriekšējais fona variants (pilsētu karte) pie mainīga augstuma
          tika apgriezts un izskatījās tukšs; šī nekad netiek apcirsta,
          tikai samazinās. */}
      <svg
        aria-hidden="true"
        viewBox="0 0 400 380"
        preserveAspectRatio="xMidYMid meet"
        className="pointer-events-none absolute right-6 bottom-6 hidden aspect-[400/380] w-[220px] select-none sm:block lg:right-10 lg:bottom-10 lg:w-[300px]"
      >
        <ellipse cx="200" cy="330" rx="165" ry="12" fill="#0a3d7a" opacity="0.08" />

        <g transform="rotate(-3 200 305)">
          <rect x="45" y="286" width="310" height="36" rx="5" fill="#0a3d7a" />
          <rect x="45" y="286" width="14" height="36" fill="#082f61" />
        </g>
        <g transform="rotate(2.5 200 268)">
          <rect x="68" y="250" width="264" height="32" rx="5" fill="#4a7c66" />
          <rect x="68" y="250" width="12" height="32" fill="#375f4d" />
        </g>
        <g transform="rotate(-4 200 235)">
          <rect x="58" y="218" width="232" height="28" rx="5" fill="#d6a12a" />
          <rect x="58" y="218" width="11" height="28" fill="#a97e1a" />
        </g>

        <polygon points="200,120 78,132 96,224 200,222" fill="#fbf9f5" stroke="#0a3d7a" strokeWidth="1.5" />
        <polygon points="200,120 322,132 304,224 200,222" fill="#fbf9f5" stroke="#0a3d7a" strokeWidth="1.5" />
        <line x1="200" y1="120" x2="200" y2="222" stroke="#0a3d7a" strokeWidth="2" opacity="0.5" />

        <g stroke="#c9c2b4" strokeWidth="3" strokeLinecap="round">
          <line x1="100" y1="155" x2="180" y2="152" />
          <line x1="98" y1="172" x2="182" y2="169" />
          <line x1="97" y1="189" x2="183" y2="187" />
          <line x1="96" y1="206" x2="184" y2="204" />
          <line x1="300" y1="155" x2="220" y2="152" />
          <line x1="302" y1="172" x2="218" y2="169" />
          <line x1="303" y1="189" x2="217" y2="187" />
          <line x1="304" y1="206" x2="216" y2="204" />
        </g>

        <path d="M193,95 h14 v34 l-7,-8 l-7,8 Z" fill="#b23b2e" />
      </svg>

      <div className="relative mx-auto flex h-full max-w-3xl flex-col justify-center px-6 py-24">
        <h1 className="text-4xl font-bold tracking-tighter text-zinc-900">
          {dict.home.title}
        </h1>
        <p className="mt-4 text-lg text-zinc-600">{dict.home.description}</p>
        <Link
          href={`/${locale}/programmes`}
          className="mt-6 inline-block w-fit rounded-full bg-brand px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-dark"
        >
          {dict.home.catalogCta}
        </Link>
      </div>
    </main>
  );
}
