"use client";

import Link from "next/link";
import { useSystemMessages } from "@/components/SystemMessages";

// Страница «не найдено» внутри оболочки сайта: с шапкой, подвалом и на языке
// страницы. Открывается, когда программа не найдена (notFound() в карточке и
// калькуляторе) и для любого несуществующего адреса — через маршрут-ловушку
// [...rest]/page.tsx. Код ответа — 404, Next.js сам добавляет noindex.
export default function NotFound() {
  const { locale, messages } = useSystemMessages();
  const t = messages.notFound;

  return (
    <main className="page-container py-8 sm:py-12">
      <div className="surface mx-auto max-w-2xl p-6 sm:p-10">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900">{t.title}</h1>
        <p className="mt-3 max-w-[60ch] leading-relaxed text-zinc-600">{t.text}</p>
        <p className="mt-6 flex flex-wrap gap-x-6 gap-y-3">
          <Link href={`/${locale}/programmes`} className="font-medium text-zinc-900 underline">
            {t.catalog}
          </Link>
          <Link href={`/${locale}`} className="font-medium text-zinc-900 underline">
            {t.home}
          </Link>
        </p>
      </div>
    </main>
  );
}
