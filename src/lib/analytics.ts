// Счётчик посещений: что именно уходит в PostHog. Чистые функции без
// обращения к сети — читаются и тестами. Отправка — в
// src/components/Analytics.tsx.
//
// Библиотеки PostHog в проекте нет намеренно: она весит около 100 КБ в
// сжатом виде и по умолчанию сама собирает клики и содержимое страницы.
// Здесь уходит только то, что перечислено в pageviewEvent, — политика
// конфиденциальности (раздел «Naudojimo statistika» / «Usage statistics»)
// обещает ровно это: без cookies, без хранения в браузере, без содержимого
// полей ввода, без записи сессий.
//
// Формат запроса — документация PostHog, «Capture API»:
// https://posthog.com/docs/api/capture

// Серверы PostHog в Европейском союзе. Не менять на us.i.posthog.com:
// политика обещает обработку в ЕС.
export const CAPTURE_URL = "https://eu.i.posthog.com/i/v0/e/";

/**
 * Адрес без параметров и якоря. В параметрах каталога стоят текст поиска и
 * ответы анкеты (интересы, город) — в аналитику они не идут
 * (docs/ANALYTICS-PLAN.md, «Что НЕ собираем»). Нечитаемый адрес — пустая строка.
 */
export function withoutQuery(href: string): string {
  try {
    const url = new URL(href);
    return url.origin + url.pathname;
  } catch {
    return "";
  }
}

/**
 * Идентификатор UUID версии 7 (первые 48 бит — время, остальное случайно):
 * в таком виде PostHog ждёт номер визита. `random` — 10 случайных байт.
 */
export function uuidv7(now: number, random: Uint8Array): string {
  const time = Math.floor(now).toString(16).padStart(12, "0").slice(-12);
  const hex = [...random].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  // 4 бита версии (7) и 2 бита варианта (10) стоят на своих местах по RFC 9562
  const variant = ((random[9] & 0x3) | 0x8).toString(16);
  return `${time.slice(0, 8)}-${time.slice(8)}-7${hex.slice(0, 3)}-${variant}${hex.slice(3, 6)}-${hex.slice(6, 18)}`;
}

export type Visit = {
  /** Случайный номер посетителя: живёт в памяти вкладки, после перезагрузки новый. */
  distinctId: string;
  /** Номер визита — у нас то же время жизни, что у номера посетителя. */
  sessionId: string;
};

/** Одно событие «просмотр страницы» — всё, что о нём узнаёт PostHog. */
export function pageviewEvent(key: string, visit: Visit, href: string, referrer: string) {
  const page = new URL(href);
  const cameFrom = withoutQuery(referrer);
  return {
    api_key: key,
    event: "$pageview",
    distinct_id: visit.distinctId,
    properties: {
      $current_url: withoutQuery(href),
      $host: page.host,
      $pathname: page.pathname,
      // "$direct" — так PostHog обозначает заход без источника
      $referrer: cameFrom || "$direct",
      $referring_domain: cameFrom ? new URL(cameFrom).hostname : "$direct",
      $session_id: visit.sessionId,
      // событие без профиля человека: PostHog не заводит на посетителя запись
      $process_person_profile: false,
      $lib: "studypick-web",
    },
  };
}

/**
 * Считать ли посещение. Только рабочий сайт: при разработке и на localhost
 * (в том числе рабочая сборка, запущенная у себя) события не уходят — иначе
 * свои же проверки попадали бы в число посетителей.
 */
export function shouldCount(key: string | undefined, nodeEnv: string | undefined, hostname: string): key is string {
  if (!key || nodeEnv !== "production") return false;
  return hostname !== "localhost" && hostname !== "127.0.0.1" && hostname !== "[::1]" && !hostname.endsWith(".localhost");
}
