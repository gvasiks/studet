-- Аудит 2026-10-04, вторая очередь: два независимых исправления прав.
--
-- 1. Права на запись у публичных ролей. Запись в базу с сайта закрывала
--    только RLS: политик на insert/update/delete нет, поэтому запись
--    запрещена. Но табличные права на запись у ролей anon и authenticated
--    оставались — ошибка в одной будущей политике открыла бы запись.
--    Отзываем их: это второй рубеж. Сайт в базу ничего не пишет (конвейер
--    пишет сервисным ключом, он эти права обходит). Когда появится сбор
--    почты, право на insert выдаётся одной таблице явно.
--
-- 2. Программа, пропавшая с сайта вуза, скрывается политикой таблицы
--    programme (missed_runs >= 2). Но её формула, направление и требования
--    оставались доступны через API по programme_id, а неподтверждённые
--    факты — в очереди проверки. Политики ниже добавляют условие «программа
--    видна»: подзапрос к programme выполняется с правами читающего, поэтому
--    к нему применяется политика самой programme — условие «missed_runs < 2»
--    не дублируется и не разойдётся с ней. Слагаемые и пороги формулы и
--    строки требований уже проверяют видимость «своей» формулы или набора
--    тем же способом — их политики не меняются.
--
--    Литовские таблицы (lt_admission_unit и другие) не тронуты: их строки —
--    открытые факты из списка программ, решение записано в
--    20261006120000_lt_formulas.sql.

-- ---------------------------------------------------------------- 1. запись

revoke insert, update, delete, truncate, references, trigger
  on all tables in schema public
  from anon, authenticated;

-- То же для таблиц, которые появятся позже: новые таблицы создаёт роль
-- postgres (миграции применяются в Studio под ней).
alter default privileges for role postgres in schema public
  revoke insert, update, delete, truncate, references, trigger
  on tables
  from anon, authenticated;

-- ---------------------------------------------------------------- 2. скрытые программы

drop policy formula_public_read on formula;
create policy formula_public_read on formula
  for select using (
    verified_at is not null
    and exists (select 1 from programme p where p.id = formula.programme_id)
  );

drop policy programme_field_public_read on programme_field;
create policy programme_field_public_read on programme_field
  for select using (
    exists (select 1 from programme p where p.id = programme_field.programme_id)
  );

drop policy programme_requirement_set_public_read on programme_requirement_set;
create policy programme_requirement_set_public_read on programme_requirement_set
  for select using (
    verified_at is not null
    and exists (select 1 from programme p where p.id = programme_requirement_set.programme_id)
  );

-- Очередь проверки — представление, оно читает таблицы с правами владельца
-- и политик не видит, поэтому условие пишется явно. Определение перенесено
-- без изменений из 20261005120000_application_channel.sql, кроме трёх
-- условий «and p.missed_runs < 2» в ветках формулы, направления и требований.
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
  null::text as disputed_reason
from formula f
join programme p on p.id = f.programme_id
join university u on u.id = p.university_id
where f.verified_at is null and p.missed_runs < 2
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
  null::text
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
  null::text
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
where pf.verified_at is null and p.missed_runs < 2
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
  null::text
from programme_requirement_set rs
join programme p on p.id = rs.programme_id
join university u on u.id = p.university_id
where rs.verified_at is null and p.missed_runs < 2

union all

select
  ac.id,
  'application_channel',
  null,
  null,
  u.slug,
  coalesce(u.name_lv, u.name_en),
  ac.created_at,
  ac.source_url,
  1,
  null::boolean,
  null::text,
  null::date,
  null::timestamptz,
  null::text
from application_channel ac
join university u on u.id = ac.university_id
where ac.verified_at is null;
