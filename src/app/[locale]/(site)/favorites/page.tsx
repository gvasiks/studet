import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getDictionary } from "@/i18n/dictionaries";
import { FavoritesList } from "./FavoritesList";

// noindex — страница у каждого посетителя своя (localStorage конкретного
// браузера), у неё нет содержимого, общего для двух разных людей, а
// значит и смысла попадать в выдачу (ревью 2026-09, пункт 08).
export async function generateMetadata({ params }: PageProps<"/[locale]/favorites">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);
  return {
    title: dict.favorites.title,
    robots: { index: false, follow: true },
  };
}

export default async function FavoritesPage({ params }: PageProps<"/[locale]/favorites">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const dict = await getDictionary(locale);

  return (
    // Заголовок — на сером фоне, как на /rights, /glossary и /survey;
    // раньше он лежал внутри карточки, из-за чего страница выглядела иначе,
    // чем остальные. Карточку теперь заводит сам список: таблице сравнения
    // нужна вся ширина, а пустому состоянию — своя форма.
    <main className="page-container py-8 sm:py-12">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">{dict.favorites.title}</h1>
        <p className="mt-3 max-w-[65ch] text-lg leading-relaxed text-zinc-600">{dict.favorites.subtitle}</p>
      </header>
      <FavoritesList locale={locale} dict={dict} />
    </main>
  );
}
