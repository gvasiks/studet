# Studet

Веб-сервис для выбора вуза в Латвии. Подробности — в [`CLAUDE.md`](./CLAUDE.md)
и [`docs/PLAN.md`](./docs/PLAN.md).

## Команды

```
npm run dev      # локальный сервер, http://localhost:3000
npm run build    # прод-сборка
npm run lint     # проверка кода
```

## Стек

Next.js (App Router) · HeroUI v2 · Tailwind v4 · Supabase (позже) · TypeScript

## Многоязычность

Маршруты `/lv` и `/en`. `/` редиректит на язык браузера через `src/proxy.ts`.
Тексты — в `src/i18n/dictionaries/*.json`, в коде строк нет.
