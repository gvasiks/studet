// Список избранного хранится только в localStorage браузера и не требует
// регистрации: у нас он нигде не сохраняется. Но «никуда не уходит» сказать
// нельзя: чтобы показать карточки, страница /favorites запрашивает эти
// программы у базы по id (getProgrammesByIds в catalog.ts), и запрос, как
// любое посещение, попадает в технические журналы провайдера. Тексты на
// странице и в политике конфиденциальности говорят именно так (аудит
// 2026-10-04, пункт 5) — не возвращай в них «никуда не отправляется».
// Храним id программы (uuid) — так все карточки приходят одним запросом,
// без сборки OR-фильтра по парам (university slug, programme slug).

import type { Country } from "@/i18n/config";

// Хранится список по странам (свой ключ у каждой): по стране программы
// страница списка знает, в каком разделе лежит её карточка. А показывается
// он общим — и на странице «Мой список», и в счётчике в шапке — для всех
// открытых стран сразу: каталог по умолчанию тоже общий (решение владельца
// 2026-10-10), и звезда на литовской программе в латвийском разделе не
// должна уходить в список, которого отсюда не видно. Пока Литва закрыта,
// её программы не показываются и не считаются. У Латвии ключ прежний, без
// суффикса, — списки, сохранённые до появления второй страны, не теряются.
function storageKey(country: Country): string {
  return country === "LV" ? "studet:favorites" : `studet:favorites:${country.toLowerCase()}`;
}
// Свой event, а не "storage" — "storage" не срабатывает во вкладке,
// которая сама изменила localStorage, только в остальных. Кнопки на одной
// странице (список каталога) должны видеть изменения друг друга сразу.
const CHANGE_EVENT = "studet:favorites-changed";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function readIds(country: Country): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(storageKey(country));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    // Только id вида UUID: строка вроде «abc» прошла бы проверку «это строка»,
    // и запрос к базе по такому id падал бы целиком — страница списка
    // оставалась пустой без объяснений (аудит 2026-10-04).
    return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === "string" && UUID.test(id)) : [];
  } catch {
    // Приватный режим, заполненное хранилище, битый JSON — в любом из
    // этих случаев просто считаем, что избранного нет, а не падаем.
    return [];
  }
}

function writeIds(country: Country, ids: string[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(storageKey(country), JSON.stringify(ids));
  } catch {
    // Хранилище недоступно (приватный режим Safari и т.п.) — тихо
    // игнорируем, кнопка просто не запомнит выбор до перезагрузки.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function getFavoriteIds(country: Country): string[] {
  return readIds(country);
}

export function isFavorite(country: Country, programmeId: string): boolean {
  return readIds(country).includes(programmeId);
}

export function toggleFavorite(country: Country, programmeId: string): boolean {
  const ids = readIds(country);
  const index = ids.indexOf(programmeId);
  if (index === -1) {
    writeIds(country, [...ids, programmeId]);
    return true;
  }
  writeIds(country, [...ids.slice(0, index), ...ids.slice(index + 1)]);
  return false;
}

/**
 * Оставить в списке страны только эти id — тех программ, которые база ещё
 * показывает. Скрытая или удалённая из каталога программа иначе навсегда
 * оставалась бы в счётчике шапки, а убрать её со страницы было нельзя: её
 * карточки больше нет (аудит 2026-10-04). Возвращает, было ли что убрать.
 */
export function keepOnlyFavorites(country: Country, available: readonly string[]): boolean {
  const ids = readIds(country);
  const kept = ids.filter((id) => available.includes(id));
  if (kept.length === ids.length) return false;
  writeIds(country, kept);
  return true;
}

export function subscribeToFavorites(callback: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(CHANGE_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(CHANGE_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}
