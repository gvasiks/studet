-- План 2026-09-21, неделя 1, пункт 08 (наблюдение за конвейером сбора).
--
-- main.py по расписанию (каждый понедельник) собирает каталог, но до сих
-- пор никто, кроме статуса в интерфейсе GitHub, не видел, прошёл ли прогон
-- целиком. По понедельникам в 01:00 UTC туда никто не смотрит — молчание
-- опаснее ошибки. Эта таблица даёт прогону начало и конец, а pipeline_health
-- отвечает на один вопрос: когда был последний УСПЕШНЫЙ ПОЛНЫЙ сбор.
--
-- full_run отличает такой сбор от ручного точечного перезапуска одного
-- источника (`python src/main.py rsu` — так чинят один вуз, не пересобирая
-- остальные 24). Без этого различия точечный перезапуск молча обновлял бы
-- "последний успешный сбор", а настоящий недельный прогон мог бы месяцами
-- падать незамеченным.
create table pipeline_run (
  id uuid primary key default gen_random_uuid(),
  started_at timestamptz not null,
  finished_at timestamptz,
  status text not null default 'running' check (status in ('running', 'success', 'failed')),
  full_run boolean not null default true,
  source_count int,
  programme_count int,
  error_count int not null default 0,
  -- первые несколько ошибок, не весь лог: этого достаточно, чтобы понять
  -- масштаб ("новый бажный сборщик" vs "один вуз закрыл набор"), а полный
  -- разбор всё равно идёт по логу самого прогона в GitHub Actions
  note text
);

-- Пишет и читает эту таблицу целиком только сервисный ключ (main.py и
-- сторож конвейера, см. check_pipeline_health.py); публично читается только
-- узкая сводка через pipeline_health ниже — тот же приём, что у
-- verification_queue (20260917210402): view создаётся ролью миграции и
-- читает исходную таблицу в её правах, минуя RLS ниже.
alter table pipeline_run enable row level security;

create view pipeline_health as
select
  max(finished_at) filter (where status = 'success' and full_run) as last_success_at,
  (select status from pipeline_run where full_run order by started_at desc limit 1) as last_status,
  (select finished_at from pipeline_run where full_run order by started_at desc limit 1) as last_finished_at,
  (select error_count from pipeline_run where full_run order by started_at desc limit 1) as last_error_count
from pipeline_run;

grant select on pipeline_health to anon, authenticated;
