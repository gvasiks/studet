import Image from "next/image";
import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { buildAlternates } from "@/lib/site";
import heroBg from "../../../public/images/hero-bg.webp";

export async function generateMetadata({ params }: PageProps<"/[locale]">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  return {
    description: dict.home.description,
    alternates: buildAlternates("", locale),
  };
}

export default async function HomePage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);

  return (
    // 4.5rem — высота шапки: без вычета страница получала лишний скролл
    <main className="relative min-h-[calc(100dvh-4.5rem)] flex-1 overflow-hidden bg-slate-950">
      <Image
        src={heroBg}
        alt=""
        fill
        priority
        sizes="100vw"
        className="object-cover"
      />
      {/* Тёмная подложка слева — гарантирует контраст текста, даже если
          на широком экране светлая (фиолетовая) часть картинки съедет влево. */}
      <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/70 to-transparent" />

      {/* page-container — та же ширина и поля, что у шапки, чтобы текст
          героя стоял на одной вертикали с логотипом */}
      <div className="page-container relative flex h-full flex-col justify-center py-24">
        <div className="max-w-3xl">
          <h1 className="text-4xl font-bold tracking-tighter text-white sm:text-5xl">
            {dict.home.title}
          </h1>
          <p className="mt-4 text-lg text-slate-200">{dict.home.description}</p>
          <Link
            href={`/${locale}/programmes`}
            className="mt-6 inline-flex h-11 items-center rounded-full bg-brand px-6 text-sm font-medium text-white hover:bg-brand-dark"
          >
            {dict.home.catalogCta}
          </Link>
        </div>
      </div>
    </main>
  );
}
