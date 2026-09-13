-- Конкурсные формулы — выпуск 2. Схема намечена в docs/PLAN.md, раздел 6.
-- Формула — данные, а не код (правило 2 CLAUDE.md): вычислитель один и
-- общий (~40 строк на TypeScript), всё различие между вузами — строки
-- здесь. Ничего из этой миграции не подтверждено автоматически: формулу
-- подтверждает только человек (правило 6), verified_at везде начинается
-- с null, даже для конкурсной модели, повторяющейся у трёх вузов.

create table formula (
  id uuid primary key default gen_random_uuid(),
  programme_id uuid not null references programme (id) on delete cascade,
  -- у программы минимум два варианта: обычные CE и льготные/зарубежные/
  -- сдавшие до 2004 — у них может быть другой набор слагаемых
  variant text not null default 'ce',
  valid_from date not null,
  valid_to date,
  -- утверждённый PDF правил приёма, не страница сайта (у РТУ две страницы
  -- сайта дают разные коэффициенты — 0,8/0,7 против 0,79/0,79)
  source_url text,
  source_doc text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  unique (programme_id, variant, valid_from)
);

create index formula_programme_id_idx on formula (programme_id);

create table formula_term (
  id uuid primary key default gen_random_uuid(),
  formula_id uuid not null references formula (id) on delete cascade,
  kind text not null check (kind in ('ce', 'ce_average', 'certificate', 'entrance_exam')),
  -- subject обязателен только для kind='ce' (конкретный экзамен);
  -- для среднего балла, аттестата, вступительного испытания — null
  subject text,
  coefficient numeric(6, 3) not null
);

create index formula_term_formula_id_idx on formula_term (formula_id);

create table formula_gate (
  id uuid primary key default gen_random_uuid(),
  formula_id uuid not null references formula (id) on delete cascade,
  -- порог допуска, не влияющий на сам балл: например, у РТУ
  -- математика должна быть не ниже 20%, иначе к конкурсу не допускают
  subject text not null,
  min_percent numeric(5, 2) not null,
  note text
);

create index formula_gate_formula_id_idx on formula_gate (formula_id);

-- augstākais / optimālais / vispārīgais — совпадают у всех проверенных
-- вузов дословно, видимо заданы общей нормативной базой, а не самим
-- вузом. Отдельная таблица (не захардкожено в вычислителе), потому что
-- меняются ежегодно и старые значения нужны для истории прошлых конкурсов.
create table level_coefficient (
  level text not null,
  coefficient numeric(4, 2) not null,
  valid_from date not null,
  source_url text,
  verified_at timestamptz,
  verified_by text,
  primary key (level, valid_from)
);

alter table formula enable row level security;
alter table formula_term enable row level security;
alter table formula_gate enable row level security;
alter table level_coefficient enable row level security;

create policy formula_public_read on formula for select using (true);
create policy formula_term_public_read on formula_term for select using (true);
create policy formula_gate_public_read on formula_gate for select using (true);
create policy level_coefficient_public_read on level_coefficient for select using (true);

-- Значения подтверждены как совпадающие у ЛУ, РТУ и Вентспилса на момент
-- разведки (сентябрь 2026, см. docs/PLAN.md) — но конкретный утверждённый
-- нормативный документ как source_url ещё не найден, verified_at пуст.
insert into level_coefficient (level, coefficient, valid_from) values
  ('augstakais', 1.00, '2022-01-01'),
  ('optimalais', 0.75, '2022-01-01'),
  ('vispaarigais', 0.50, '2022-01-01');
