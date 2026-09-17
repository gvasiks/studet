import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { getVerificationHealth, getVerificationQueue, type VerificationQueueItem } from "@/lib/verification-queue";

// Данные меняются с каждым запуском конвейера — как и /programmes,
// страница не может закаменеть на состоянии последней сборки.
export const dynamic = "force-dynamic";

// Внутренний рабочий инструмент (ревью 2026-09, пункт 03), не часть
// продукта ни для одной из двух аудиторий — поэтому текст сразу на
// латышском, без словаря локалей (правило 1 CLAUDE.md — про интерфейс
// для пользователей, не про однострочный список для себя). noindex,
// follow: false — в отличие от /favorites, сюда не должны вести ссылки
// из выдачи вообще.
export async function generateMetadata({ params }: PageProps<"/[locale]/verification">): Promise<Metadata> {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  return {
    title: "Verifikācijas rinda",
    robots: { index: false, follow: false },
  };
}

const FACT_TYPE_LABEL: Record<VerificationQueueItem["factType"], string> = {
  formula: "Konkursa formula",
  application_round: "Pieteikšanās termiņš",
  admission_type: "Uzņemšanas veids",
};

export default async function VerificationPage({ params }: PageProps<"/[locale]/verification">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const [health, queue] = await Promise.all([getVerificationHealth(), getVerificationQueue()]);
  const healthPercent = health.totalFormulas > 0 ? Math.round((health.verifiedFormulas / health.totalFormulas) * 100) : 0;

  return (
    <main className="mx-auto max-w-4xl px-6 py-16">
      <h1 className="text-3xl font-bold tracking-tighter text-zinc-900">Verifikācijas rinda</h1>
      <p className="mt-2 max-w-2xl text-zinc-600">
        Kas vēl nav apstiprināts. Pats šis saraksts neko negroza — apstiprināšana notiek Supabase Studio
        (CLAUDE.md, 6. noteikums).
      </p>

      <div className="mt-6 rounded-xl border border-zinc-200 p-4 text-sm">
        <p className="text-zinc-900">
          Apstiprinātas formulas: <strong>{health.verifiedFormulas}</strong> no <strong>{health.totalFormulas}</strong> (
          {healthPercent}%)
        </p>
        <p className="mt-1 text-zinc-600">Rindā palicis: {queue.length}</p>
      </div>

      {queue.length === 0 ? (
        <p className="mt-8 text-zinc-500">Rinda tukša — viss savāktais ir apstiprināts.</p>
      ) : (
        <ul className="mt-8 divide-y divide-zinc-200">
          {queue.map((item) => (
            <li key={item.factId} className="flex items-start justify-between gap-3 py-4">
              <div>
                <p className="font-medium text-zinc-900">
                  {FACT_TYPE_LABEL[item.factType]}
                  {item.programmeName && ` — ${item.programmeName}`}
                </p>
                <p className="mt-1 text-sm text-zinc-600">
                  {item.universityName}
                  {" · savākts "}
                  {new Date(item.collectedAt).toLocaleDateString(locale)}
                </p>
              </div>
              {item.sourceUrl && (
                <a
                  href={item.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 text-sm text-brand underline"
                >
                  Avots
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
