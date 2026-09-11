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

Next.js (App Router) · HeroUI v2 · Tailwind v4 · Supabase · TypeScript

## Многоязычность

Маршруты `/lv` и `/en`. `/` редиректит на язык браузера через `src/proxy.ts`.
Тексты — в `src/i18n/dictionaries/*.json`, в коде строк нет.

## Supabase

Проект в регионе ЕС (Frankfurt). Клиент — `src/lib/supabase.ts`, читает
`NEXT_PUBLIC_SUPABASE_URL` и `NEXT_PUBLIC_SUPABASE_ANON_KEY` (anon/publishable
key — публичный, ограничения через RLS-политики на каждой таблице).
Сервисный ключ сюда не попадает — он только в окружении Python-конвейера.

1. Скопируйте `.env.local.example` → `.env.local`, заполните значениями
   из дэшборда проекта: Settings → API.
2. Схема хранится как SQL-миграции в `supabase/migrations/` (появятся
   в следующем коммите вместе с таблицами каталога).
3. Разработка — только в облаке, без локального Docker-стека (осознанный
   компромисс при 5 ч/нед: проще, но нет изолированной локальной песочницы).
4. Одноразово перед первым `supabase db push`: `npx supabase login`,
   затем `npx supabase link --project-ref <ref-из-URL-проекта>`
   (это интерактивный вход через браузер — сделайте сами в своём терминале).
