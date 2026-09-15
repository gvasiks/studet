// Список избранного — только в localStorage браузера, ничего не уходит на
// сервер и не требует регистрации (тот же принцип, что и у анкеты: "нигде
// не сохраняется", только тут "нигде" означает "нигде, кроме этого
// браузера"). Храним id программы (uuid) — так страница /favorites может
// получить все карточки одним запросом by id, без сборки OR-фильтра по
// парам (university slug, programme slug).

const STORAGE_KEY = "studet:favorites";
// Свой event, а не "storage" — "storage" не срабатывает во вкладке,
// которая сама изменила localStorage, только в остальных. Кнопки на одной
// странице (список каталога) должны видеть изменения друг друга сразу.
const CHANGE_EVENT = "studet:favorites-changed";

function readIds(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === "string") : [];
  } catch {
    // Приватный режим, заполненное хранилище, битый JSON — в любом из
    // этих случаев просто считаем, что избранного нет, а не падаем.
    return [];
  }
}

function writeIds(ids: string[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  } catch {
    // Хранилище недоступно (приватный режим Safari и т.п.) — тихо
    // игнорируем, кнопка просто не запомнит выбор до перезагрузки.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function getFavoriteIds(): string[] {
  return readIds();
}

export function isFavorite(programmeId: string): boolean {
  return readIds().includes(programmeId);
}

export function toggleFavorite(programmeId: string): boolean {
  const ids = readIds();
  const index = ids.indexOf(programmeId);
  if (index === -1) {
    writeIds([...ids, programmeId]);
    return true;
  }
  writeIds([...ids.slice(0, index), ...ids.slice(index + 1)]);
  return false;
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
