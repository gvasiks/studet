"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { locales, type Locale } from "@/i18n/config";

// Единственный клиентский компонент в шапке — нужен usePathname(), чтобы
// при переключении языка остаться на той же странице (та же programme/
// university slug работает под обоими локалями, менять нужно только
// первый сегмент пути). Серверный компонент этого не умеет без
// прокидывания текущего пути через каждую страницу.
export function LocaleSwitcher({ locale }: { locale: Locale }) {
  const pathname = usePathname();
  const rest = pathname.split("/").slice(2).join("/");

  return (
    <nav className="flex items-center gap-1 text-sm font-medium" aria-label="Language">
      {locales.map((code) => (
        <Link
          key={code}
          href={`/${code}${rest ? `/${rest}` : ""}`}
          aria-current={code === locale ? "page" : undefined}
          className={
            code === locale
              ? "rounded-full bg-zinc-900 px-3 py-1 text-white"
              : "rounded-full px-3 py-1 text-zinc-500 hover:text-zinc-900"
          }
        >
          {code.toUpperCase()}
        </Link>
      ))}
    </nav>
  );
}
