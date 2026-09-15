import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import heroBg from "../../../public/images/hero-bg.png";

export default async function HomePage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);

  return (
    <main className="relative min-h-dvh flex-1 overflow-hidden bg-slate-950">
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

      <div className="relative flex h-full max-w-3xl flex-col justify-center px-6 py-24">
        <h1 className="text-4xl font-bold tracking-tighter text-white">
          {dict.home.title}
        </h1>
        <p className="mt-4 text-lg text-slate-200">{dict.home.description}</p>
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
