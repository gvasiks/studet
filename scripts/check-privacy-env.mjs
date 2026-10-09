// План 2026-09-21, пункт 12: "сайт не публикуется, пока в политике есть
// раздел про то, чего нет, или не задано имя оператора" (правило проекта,
// docs/PRIVACY-CHECKLIST.md, раздел 1). Без PRIVACY_CONTROLLER_NAME и
// PRIVACY_CONTACT_EMAIL страница /privacy показывает плейсхолдер
// "[PRIVACY_CONTROLLER_NAME]" вместо настоящего оператора данных —
// лучше сломанная сборка, чем опубликованная страница с этим текстом.
//
// Флаг PRIVACY_ENFORCE=1, а не автоопределение "это прод": хостинг ещё
// не выбран (CLAUDE.md), а многие площадки (Vercel, Netlify) сами ставят
// CI=1 на своих сборках — на CI/NODE_ENV полагаться нельзя, будет либо
// ложное срабатывание в обычном CI, либо тишина на настоящем деплое.
// Явный флаг предсказуем при любом хостинге: владелец включает его ОДИН
// раз в настройках окружения выбранного хостинга, рядом с двумя
// переменными оператора — см. docs/PRIVACY-CHECKLIST.md, раздел 4.
// Счётчик посещений (src/components/Analytics.tsx) включается ключом
// NEXT_PUBLIC_POSTHOG_KEY. Правило проекта — аналитика только после того,
// как опубликована политика с настоящим оператором данных, — здесь проверяется
// без флага: ключ аналитики сам говорит, что сборка идёт на публикацию.
// Локальной сборке это не мешает: .env.local этот скрипт не читает, он видит
// только переменные окружения самой площадки.
if (process.env.NEXT_PUBLIC_POSTHOG_KEY) {
  const missing = ["PRIVACY_CONTROLLER_NAME", "PRIVACY_CONTACT_EMAIL"].filter(
    (name) => !process.env[name],
  );
  if (missing.length > 0) {
    console.error(
      `Сборка остановлена: задан ключ аналитики NEXT_PUBLIC_POSTHOG_KEY, но не заданы ${missing.join(", ")}. ` +
        "Счётчик посещений нельзя включать, пока в политике нет оператора данных. " +
        "См. docs/PRIVACY-CHECKLIST.md, раздел 1.",
    );
    process.exit(1);
  }
}

if (process.env.PRIVACY_ENFORCE === "1") {
  const missing = ["PRIVACY_CONTROLLER_NAME", "PRIVACY_CONTACT_EMAIL"].filter(
    (name) => !process.env[name],
  );
  if (missing.length > 0) {
    console.error(
      `Сборка остановлена (PRIVACY_ENFORCE=1): не заданы ${missing.join(", ")}. ` +
        "См. docs/PRIVACY-CHECKLIST.md, раздел 1.",
    );
    process.exit(1);
  }
}
