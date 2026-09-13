import Link from "next/link";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";

export default async function HomePage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);

  return (
    <main className="mx-auto flex max-w-3xl flex-1 flex-col justify-center px-6 py-24">
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
    </main>
  );
}
