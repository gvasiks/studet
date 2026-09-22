-- План 2026-09-21, неделя 3, пункт 03: третье состояние факта.
--
-- Сегодня у факта (formula/application_round/university_admission_type/
-- programme_field) два состояния: подтверждён или нет. Третьего —
-- "посмотрел, подтвердить не могу, вот почему" — не было, и такое знание
-- уходило в прозу комментариев кода (например, docstring seed_formulas.py
-- про Elektronikas inženierija: сумма коэффициентов даёт 110 при заявленной
-- "шкале 100", потому что физика — необязательное слагаемое сверху). Через
-- год такой абзац никто не свяжет с конкретной записью в базе.
--
-- disputed_at/disputed_reason — не альтернатива verified_at, а соседнее
-- состояние: запись остаётся неподтверждённой (verified_at по-прежнему
-- null, запись остаётся в выборке verification_queue), но помечена как уже
-- разобранную человеком или явно осторожной автоматикой — и очередь может
-- показать её отдельно, не предлагая как "давайте посмотрим это" на каждой
-- сверке.
--
-- Кто вправе поставить disputed_at — не то же самое, что "кто вправе
-- подтвердить" (правило 6 — только человек). Пометка "спорно" не объявляет
-- факт используемым, а наоборот, явно снижает доверие к нему — поэтому,
-- в отличие от verified_at, её может проставить и осторожная автоматика
-- (парсер, нашедший объяснимую, но не однозначную формулу), раз она не
-- разрешает то, что запрещает правило 6, а честно фиксирует сомнение.
-- Ограничение ниже гарантирует только одно: подтверждённая запись не может
-- одновременно считаться спорной.
alter table formula
  add column disputed_at timestamptz,
  add column disputed_reason text,
  add constraint formula_not_verified_and_disputed check (verified_at is null or disputed_at is null);

alter table application_round
  add column disputed_at timestamptz,
  add column disputed_reason text,
  add constraint application_round_not_verified_and_disputed check (verified_at is null or disputed_at is null);

alter table university_admission_type
  add column disputed_at timestamptz,
  add column disputed_reason text,
  add constraint admission_type_not_verified_and_disputed check (verified_at is null or disputed_at is null);

alter table programme_field
  add column disputed_at timestamptz,
  add column disputed_reason text,
  add constraint programme_field_not_verified_and_disputed check (verified_at is null or disputed_at is null);

-- verification_queue (20260917210402, дополнена 20260921140000) — те же
-- четыре ветки, с двумя добавленными колонками. programme_field группирует
-- много строк в одну (одна строка на вуз), поэтому одно текстовое
-- disputed_reason на группу не имеет смысла — там пока null; у этого типа
-- факта на 2026-09-22 ни одной спорной записи и нет.
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
group by u.id, u.slug, u.name_lv, u.name_en;
