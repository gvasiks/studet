# Studet

Веб-сервис для выбора вуза в Латвии. Полное описание проекта —
в [`docs/PROJECT.md`](./docs/PROJECT.md); краткий обзор —
в [`docs/OVERVIEW.md`](./docs/OVERVIEW.md); рабочие правила и решения
бизнес-анализа — в [`CLAUDE.md`](./CLAUDE.md); исходный детальный план
— в [`docs/PLAN.md`](./docs/PLAN.md).

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

Проект в регионе ЕС (`eu-west-1`, Ирландия). Клиент — `src/lib/supabase.ts`,
читает `NEXT_PUBLIC_SUPABASE_URL` и `NEXT_PUBLIC_SUPABASE_ANON_KEY`
(anon/publishable key — публичный, ограничения через RLS-политики на
каждой таблице). Сервисный ключ сюда не попадает — он только в окружении
Python-конвейера, см. `pipeline/README.md`.

1. Скопируйте `.env.local.example` → `.env.local`, заполните значениями
   из дэшборда проекта: Settings → API.
2. Схема — SQL-миграции в `supabase/migrations/`: каталог (`university`,
   `programme`, `programme_requirement`), формулы — отдельно в выпуске 2.
3. Разработка — только в облаке, без локального Docker-стека (осознанный
   компромисс при 5 ч/нед: проще, но нет изолированной локальной песочницы).
4. Одноразово перед `supabase db push`: `npx supabase login`, затем
   `npx supabase link --project-ref <ref-из-URL-проекта>` (интерактивный
   вход через браузер — делается в своём терминале).

## Конвейер данных

`pipeline/` — Python + Playwright, обходит сайты вузов и пишет черновики
в ту же базу сервисным ключом (без HTTP-API, CLAUDE.md правило 3).
Ничего не подтверждает автоматически — подробности и как запустить
локально в `pipeline/README.md`.
