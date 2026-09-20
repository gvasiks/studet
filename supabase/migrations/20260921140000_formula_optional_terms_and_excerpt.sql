-- Извлечение формул ЛУ 2026/27 (план работ, "вытаскиваем все формулы").
--
-- 1. formula_term.optional. В документе ЛУ бывают слагаемые с оговоркой
--    "ja nav CE sociālajās zinātnēs, tad 0" или "ja iestājpārbaudījums netiek
--    kārtots, tad 0": не сдал — слагаемое равно нулю, а программа при этом
--    остаётся доступной. Раньше модель не отличала такое слагаемое от
--    обязательного, и обратный поиск считал бы социальные науки обязательным
--    экзаменом. Считает вычислитель по-прежнему одинаково (нет данных — 0);
--    флаг нужен тем, кто решает, чего "не хватает".
--
-- 2. formula.source_excerpt — дословный текст блока программы из документа.
--    Человек, подтверждающий формулу, сверяет разобранные слагаемые с
--    оригиналом, а не с пересказом: в блоке есть и то, что модель не
--    выражает (особые условия, минимальные баллы, дополнительные баллы).
--
-- 3. Очередь проверки не показывает вытесненные формулы (valid_to задан):
--    когда формулу заменяет версия нового учебного года, старая остаётся в
--    истории, но проверять её уже незачем.

alter table formula_term
  add column optional boolean not null default false;

alter table formula
  add column source_excerpt text;

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
