"use client";

import { useRef, useState } from "react";
import { interpolate } from "@/lib/outcomes";

// Страницы внутри групп «Prasību pārbaude» (комментарий #19 к гиду
// тестирования): «Atbilst prasībām» бывает в 250 программ, длинный список
// целиком было не пролистать. По 20 программ на страницу, всё на клиенте:
// адрес не меняется — экзамены в него попасть не могут.
export const PAGE_SIZE = 20;
const PAGE_KEY_PREFIX = "studet:match-page:";

// Номер страницы группы помнит вкладка (sessionStorage), как и экзамены:
// открыл программу с 3-й страницы, вернулся — снова 3-я. Это не экзамены,
// а только номер страницы, но живёт он там же и так же недолго.
function readPage(storageKey: string): number {
  try {
    const value = Number(window.sessionStorage.getItem(storageKey));
    return Number.isInteger(value) && value > 0 ? value : 1;
  } catch {
    return 1;
  }
}

function writePage(storageKey: string, page: number): void {
  try {
    if (page === 1) window.sessionStorage.removeItem(storageKey);
    else window.sessionStorage.setItem(storageKey, String(page));
  } catch {
    // хранилище недоступно — страница просто не запомнится
  }
}

// «Notīrīt rezultātus» стирает и номера страниц: новые экзамены — новый
// список, начинать его с 13-й страницы прошлого было бы странно.
export function clearMatchPages(): void {
  try {
    for (const key of Object.keys(window.sessionStorage)) {
      if (key.startsWith(PAGE_KEY_PREFIX)) window.sessionStorage.removeItem(key);
    }
  } catch {
    // хранилище недоступно — и запоминать было нечего
  }
}

// Группы появляются только после того, как экзамены прочитаны из вкладки, то
// есть уже в браузере, — поэтому начальная страница читается сразу, без
// расхождения с серверной разметкой.
export function useMatchPage<T>(groupId: string, items: T[]) {
  const storageKey = `${PAGE_KEY_PREFIX}${groupId}`;
  const [requested, setRequested] = useState(() => readPage(storageKey));
  const pageCount = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  // Экзамены поменялись, группа стала короче — последняя существующая страница
  const page = Math.min(requested, pageCount);
  const pageItems = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  // Заголовок группы: после смены страницы фокус и прокрутка переходят к
  // нему, иначе человек остался бы внизу, у кнопок, перед концом нового списка.
  const headingRef = useRef<HTMLHeadingElement>(null);

  function setPage(next: number) {
    setRequested(next);
    writePage(storageKey, next);
    headingRef.current?.scrollIntoView({ block: "start" });
    headingRef.current?.focus({ preventScroll: true });
  }

  return { page, pageCount, pageItems, setPage, headingRef };
}

export type PagerText = { label: string; previous: string; next: string; status: string };

export function MatchPager({
  page,
  pageCount,
  onChange,
  text,
  groupTitle,
}: {
  page: number;
  pageCount: number;
  onChange: (page: number) => void;
  text: PagerText;
  groupTitle: string;
}) {
  if (pageCount <= 1) return null;
  const button =
    "inline-flex h-9 shrink-0 items-center rounded-full border border-zinc-300 px-3 text-sm sm:px-4 font-medium text-zinc-800 hover:bg-zinc-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent";
  return (
    <nav
      aria-label={`${text.label}: ${groupTitle}`}
      className="flex items-center justify-between gap-2 border-t border-zinc-100 px-6 py-4 sm:px-8"
    >
      <button type="button" className={button} disabled={page === 1} onClick={() => onChange(page - 1)}>
        {text.previous}
      </button>
      <span className="min-w-0 text-center text-sm tabular-nums text-zinc-600">
        {interpolate(text.status, { page, total: pageCount })}
      </span>
      <button type="button" className={button} disabled={page === pageCount} onClick={() => onChange(page + 1)}>
        {text.next}
      </button>
    </nav>
  );
}
