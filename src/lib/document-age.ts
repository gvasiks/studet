// Возраст документа-источника формулы (план работ, неделя 3). Правила
// приёма меняются каждый год, поэтому формула, взятая из документа старше
// года, — кандидат на пересев, а не на подтверждение: подтверждённая
// формула прошлого года хуже неподтверждённой, потому что выглядит верной.
// Чистая функция без обращений к базе — чтобы тестироваться отдельно.

export const STALE_AFTER_DAYS = 365;

export function documentAgeDays(documentDate: string, now: Date = new Date()): number {
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  return Math.floor((now.getTime() - new Date(documentDate).getTime()) / millisecondsPerDay);
}

export function isDocumentStale(documentDate: string | null, now: Date = new Date()): boolean {
  return documentDate !== null && documentAgeDays(documentDate, now) > STALE_AFTER_DAYS;
}
