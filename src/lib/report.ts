// Ссылка «здесь ошибка» на карточке программы и в калькуляторе (план, пункт
// Д4): обычный mailto, без бэкенда и без JavaScript. Без импортов — модуль
// читается и тестами (vitest не понимает алиас "@/").

// Куда писать об ошибках. FEEDBACK_EMAIL — отдельный ящик, если он заведён;
// иначе тот же адрес, что на странице /privacy. Пока не задан ни один,
// ссылка не выводится совсем: битый mailto хуже, чем его отсутствие.
export function getReportEmail(env: Record<string, string | undefined> = process.env): string | null {
  const email = (env.FEEDBACK_EMAIL || env.PRIVACY_CONTACT_EMAIL || "").trim();
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? email : null;
}

// Тема и текст письма кодируются целиком; перенос строки в mailto по
// RFC 6068 — %0D%0A. В текст попадает только то, что передали: адрес
// страницы и подсказки, что написать. Результаты экзаменов сюда не
// передаются никогда (правило проекта: они не покидают браузер).
export function buildReportMailto(email: string, subject: string, body: string): string {
  const encodedBody = encodeURIComponent(body.replace(/\r?\n/g, "\r\n"));
  return `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodedBody}`;
}
