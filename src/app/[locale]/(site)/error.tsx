"use client";

import Link from "next/link";
import { useSystemMessages } from "@/components/SystemMessages";

// Страница «не удалось загрузить» — вместо голой ошибки 500, когда не
// ответила база (запросы в src/lib бросают исключение). Шапка и подвал
// остаются. Текст самой ошибки человеку не показывается: он ему ничего не
// скажет, а в нём могут оказаться внутренние подробности.
export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const { locale, messages } = useSystemMessages();
  const t = messages.error;

  return (
    <main className="page-container py-8 sm:py-12">
      <div className="surface mx-auto max-w-2xl p-6 sm:p-10">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900">{t.title}</h1>
        <p className="mt-3 max-w-[60ch] leading-relaxed text-zinc-600">{t.text}</p>
        <p className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
          <button
            type="button"
            onClick={reset}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700"
          >
            {t.retry}
          </button>
          <Link href={`/${locale}/programmes`} className="font-medium text-zinc-900 underline">
            {t.catalog}
          </Link>
        </p>
      </div>
    </main>
  );
}
