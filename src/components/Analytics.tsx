"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { useReportWebVitals } from "next/web-vitals";
import {
  CAPTURE_URL,
  isTrackedVital,
  pageviewEvent,
  productEvent,
  shouldCount,
  uuidv7,
  webVitalEvent,
  type ProductEvent,
  type Visit,
  type WebVital,
} from "@/lib/analytics";

// Счётчик посещений: одно событие «просмотр страницы» при открытии сайта и
// при каждом переходе между страницами, плюс три события о том, что анкетой,
// калькулятором и обратным поиском пользуются до конца, и скорость страницы
// у посетителя (Core Web Vitals). Что именно уходит и
// почему без библиотеки PostHog — src/lib/analytics.ts.
//
// Клиентский компонент, но ничего не рисует и стоит один раз в корневой
// раскладке: публичные страницы остаются серверными (правило 4 CLAUDE.md).

// Номер визита живёт в памяти вкладки: ни cookie, ни localStorage. Переход
// между страницами сайта его сохраняет, перезагрузка или новая вкладка —
// нет. Поэтому «уникальные посетители» в отчётах — это визиты, а не люди.
let visit: Visit | null = null;

function currentVisit(): Visit {
  if (!visit) {
    const id = () => uuidv7(Date.now(), crypto.getRandomValues(new Uint8Array(10)));
    visit = { distinctId: id(), sessionId: id() };
  }
  return visit;
}

// Только рабочий сайт (shouldCount). keepalive — чтобы запрос дошёл, даже если
// человек сразу ушёл со страницы. Ошибку глотаем: недоступная аналитика не
// должна мешать сайту.
function send(event: (key: string, visit: Visit) => object) {
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!shouldCount(key, process.env.NODE_ENV, window.location.hostname)) return;
  const body = JSON.stringify(event(key, currentVisit()));
  fetch(CAPTURE_URL, { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true }).catch(() => {});
}

/** Событие функции — например, перед переходом из анкеты в каталог. */
export function track(name: ProductEvent) {
  send((key, current) => productEvent(key, current, name, window.location.href));
}

/**
 * Отправить событие один раз за показ страницы, когда условие впервые стало
 * верным (балл посчитан, список не пуст). Человек, который меняет оценки и
 * видит новый балл, событие повторно не шлёт; после перехода на другую
 * страницу и обратно — шлёт снова.
 */
export function useTrackOnce(name: ProductEvent, happened: boolean) {
  const sent = useRef(false);
  useEffect(() => {
    if (happened && !sent.current) {
      sent.current = true;
      track(name);
    }
  }, [happened, name]);
}

// Скорость страницы: Next.js сообщает замеры сам (LCP — после загрузки,
// INP и CLS — когда человек уходит со страницы). Функция вне компонента —
// так советует документация Next.js, иначе замеры могут прийти дважды.
function reportVital(metric: WebVital) {
  if (!isTrackedVital(metric)) return;
  send((key, current) => webVitalEvent(key, current, metric, window.location.href));
}

export function Analytics() {
  const pathname = usePathname();
  useReportWebVitals(reportVital);

  useEffect(() => {
    send((key, current) => pageviewEvent(key, current, window.location.href, document.referrer));
  }, [pathname]);

  return null;
}
