"use client";

import { useEffect, useRef, type FormEvent, type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

// Сколько ждать после последней буквы в поиске, прежде чем обновить список.
const SEARCH_DELAY_MS = 400;

// Обёртка формы каталога. Сами поля по-прежнему рисует сервер
// (CatalogControls.tsx), здесь только два поведения:
//
// 1. Фильтр применяется сразу при изменении — без кнопки «Lietot».
//    Форма превращается в адрес страницы (?city=…&language=…), и сервер
//    отдаёт новый список. Поиск — с паузой SEARCH_DELAY_MS.
// 2. Поля всегда совпадают с адресом страницы. Без этого «Notīrīt» не
//    работал: переход внутри Next.js не пересоздаёт поля, и галочки
//    оставались стоять, хотя список уже был без фильтров. То же при
//    кнопках браузера «назад/вперёд».
//
// Без JavaScript форма работает как раньше: обычный GET по кнопке
// (кнопка — в <noscript>, см. FilterSidebar).
export function CatalogForm({
  action,
  className,
  children,
}: {
  action: string;
  className?: string;
  children: ReactNode;
}) {
  const formRef = useRef<HTMLFormElement>(null);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function apply() {
    const form = formRef.current;
    if (!form) return;
    const params = new URLSearchParams();
    for (const [name, value] of new FormData(form)) {
      // Пустые значения («любой вуз», пустой поиск) в адрес не пишем —
      // так же, как catalogQuery() в lib/catalog-query.ts.
      if (typeof value === "string" && value.trim() !== "") params.append(name, value.trim());
    }
    const query = params.toString();
    // replace, а не push: иначе каждая галочка — отдельный шаг «назад».
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  function handleChange(event: FormEvent<HTMLFormElement>) {
    const target = event.target as HTMLInputElement;
    // Переключатель панели фильтров на телефоне — без name, это не фильтр.
    if (!target.name) return;
    if (searchTimer.current) clearTimeout(searchTimer.current);
    if (target.type === "search") {
      searchTimer.current = setTimeout(apply, SEARCH_DELAY_MS);
    } else {
      apply();
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    // Enter в поиске — применить сразу, без перезагрузки страницы.
    event.preventDefault();
    if (searchTimer.current) clearTimeout(searchTimer.current);
    apply();
  }

  useEffect(() => {
    const form = formRef.current;
    if (!form) return;
    // Города и интересы в адресе бывают и через запятую (ссылка из анкеты).
    const listValues = (name: string) => searchParams.getAll(name).flatMap((value) => value.split(","));

    for (const element of Array.from(form.elements)) {
      if (element instanceof HTMLInputElement && element.name) {
        if (element.type === "checkbox") {
          element.checked = listValues(element.name).includes(element.value);
        } else if (element.type === "search" && element !== document.activeElement) {
          // Поле, в котором человек сейчас печатает, не трогаем — иначе
          // запоздавший ответ сервера сотрёт только что набранные буквы.
          element.value = searchParams.get(element.name) ?? "";
        }
      } else if (element instanceof HTMLSelectElement) {
        element.value = searchParams.get(element.name) ?? "";
      }
    }
  }, [searchParams]);

  useEffect(() => () => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
  }, []);

  return (
    <form ref={formRef} method="get" action={action} onChange={handleChange} onSubmit={handleSubmit} className={className}>
      {children}
    </form>
  );
}
