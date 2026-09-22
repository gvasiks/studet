-- План 2026-09-21, пункт 02: требования к экзаменам как отдельный тип
-- факта — то, что реально открывает обратный поиск программам без
-- формулы (сегодня подтверждённая формула есть у 75 из 900 программ;
-- требования — «какие экзамены вообще нужны» — можно извлечь из тех же
-- документов гораздо для большего числа программ, включая те, где сама
-- формула неоднозначна: LU «CE fizikā vai CE ķīmijā, vai CE bioloģijā» не
-- разбирается как формула — какая доля веса у какого предмета неясна, — но
-- как ТРЕБОВАНИЕ («нужен один из трёх») разбирается однозначно).
--
-- Таблица programme_requirement существует с 20260911, но пуста (0 строк)
-- и спроектирована без протокола источника и подтверждения человеком —
-- то же упущение, что было у formula до недели 3 (миграции
-- 20260921120000/20260921123000). Раз данных нет, перестраиваем набело,
-- а не патчим: по образцу formula/formula_term — заголовок с протоколом
-- и подтверждением на программу (programme_requirement_set), строки-предметы
-- отдельно. Ошибка в требовании стоит так же дорого, как ошибка в формуле
-- (правило 6 CLAUDE.md — abiturient may не сдать нужный экзамен), поэтому
-- тот же протокол и тот же гейт по RLS.

drop policy if exists programme_requirement_public_read on programme_requirement;
drop table if exists programme_requirement;

create table programme_requirement_set (
  id uuid primary key default gen_random_uuid(),
  programme_id uuid not null references programme (id) on delete cascade unique,
  source_url text,
  source_doc text,
  source_doc_number text,
  source_doc_date date,
  source_copy_path text,
  source_copy_sha256 text check (source_copy_sha256 is null or source_copy_sha256 ~ '^[0-9a-f]{64}$'),
  source_copy_fetched_on date,
  -- дословный текст блока документа — как formula.source_excerpt
  source_excerpt text,
  verified_at timestamptz,
  verified_by text,
  disputed_at timestamptz,
  disputed_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint programme_requirement_set_verified_needs_protocol check (
    verified_at is null
    or (
      source_url is not null
      and source_doc_number is not null
      and source_doc_date is not null
      and source_copy_path is not null
      and source_copy_sha256 is not null
    )
  ),
  constraint programme_requirement_set_not_verified_and_disputed check (
    verified_at is null or disputed_at is null
  )
);

create trigger programme_requirement_set_set_updated_at
before update on programme_requirement_set
for each row execute function set_updated_at();

create table programme_requirement (
  id uuid primary key default gen_random_uuid(),
  requirement_set_id uuid not null references programme_requirement_set (id) on delete cascade,
  -- mathematics, latvian, english, physics, chemistry, biology, history...
  -- (те же ключи, что в dict.survey.exams.subjects и в formula_term.subject)
  subject text not null,
  -- augstakais | optimalais | vispaarigais; null = уровень не важен для допуска
  min_level text,
  -- строки с одинаковым значением внутри ОДНОГО requirement_set —
  -- взаимозаменяемые варианты ("нужен хотя бы один из"), например три
  -- строки english/french/german с alternative_group='foreign_language' —
  -- LU "CE angļu valodā vai CE franču valodā, vai CE vācu valodā", или
  -- physics/chemistry/biology с alternative_group='science' — LU
  -- "CE fizikā vai CE ķīmijā, vai CE bioloģijā". null = предмет обязателен
  -- сам по себе, без альтернативы.
  alternative_group text,
  note text,
  created_at timestamptz not null default now()
);

create index programme_requirement_set_id_idx on programme_requirement (requirement_set_id);

alter table programme_requirement_set enable row level security;
alter table programme_requirement enable row level security;

create policy programme_requirement_set_public_read on programme_requirement_set
  for select using (verified_at is not null);

create policy programme_requirement_public_read on programme_requirement
  for select using (
    exists (
      select 1 from programme_requirement_set s
      where s.id = programme_requirement.requirement_set_id and s.verified_at is not null
    )
  );

-- verification_queue (20260917210402 и позже) — новая ветка, тот же приём,
-- что у formula: один факт на программу, item_count — число строк-предметов.
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
  1 as item_count,
  (
    f.source_url is not null
    and f.source_doc_number is not null
    and f.source_doc_date is not null
    and f.source_copy_path is not null
    and f.source_copy_sha256 is not null
  ) as protocol_complete,
  nullif(
    concat_ws(
      ', ',
      case when f.source_url is null then 'adrese' end,
      case when f.source_doc_number is null then 'dokumenta numurs' end,
      case when f.source_doc_date is null then 'dokumenta datums' end,
      case when f.source_copy_path is null or f.source_copy_sha256 is null then 'dokumenta kopija' end
    ),
    ''
  ) as protocol_missing,
  f.source_doc_date,
  f.disputed_at,
  f.disputed_reason
from formula f
join programme p on p.id = f.programme_id
join university u on u.id = p.university_id
where f.verified_at is null
  and f.valid_to is null

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
  1,
  null::boolean,
  null::text,
  null::date,
  ar.disputed_at,
  ar.disputed_reason
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
  1,
  null::boolean,
  null::text,
  null::date,
  uat.disputed_at,
  uat.disputed_reason
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
  count(*)::int,
  null::boolean,
  null::text,
  null::date,
  null::timestamptz,
  null::text
from programme_field pf
join programme p on p.id = pf.programme_id
join university u on u.id = p.university_id
where pf.verified_at is null
group by u.id, u.slug, u.name_lv, u.name_en

union all

select
  rs.id,
  'programme_requirement',
  p.id,
  coalesce(p.name_lv, p.name_en),
  u.slug,
  coalesce(u.name_lv, u.name_en),
  rs.created_at,
  rs.source_url,
  (select count(*)::int from programme_requirement pr where pr.requirement_set_id = rs.id),
  (
    rs.source_url is not null
    and rs.source_doc_number is not null
    and rs.source_doc_date is not null
    and rs.source_copy_path is not null
    and rs.source_copy_sha256 is not null
  ),
  nullif(
    concat_ws(
      ', ',
      case when rs.source_url is null then 'adrese' end,
      case when rs.source_doc_number is null then 'dokumenta numurs' end,
      case when rs.source_doc_date is null then 'dokumenta datums' end,
      case when rs.source_copy_path is null or rs.source_copy_sha256 is null then 'dokumenta kopija' end
    ),
    ''
  ),
  rs.source_doc_date,
  rs.disputed_at,
  rs.disputed_reason
from programme_requirement_set rs
join programme p on p.id = rs.programme_id
join university u on u.id = p.university_id
where rs.verified_at is null;
