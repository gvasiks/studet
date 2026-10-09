"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { CAPTURE_URL, pageviewEvent, shouldCount, uuidv7, type Visit } from "@/lib/analytics";

// Счётчик посещений: одно событие «просмотр страницы» при открытии сайта и
// при каждом переходе между страницами. Что именно уходит и почему без
// библиотеки PostHog — src/lib/analytics.ts.
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

export function Analytics() {
  const pathname = usePathname();

  useEffect(() => {
    const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
    if (!shouldCount(key, process.env.NODE_ENV, window.location.hostname)) return;
    const body = JSON.stringify(pageviewEvent(key, currentVisit(), window.location.href, document.referrer));
    // keepalive — чтобы запрос дошёл, даже если человек сразу ушёл со страницы.
    // Ошибку глотаем: недоступная аналитика не должна мешать сайту.
    fetch(CAPTURE_URL, { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true }).catch(() => {});
  }, [pathname]);

  return null;
}
