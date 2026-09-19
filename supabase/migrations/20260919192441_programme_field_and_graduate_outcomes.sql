-- Ревью 2026-09, пункты 14 и 16 держатся на одном недостающем поле:
-- у наших программ нет "направления" (код группы программ из
-- классификатора образования — тот же справочник, по которому ИЗМ
-- публикует мониторинг выпускников). Без него нельзя ни показать, что
-- стало с выпускниками именно этого направления (14), ни проверить,
-- что категории интересов в анкете вообще совпадают с тем, что есть
-- в каталоге (16).
--
-- Отдельная таблица, а не колонка на programme: конвейер (main.py)
-- upsert-ит programme целиком по данным сайтов вузов, а направление
-- присваивается отдельным шагом (seed_programme_fields.py) и
-- подтверждается отдельно.
--
-- Публичное чтение открыто и для неподтверждённых строк — это
-- навигационная подсказка (фильтр по интересам в анкете), а не факт,
-- на который человек опирается при выборе. Блок "что стало с
-- выпускниками" (зарплаты) требует verified_at на этой таблице —
-- проверка в приложении (src/lib/outcome-queries.ts), не в RLS: сам
-- код направления безобиден, вредна только неверно подобранная к нему
-- статистика доходов, а её показывает уже приложение.
create table programme_field (
  programme_id uuid primary key references programme (id) on delete cascade,
  -- Programmu_grupa из датасета ИЗМ: 3 цифры, первые две — тематическая
  -- область (34 — бизнес и управление, 48 — вычислительная техника...)
  field_code text not null check (field_code ~ '^[0-9]{3}$'),
  -- откуда взято: 'name-rules' — черновая разметка по названию
  -- (pipeline/src/seed_programme_fields.py), человек подтверждает
  source text not null default 'name-rules',
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger programme_field_set_updated_at
before update on programme_field
for each row execute function set_updated_at();

alter table programme_field enable row level security;
create policy programme_field_public_read on programme_field for select using (true);

-- Официальные открытые данные (data.gov.lv, ИЗМ/ЦСУ, CC0): агрегаты по
-- вузу + уровню + группе программ + году выпуска; персональных данных
-- нет, мелкие ячейки (<5 выпускников) издатель уже скрыл. Значит и
-- политика чтения открыта без гейта.
create table graduate_outcome (
  id uuid primary key default gen_random_uuid(),
  university_id uuid not null references university (id) on delete cascade,
  -- год выпуска и год, на который собраны данные о занятости/доходах
  graduation_year integer not null,
  tax_year integer not null,
  -- Studiju_limenis: 41 колледж, 42/43 бакалавр, 45/47 магистр,
  -- 51 докторантура (см. pipeline/src/graduate_outcomes.py)
  level_code text not null,
  programme_group text not null check (programme_group ~ '^[0-9]{3}$'),
  graduates integer not null,
  employed integer not null,
  unemployed_or_inactive integer not null,
  emigrated integer not null,
  no_info integer not null,
  -- null = издатель скрыл (меньше 30 занятых) или докторантура
  avg_income_eur numeric(10, 2),
  median_income_eur numeric(10, 2),
  source_url text not null,
  imported_at timestamptz not null default now(),
  unique (university_id, graduation_year, tax_year, level_code, programme_group)
);

create index graduate_outcome_lookup_idx on graduate_outcome (university_id, programme_group);

alter table graduate_outcome enable row level security;
create policy graduate_outcome_public_read on graduate_outcome for select using (true);

-- Очередь верификации (пункт 03) — добавляем строку на вуз с
-- количеством неподтверждённых направлений: 339 отдельных строк
-- утопили бы остальную очередь. item_count дописан в конец — так
-- create or replace view допускает расширение.
create or replace view verification_queue as
select
  f.id as fact_id,
  'formula'::text as fact_type,
  p.id as programme_id,
  coalesce(p.name_lv, p.name_en) as programme_name,
  u.slug as university_slug,
  coalesce(u.name_lv, u.name_en) as university_name,
  f.created_at as collected_at,
  f.source_url,
  1 as item_count
from formula f
join programme p on p.id = f.programme_id
join university u on u.id = p.university_id
where f.verified_at is null

union all

select
  ar.id,
  'application_round',
  null,
  null,
  u.slug,
  coalesce(u.name_lv, u.name_en),
  ar.created_at,
  ar.source_url,
  1
from application_round ar
join university u on u.id = ar.university_id
where ar.verified_at is null

union all

select
  uat.university_id,
  'admission_type',
  null,
  null,
  u.slug,
  coalesce(u.name_lv, u.name_en),
  uat.created_at,
  uat.source_url,
  1
from university_admission_type uat
join university u on u.id = uat.university_id
where uat.verified_at is null

union all

select
  u.id,
  'programme_field',
  null,
  null,
  u.slug,
  coalesce(u.name_lv, u.name_en),
  min(pf.created_at),
  null,
  count(*)::int
from programme_field pf
join programme p on p.id = pf.programme_id
join university u on u.id = p.university_id
where pf.verified_at is null
group by u.id, u.slug, u.name_lv, u.name_en;
