import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { isLocale } from "@/i18n/config";
import { isDocumentStale } from "@/lib/document-age";
import { isPipelineStale } from "@/lib/pipeline-health";
import { getPipelineHealth } from "@/lib/pipeline-health-queries";
import { getVerificationHealth, getVerificationQueue, type VerificationQueueItem } from "@/lib/verification-queue";
import { ArrowRightIcon, CheckIcon, ClockIcon } from "@/components/icons";

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
  programme_field: "Programmu virzieni",
};

// Порядок групп: сверху то, что дороже стоит при ошибке (правило 6 CLAUDE.md).
const FACT_TYPE_ORDER: VerificationQueueItem["factType"][] = [
  "formula",
  "application_round",
  "admission_type",
  "programme_field",
];

// Что мешает подтвердить запись прямо сейчас. Очередь нужна не чтобы
// показать объём, а чтобы ответить «что брать следующим» — поэтому
// заблокированное должно быть видно до чтения текста.
function getBlocker(item: VerificationQueueItem): { text: string; tone: "red" | "amber" } | null {
  if (item.factType !== "formula") return null;
  if (item.protocolComplete === false) {
    return { text: `Protokols nepilns — trūkst ${item.protocolMissing}`, tone: "red" };
  }
  if (isDocumentStale(item.sourceDocDate)) {
    return { text: "Dokuments vecāks par 12 mēnešiem", tone: "amber" };
  }
  return null;
}

export default async function VerificationPage({ params }: PageProps<"/[locale]/verification">) {
  const { locale } = await params;
  if (!isLocale(locale)) notFound();

  const [health, queue, pipeline] = await Promise.all([
    getVerificationHealth(),
    getVerificationQueue(),
    getPipelineHealth(),
  ]);
  const healthPercent = health.totalFormulas > 0 ? Math.round((health.verifiedFormulas / health.totalFormulas) * 100) : 0;
  const pipelineStale = isPipelineStale(pipeline.lastSuccessAt);
  const remaining = queue.reduce((total, item) => total + item.itemCount, 0);
  const blocked = queue.filter((item) => getBlocker(item) !== null).length;

  const groups = FACT_TYPE_ORDER.map((factType) => ({
    factType,
    items: queue.filter((item) => item.factType === factType),
  })).filter((group) => group.items.length > 0);

  return (
    <main className="page-container py-8 sm:py-12">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-bold tracking-tighter text-zinc-900 sm:text-4xl">Verifikācijas rinda</h1>
        <p className="mt-3 leading-relaxed text-zinc-600">
          Kas vēl nav apstiprināts. Pats šis saraksts neko negroza — apstiprināšana notiek Supabase Studio
          (CLAUDE.md, 6. noteikums).
        </p>
      </header>

      {/* Дата последнего успешного полного сбора (план 2026-09-21, неделя 1,
          пункт 08) — самое дешёвое место её заметить: эту страницу и так
          открывают для подтверждений. Точечные перезапуски одного вуза сюда
          не попадают (full_run=false в базе), поэтому дата не мигает от
          них — только от настоящего понедельничного прогона. */}
      <p
        className={`mt-4 flex items-center gap-2 text-sm ${pipelineStale ? "font-medium text-red-700" : "text-zinc-500"}`}
      >
        <ClockIcon size={14} className="shrink-0" />
        {pipeline.lastSuccessAt ? (
          <>
            Pēdējā veiksmīgā savākšana: {new Date(pipeline.lastSuccessAt).toLocaleString(locale)}
            {pipelineStale && " — pagājuši vairāk par 9 dienām, pārbaudiet grafiku GitHub Actions"}
          </>
        ) : (
          "Veiksmīga pilna savākšana vēl nav reģistrēta"
        )}
      </p>

      {/* Показатель здоровья — главное число страницы, а не сноска:
          доля подтверждённых формул решает, что вообще можно показывать
          пользователям. */}
      <section className="surface mt-8 flex flex-wrap items-start gap-x-10 gap-y-6 p-6 sm:p-8">
        {/* Полоса относится только к формулам, поэтому живёт внутри их блока,
            а не под всей карточкой: иначе 96% читались бы как прогресс по всей
            очереди, где лежат ещё сотни записей других типов.
            Числа рядом дублируют её, поэтому для скринридера она скрыта. */}
        <div className="min-w-[14rem] flex-1">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Apstiprinātas formulas</p>
          <p className="mt-1 flex items-baseline gap-2">
            <span className="text-4xl font-bold tabular-nums tracking-tight text-zinc-900">{healthPercent}%</span>
            <span className="text-sm tabular-nums text-zinc-500">
              {health.verifiedFormulas} / {health.totalFormulas}
            </span>
          </p>
          <div aria-hidden="true" className="mt-3 h-2 overflow-hidden rounded-full bg-zinc-100">
            <div className="h-full rounded-full bg-brand" style={{ width: `${healthPercent}%` }} />
          </div>
        </div>
        <dl className="flex gap-8">
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-zinc-500">Rindā</dt>
            <dd className="mt-1 text-2xl font-semibold tabular-nums text-zinc-900">{remaining}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium uppercase tracking-wide text-zinc-500">Bloķēti</dt>
            <dd className={`mt-1 text-2xl font-semibold tabular-nums ${blocked > 0 ? "text-red-700" : "text-zinc-900"}`}>
              {blocked}
            </dd>
          </div>
        </dl>
      </section>

      {queue.length === 0 ? (
        <p className="surface mt-6 flex items-center gap-3 p-6 text-zinc-600 sm:p-8">
          <CheckIcon size={18} className="shrink-0 text-emerald-600" />
          Rinda tukša — viss savāktais ir apstiprināts.
        </p>
      ) : (
        <div className="mt-6 space-y-6">
          {groups.map((group) => (
            <section key={group.factType} className="surface overflow-hidden">
              <h2 className="flex items-baseline justify-between gap-3 border-b border-zinc-100 px-6 py-4 sm:px-8">
                <span className="text-sm font-semibold tracking-tight text-zinc-900">
                  {FACT_TYPE_LABEL[group.factType]}
                </span>
                <span className="text-xs tabular-nums text-zinc-500">
                  {group.items.reduce((total, item) => total + item.itemCount, 0)}
                </span>
              </h2>
              <ul className="divide-y divide-zinc-100">
                {/* fact_id у типов admission_type и programme_field — id вуза, один и тот же: ключом служит пара */}
                {group.items.map((item) => {
                  const blocker = getBlocker(item);
                  return (
                    <li
                      key={`${item.factType}:${item.factId}`}
                      className={`flex flex-wrap items-start justify-between gap-x-4 gap-y-2 px-6 py-4 sm:px-8 ${
                        blocker ? "border-l-2 border-l-red-300 bg-red-50/30" : ""
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <p className="font-medium leading-snug text-zinc-900">
                          {item.programmeName ?? item.universityName}
                          {item.itemCount > 1 && (
                            <span className="ml-1.5 text-sm font-normal tabular-nums text-zinc-500">
                              ×{item.itemCount}
                            </span>
                          )}
                        </p>
                        <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-zinc-500">
                          {item.programmeName && <span>{item.universityName}</span>}
                          <span className="tabular-nums">
                            {new Date(item.collectedAt).toLocaleDateString(locale)}
                          </span>
                          {item.sourceDocDate && (
                            <span className="tabular-nums">
                              {new Date(item.sourceDocDate).toLocaleDateString(locale)}
                            </span>
                          )}
                        </p>
                        {blocker && (
                          <p
                            className={`mt-2 inline-block rounded-lg px-2 py-1 text-xs font-medium ${
                              blocker.tone === "red" ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-900"
                            }`}
                          >
                            {blocker.text}
                          </p>
                        )}
                      </div>
                      {item.sourceUrl && (
                        <a
                          href={item.sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex shrink-0 items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-sm text-brand hover:bg-brand-soft"
                        >
                          Avots
                          <ArrowRightIcon size={13} className="-rotate-45" />
                        </a>
                      )}
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>
      )}
    </main>
  );
}
