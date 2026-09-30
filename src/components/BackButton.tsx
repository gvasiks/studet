"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { MouseEvent } from "react";
import { ArrowLeftIcon } from "@/components/icons";

// Был ли в этой вкладке предыдущий экран нашего же сайта.
// Navigation API видит только записи истории своего сайта, поэтому
// index > 0 значит «до этой страницы человек был у нас» — а не пришёл
// из поиска. Где API нет (старые браузеры), смотрим на document.referrer:
// он не обновляется при переходах внутри Next.js, так что в худшем случае
// кнопка просто поведёт по обычной ссылке.
function cameFromThisSite(): boolean {
  const nav = (window as { navigation?: { currentEntry?: { index: number } | null } }).navigation;
  if (nav?.currentEntry) return nav.currentEntry.index > 0;
  return document.referrer.startsWith(window.location.origin);
}

// Кнопка «← Назад». Это обычная ссылка на fallbackHref — работает и без
// JavaScript, и для пришедших из поиска. Если человек пришёл с другой
// страницы сайта, возвращаем его туда же через историю браузера: так
// сохраняются фильтры каталога и результаты /match, чего ссылка на
// fallbackHref не умеет.
export function BackButton({ fallbackHref, label }: { fallbackHref: string; label: string }) {
  const router = useRouter();

  function handleClick(event: MouseEvent<HTMLAnchorElement>) {
    // Ctrl/Cmd/Shift-клик — человек хочет новую вкладку, не мешаем.
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
    if (!cameFromThisSite()) return;
    event.preventDefault();
    router.back();
  }

  return (
    <Link
      href={fallbackHref}
      onClick={handleClick}
      className="inline-flex h-9 items-center gap-1.5 rounded-full border border-zinc-200 bg-white px-3.5 text-sm font-medium text-zinc-700 hover:border-zinc-300 hover:text-zinc-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
    >
      <ArrowLeftIcon size={15} />
      {label}
    </Link>
  );
}
