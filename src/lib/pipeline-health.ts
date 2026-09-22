// Свежесть последнего сбора каталога — план 2026-09-21, неделя 1, пункт 08.
// Чистая логика без обращений к базе (тот же приём, что formula.ts /
// formula-queries.ts) — чтобы тестировать без клиента Supabase. Сам запрос —
// в pipeline-health-queries.ts.

export type PipelineHealth = {
  lastSuccessAt: string | null;
  lastStatus: "running" | "success" | "failed" | null;
  lastFinishedAt: string | null;
  lastErrorCount: number | null;
};

// Сбор — раз в неделю; порог такой же, как в pipeline/src/check_pipeline_health.py
// (день запаса на повторную попытку) — держите оба числа одинаковыми.
export const PIPELINE_STALE_AFTER_DAYS = 9;

export function isPipelineStale(lastSuccessAt: string | null, now: Date = new Date()): boolean {
  if (lastSuccessAt === null) return true;
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  const days = Math.floor((now.getTime() - new Date(lastSuccessAt).getTime()) / millisecondsPerDay);
  return days > PIPELINE_STALE_AFTER_DAYS;
}
