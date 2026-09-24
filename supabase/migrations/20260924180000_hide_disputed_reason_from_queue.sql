-- Ревью security-tester, 2026-09-24: verification_queue читаема анонимным
-- ключом (grant в 20260917210402_verification_queue.sql, никогда не
-- отзывался) и рендерится без авторизации на /lv|en/verification. Сама
-- эта миграция создавала view с явной целью "не должна утекать сами
-- неподтверждённые значения, только факт "тут есть что проверить"" (см.
-- комментарий в 20260917210402_verification_queue.sql) — формула/дата/тип
-- отбора туда никогда не попадали. disputed_reason (добавлен
-- 20260922100000_disputed_facts.sql) это правило нарушил: живая проверка
-- подтвердила, что через анонимный REST-запрос читается дословный текст
-- неподтверждённой формулы Ventspils "Elektronikas inženierija"
-- (коэффициенты формулы прямо в тексте причины — pipeline/src/
-- mark_disputed.py).
--
-- Фикс — тот же принцип, что и раньше: колонка остаётся (не ломаем форму
-- API, которую уже читает src/lib/verification-queue.ts), но публичное
-- view больше не отдаёт её содержимое, только disputed_at (факт "спорно",
-- не почему). Владелец видит настоящую причину как обычно — прямым
-- запросом к formula/application_round/university_admission_type/
-- programme_requirement_set в Studio (сервисная роль, не эта view).
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
  null::text
from programme_requirement_set rs
join programme p on p.id = rs.programme_id
join university u on u.id = p.university_id
where rs.verified_at is null;
