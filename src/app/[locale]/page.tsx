import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";

export default async function HomePage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);

  return (
    <main className="relative flex-1 overflow-hidden">
      {/* Pilsētu tīkls — 7 katalogā pārstāvētās pilsētas, Rīga kā mezgls
          (tur ir visvairāk programmu). Tikai fons, ne informācija — tāpēc
          aria-hidden un bez pilsētu nosaukumiem. */}
      <svg
        aria-hidden="true"
        viewBox="0 0 500 800"
        preserveAspectRatio="xMidYMid slice"
        className="pointer-events-none absolute inset-y-0 right-0 hidden w-[420px] select-none sm:block lg:w-[520px]"
        style={{
          maskImage: "linear-gradient(to right, transparent, black 35%)",
          WebkitMaskImage: "linear-gradient(to right, transparent, black 35%)",
        }}
      >
        <path
          d="M 220,100 C 300,90 370,110 410,170 C 440,215 430,260 445,310 C 460,365 450,420 440,470 C 430,520 445,560 420,600 C 395,645 350,660 300,650 C 250,660 190,655 150,620 C 105,585 80,540 75,480 C 65,420 90,370 80,320 C 70,260 90,210 130,170 C 160,135 185,110 220,100 Z"
          fill="#e5f0ff"
          stroke="#bcdcff"
          strokeWidth="1.5"
        />
        <g stroke="#006fee" strokeWidth="1.6" opacity="0.4">
          <line x1="120" y1="220" x2="250" y2="400" />
          <line x1="300" y1="150" x2="250" y2="400" />
          <line x1="400" y1="420" x2="250" y2="400" />
          <line x1="360" y1="600" x2="250" y2="400" />
          <line x1="230" y1="620" x2="250" y2="400" />
          <line x1="110" y1="580" x2="250" y2="400" />
        </g>
        <g fill="#006fee">
          <circle cx="120" cy="220" r="7" />
          <circle cx="300" cy="150" r="7" />
          <circle cx="400" cy="420" r="7" />
          <circle cx="360" cy="600" r="7" />
          <circle cx="230" cy="620" r="7" />
          <circle cx="110" cy="580" r="7" />
          <circle cx="250" cy="400" r="10" fill="#004a9f" />
        </g>
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
