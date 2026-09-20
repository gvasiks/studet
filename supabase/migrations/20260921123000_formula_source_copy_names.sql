-- Продолжение 20260921120000_formula_source_protocol.sql: копия документа —
-- не обязательно PDF. У РТУ утверждённый текст правил приёма (Senāta
-- protokollēmums Nr. 697 от 24.11.2025) опубликован только страницей
-- сайта, PDF нет; у ЛУ на 2026/27 — тоже страница. Поэтому поля
-- называются "копия", а не "PDF": для страницы это сохранённый HTML.
-- Переименование колонок Postgres переносит в ограничения и представления
-- сам; заново пересоздаётся только представление — из-за текста подсказки.

alter table formula rename column source_pdf_path to source_copy_path;
alter table formula rename column source_pdf_sha256 to source_copy_sha256;
alter table formula rename column source_pdf_fetched_on to source_copy_fetched_on;

comment on column formula.source_doc_date is
  'Дата версии документа: у документа с поправками — дата ПОСЛЕДНЕГО решения, по которому взята копия';
comment on column formula.source_copy_path is
  'Путь к копии документа (PDF или сохранённая страница) в репозитории, docs/source-documents/...';

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
  f.source_doc_date
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
  1,
  null::boolean,
  null::text,
  null::date
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
  null::date
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
  null::date
from programme_field pf
join programme p on p.id = pf.programme_id
join university u on u.id = p.university_id
where pf.verified_at is null
group by u.id, u.slug, u.name_lv, u.name_en;
