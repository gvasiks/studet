// Память серверного процесса для данных, которые меняются редко, а читаются
// при каждом показе страницы.
//
// Зачем. Каталог при каждом открытии и при каждом щелчке по фильтру заново
// скачивал из базы весь список программ — полтора мегабайта ради двенадцати
// карточек (замер 2026-10-11). Данные при этом меняются раз в неделю, после
// сбора. Здесь список скачивается один раз и живёт в памяти ttlMs.
//
// Как работает remember(key, ttlMs, load):
// - значения нет — выполняется load(), все одновременные вызовы ждут его же;
// - значение свежее — отдаётся сразу, без обращения к базе;
// - срок вышел — прежнее значение отдаётся СРАЗУ, а load() идёт в фоне:
//   посетитель не ждёт обновления, следующий получит новое;
// - обновление упало — остаётся прежнее значение, повтор через RETRY_AFTER_MS:
//   сбой базы не роняет каталог.
//
// Чем платим: изменение в базе (сбор данных, подтверждение в Studio) видно
// на таких страницах не сразу, а в течение ttlMs.
//
// Память живёт, пока жив процесс сайта: служба на сервере — один процесс
// (deploy/studypick.service), перезапуск при обновлении её очищает.
//
// ВАЖНО: значение одно на все запросы. Не меняй то, что вернул remember()
// (не сортируй массив на месте, не дописывай поля) — отдавай копию.

type Entry = {
  value: unknown;
  /** Когда значение пора обновлять. */
  staleAt: number;
  /** Идёт фоновое обновление. */
  refreshing: boolean;
};

const RETRY_AFTER_MS = 30_000;

const entries = new Map<string, Entry>();
const firstLoads = new Map<string, Promise<unknown>>();

export function remember<T>(
  key: string,
  ttlMs: number,
  load: () => Promise<T>,
  now: () => number = Date.now,
): Promise<T> {
  const entry = entries.get(key);
  if (entry) {
    if (now() >= entry.staleAt && !entry.refreshing) {
      entry.refreshing = true;
      load()
        .then((value) => {
          entries.set(key, { value, staleAt: now() + ttlMs, refreshing: false });
        })
        .catch((error) => {
          console.error(`remember("${key}"): обновить не удалось, остаётся прежнее значение`, error);
          entry.staleAt = now() + RETRY_AFTER_MS;
          entry.refreshing = false;
        });
    }
    return Promise.resolve(entry.value as T);
  }

  // Первая загрузка: значение ещё нечем заменить, поэтому ошибка уходит
  // вызывающему, а в память ничего не кладётся — следующий запрос попробует снова.
  let pending = firstLoads.get(key) as Promise<T> | undefined;
  if (!pending) {
    pending = load()
      .then((value) => {
        entries.set(key, { value, staleAt: now() + ttlMs, refreshing: false });
        return value;
      })
      .finally(() => {
        firstLoads.delete(key);
      });
    firstLoads.set(key, pending);
  }
  return pending;
}

/** Забыть всё — для тестов. */
export function forgetEverything(): void {
  entries.clear();
  firstLoads.clear();
}
