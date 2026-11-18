import type { NextConfig } from "next";

// Защитные заголовки на все ответы (аудит 2026-10-04, OWASP A02 — ошибки
// настройки). Без них страницы с вводом результатов экзаменов можно было
// встроить в чужой сайт во фрейме.
//
// Content-Security-Policy запрещает встраивание (frame-ancestors), плагины,
// подмену базового адреса и отправку форм на чужие адреса. С 2026-11-18
// (проверка безопасности 2026-11-16, находка 2) она ещё и ограничивает, откуда
// берутся скрипты, стили, картинки, шрифты и куда страница может отправлять
// запросы: только свой сайт, плюс сервер аналитики PostHog в ЕС
// (src/lib/analytics.ts) и база Supabase. Чужой скрипт или отправка данных на чужой адрес
// браузер теперь заблокирует.
//
// 'unsafe-inline' у скриптов остаётся: Next.js вставляет в страницу свои
// встроенные скрипты, и без одноразового ключа (nonce) на каждый ответ их не
// отличить от чужих. Nonce убирает статическую отдачу страниц — для сайта без
// входа и без чужих скриптов цена выше пользы. У стилей 'unsafe-inline' нужен
// HeroUI и анимациям (style="…"). 'unsafe-eval' — только в `next dev`: без него
// не работает горячая перезагрузка.
//
// Новый внешний адрес (картинка, шрифт, сервис) — сначала сюда, иначе браузер
// его не загрузит; e2e/keyboard.spec.ts ловит нарушения политики на главных
// страницах.
//
// HSTS: браузер запоминает, что сайт открывается только по HTTPS (Caddy сам
// получает сертификат, deploy/README.md). Без preload — его потом трудно
// отменить. По HTTP на localhost браузеры заголовок не учитывают.
const isDev = process.env.NODE_ENV === "development";

// «Сохранённые программы» читают список из базы прямо из браузера
// (getProgrammesByIds в src/lib/catalog.ts, публичным ключом) — адрес базы
// должен быть разрешён. Берётся из того же NEXT_PUBLIC_SUPABASE_URL, что и
// для сайта; без него сборка всё равно не пройдёт (src/lib/supabase.ts).
function originOf(url: string | undefined): string {
  try {
    return url ? new URL(url).origin : "";
  } catch {
    return "";
  }
}
const supabaseOrigin = originOf(process.env.NEXT_PUBLIC_SUPABASE_URL);

const contentSecurityPolicy = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  // data: и blob: — размытая заглушка картинки next/image и иконки HeroUI
  "img-src 'self' data: blob:",
  // шрифт Inter next/font отдаёт со своего сайта
  "font-src 'self'",
  `connect-src 'self' https://eu.i.posthog.com${supabaseOrigin ? ` ${supabaseOrigin}` : ""}`,
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "object-src 'none'",
  "form-action 'self'",
].join("; ");

const securityHeaders = [
  { key: "Content-Security-Policy", value: contentSecurityPolicy },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()" },
  { key: "Strict-Transport-Security", value: "max-age=31536000" },
];

const nextConfig: NextConfig = {
  // заголовок «X-Powered-By: Next.js» лишь подсказывает, чем сайт сделан
  poweredByHeader: false,
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
