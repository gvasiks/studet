import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { ArrowRightIcon } from "@/components/icons";
import { getProgrammeCount, listUniversities } from "@/lib/catalog";
import { interpolate } from "@/lib/outcomes";
import { buildAlternates } from "@/lib/site";

// Счётчик в бейдже — из базы, но главная остаётся статической (быстрая
// первая отрисовка — весь годовой трафик приходится на несколько дней
// июля): пересобирается раз в час.
export const revalidate = 3600;

export async function generateMetadata({ params }: PageProps<"/[locale]">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  return {
    description: dict.home.description,
    alternates: buildAlternates("", locale),
  };
}

// Сбой базы не должен ронять сборку или главную страницу — просто
// не показываем бейдж со счётчиками.
async function loadStats(): Promise<{ programmes: number; universities: number } | null> {
  try {
    const [programmes, universities] = await Promise.all([getProgrammeCount(), listUniversities()]);
    return { programmes, universities: universities.length };
  } catch {
    return null;
  }
}

const FOCUS = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white";

export default async function HomePage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  const stats = await loadStats();

  return (
    <main className="page-container relative z-10 flex flex-1 flex-col justify-center py-16">
      <div className="max-w-[560px]">
        {stats && (
          <span className="inline-flex h-7 items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 text-xs font-medium text-slate-200">
            <span className="h-1.5 w-1.5 rounded-full bg-sky-400" aria-hidden="true" />
            {interpolate(dict.catalog.heroBadge, stats)}
          </span>
        )}
        <h1 className="mt-5 text-4xl font-bold leading-[1.05] tracking-[-0.03em] text-white sm:text-5xl lg:text-[56px]">
          {dict.home.title}
        </h1>
        <p className="mt-5 max-w-md text-lg leading-relaxed text-slate-300">{dict.home.description}</p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href={`/${locale}/programmes`}
            className={`inline-flex h-11 items-center gap-2 rounded-full bg-brand px-6 text-sm font-medium text-white shadow-[0_0_28px_rgba(0,111,238,0.4)] transition-colors hover:bg-brand-dark ${FOCUS}`}
          >
            {dict.home.catalogCta}
            <ArrowRightIcon />
          </Link>
          <Link
            href={`/${locale}/survey`}
            className={`inline-flex h-11 items-center rounded-full border border-white/15 bg-white/5 px-6 text-sm font-medium text-white transition-colors hover:bg-white/10 ${FOCUS}`}
          >
            {dict.home.surveyCta}
          </Link>
        </div>
      </div>
    </main>
  );
}
