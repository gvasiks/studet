-- Протокол источника формулы (план работ, неделя 3; ревизия от 20 сентября,
-- позиция 01).
--
-- Проблема: у формулы был только source_url и свободный текст source_doc.
-- Этого мало, чтобы человек, подтверждающий формулу, мог убедиться, что она
-- взята из ТОГО документа: у РТУ source_url вёл на страницу сайта (у РТУ две
-- страницы давали разные веса), у ЛУ — на правила прошлого учебного года.
-- Личная память ("я так поступал") документом не является: коэффициенты
-- меняются каждый год.
--
-- Формула не может стать подтверждённой, пока у неё не заполнены:
--   1. source_url — адрес утверждённого документа;
--   2. source_doc_number и source_doc_date — номер и дата решения/приказа;
--   3. source_pdf_path и source_pdf_sha256 — копия PDF в репозитории
--      (docs/source-documents/...) и её хэш. Хэш нужен, чтобы подмену или
--      порчу файла было видно, а не только его отсутствие.
-- Черновик без этих полей в базе лежать МОЖЕТ (конвейер их не подтверждает),
-- подтвердить его — нет: проверка ниже не даст поставить verified_at даже
-- через Supabase Studio.
--
-- Дата загрузки копии (source_pdf_fetched_on) — для годового цикла сверки:
-- сравнивать с датой свежей версии на сайте вуза.

alter table formula
  add column source_doc_number text,
  add column source_doc_date date,
  add column source_pdf_path text,
  add column source_pdf_sha256 text check (source_pdf_sha256 is null or source_pdf_sha256 ~ '^[0-9a-f]{64}$'),
  add column source_pdf_fetched_on date;

alter table formula
  add constraint formula_verified_needs_protocol check (
    verified_at is null
    or (
      source_url is not null
      and source_doc_number is not null
      and source_doc_date is not null
      and source_pdf_path is not null
      and source_pdf_sha256 is not null
    )
  );

-- Очередь проверки: для формул показываем, чего не хватает протоколу.
-- Колонки дописаны в конец — так create or replace view допускает
-- расширение. Значения самой формулы (коэффициентов) по-прежнему не
-- выдаём: только факт "протокол неполон" и список пустых полей.
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
    and f.source_pdf_path is not null
    and f.source_pdf_sha256 is not null
  ) as protocol_complete,
  nullif(
    concat_ws(
      ', ',
      case when f.source_url is null then 'adrese' end,
      case when f.source_doc_number is null then 'dokumenta numurs' end,
      case when f.source_doc_date is null then 'dokumenta datums' end,
      case when f.source_pdf_path is null or f.source_pdf_sha256 is null then 'PDF kopija' end
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
