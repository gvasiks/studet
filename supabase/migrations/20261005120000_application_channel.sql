-- Через кого и где подают документы — «канал подачи» (решение владельца
-- 2026-10-05: на карточке каждой программы должна быть ссылка, где подать
-- документы в этот вуз).
--
-- Это поле правила 6 CLAUDE.md («через кого подача» подтверждает только
-- человек), поэтому таблица устроена как application_round: конвейер пишет
-- черновик с источником, а публично строка видна только после того, как
-- владелец проставит verified_at в Studio. Неверная ссылка на подачу
-- документов опаснее неверной цены — неподтверждённые не показываем вовсе.
--
-- Запись — на вуз и уровень, а не на программу: куда подавать, зависит от
-- вуза и от уровня (бакалавриат государственных вузов — единая подача на
-- портале latvija.gov.lv, магистратура и частные вузы — обычно система
-- самого вуза). degree_level = null значит «все уровни этого вуза»; запись
-- с конкретным уровнем имеет приоритет (см. src/lib/application-channel.ts).
--
-- Канал описывает подачу для абитуриентов с латвийским образованием —
-- первой аудитории сайта. У иностранных абитуриентов порядок может быть
-- другим; это продукт выпуска 4.
create table application_channel (
  id uuid primary key default gen_random_uuid(),
  university_id uuid not null references university (id) on delete cascade,
  degree_level text check (degree_level in ('college', 'bachelor', 'master', 'doctoral')),
  -- unified_portal — единая подача через государственный портал услуг
  --                  (одна заявка сразу в несколько вузов)
  -- university     — подача в сам вуз: его электронная система, почта или
  --                  лично. Способов у вузов много, и они меняются от уровня
  --                  к уровню (магистратура РТУ — электронно или лично,
  --                  докторантура — письмом), поэтому тип один, а порядок
  --                  человек читает на странице вуза, куда ведёт url.
  channel_type text not null check (channel_type in ('unified_portal', 'university')),
  -- куда вести человека: услуга на портале либо страница вуза о подаче
  -- документов на этот уровень
  url text not null,
  -- страница вуза (или портала), где описан порядок подачи, и дословная
  -- цитата оттуда — чтобы проверяющий видел, на чём основан черновик
  source_url text not null,
  source_excerpt text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  -- одна запись на (вуз, уровень); «все уровни» (null) — тоже одна.
  -- nulls not distinct нужен и для upsert из seed_application_channels.py
  unique nulls not distinct (university_id, degree_level)
);

create index application_channel_university_id_idx on application_channel (university_id);

create trigger application_channel_set_updated_at
before update on application_channel
for each row execute function set_updated_at();

alter table application_channel enable row level security;

-- Гейт на verified_at в самой политике — тот же паттерн, что у
-- application_round и formula: anon-ключ публичный, без политики прямой
-- запрос к REST API в обход Next.js вернул бы неподтверждённую ссылку.
create policy application_channel_public_read on application_channel
  for select using (verified_at is not null);

-- Очередь проверки: добавлена пятая ветка — каналы подачи. Остальные ветки
-- перенесены без изменений из 20260924180000 (disputed_reason по-прежнему
-- не отдаётся). Как и раньше, в очередь попадает только факт «тут есть что
-- проверить» — сама ссылка и тип подачи наружу не выходят.
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
where rs.verified_at is null

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
