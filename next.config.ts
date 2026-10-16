import type { NextConfig } from "next";

// Защитные заголовки на все ответы (аудит 2026-10-04, OWASP A02 — ошибки
// настройки). Без них страницы с вводом результатов экзаменов можно было
// встроить в чужой сайт во фрейме.
//
// Content-Security-Policy — осторожная: запрещает встраивание (frame-ancestors),
// плагины, подмену базового адреса и отправку форм на чужие адреса, но не
// ограничивает скрипты и стили. Строгая политика скриптов в Next.js требует
// одноразового ключа (nonce) на каждый ответ, а это убирает статическую
// отдачу страниц — для сайта без входа и без чужих скриптов цена выше пользы.
//
// HSTS: браузер запоминает, что сайт открывается только по HTTPS (Caddy сам
// получает сертификат, deploy/README.md). Без preload — его потом трудно
// отменить. По HTTP на localhost браузеры заголовок не учитывают.
const securityHeaders = [
  {
    key: "Content-Security-Policy",
    value: "frame-ancestors 'none'; base-uri 'self'; object-src 'none'; form-action 'self'",
  },
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
