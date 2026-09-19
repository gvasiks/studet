"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { locales, type Locale } from "@/i18n/config";

// Нужен usePathname(), чтобы при переключении языка остаться на той же
// странице (та же programme/university slug работает под обоими локалями,
// менять нужно только первый сегмент пути). Серверный компонент этого не
// умеет без прокидывания текущего пути через каждую страницу.
//
// Ссылки, а не кнопки: переключатель языка — это навигация (другой
// адрес, другой индексируемый документ), не действие на странице.
export function LocaleSwitcher({ locale }: { locale: Locale }) {
  const pathname = usePathname();
  const rest = pathname.split("/").slice(2).join("/");

  return (
    <nav aria-label="Language" className="flex items-center rounded-full bg-zinc-200 p-[3px]">
      {locales.map((code) => (
        <Link
          key={code}
          href={`/${code}${rest ? `/${rest}` : ""}`}
          aria-current={code === locale ? "page" : undefined}
          className={
            code === locale
              ? "inline-flex h-[30px] items-center rounded-full bg-white px-3.5 text-[13px] font-semibold text-zinc-900 shadow-pill"
              : "inline-flex h-[30px] items-center rounded-full px-3.5 text-[13px] font-medium text-zinc-600 hover:text-zinc-900"
          }
        >
          {code.toUpperCase()}
        </Link>
      ))}
    </nav>
  );
}
