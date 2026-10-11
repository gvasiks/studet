-- Эстония: направление программы по классификатору ISCED-F
-- (docs/PLAN-ESTONIA.md, фаза 2).
--
-- Государственный портал haridusportaal.edu.ee у каждой программы называет
-- три уровня классификатора: область (õppevaldkond, 10 штук), направление
-- (õppesuund, 34) и группу программ (õppekavarühm). По направлению работают
-- фильтр «интересы» в каталоге и анкета, и оно показывается на карточке
-- программы.
--
-- Почему не programme_field: там код латвийского классификатора, его
-- подтверждает человек, и неподтверждённые строки попадают в очередь
-- проверки владельца. Эстонское направление берётся с портала как есть и
-- подтверждения человеком не ждёт (решение владельца 2026-10-11, как для
-- Литвы).
--
-- field_code — номер направления в справочнике портала («2464» — Ärindus ja
-- haldus). Числовых кодов ISCED-F портал не отдаёт, поэтому ключом служит
-- его собственный номер; названия хранятся рядом, как пришли.
--
-- Пишет pipeline/src/ee_load_fields.py.

create table ee_programme_field (
  programme_id uuid primary key references programme (id) on delete cascade,
  broad_name text not null,
  field_code text not null check (field_code ~ '^[0-9]+$'),
  field_name text not null,
  detailed_name text,
  source_url text not null,
  extracted_at timestamptz not null default now()
);

create index ee_programme_field_field_code_idx on ee_programme_field (field_code);

alter table ee_programme_field enable row level security;

-- Открытый факт с государственного портала — виден всем, но только пока
-- видна сама программа (скрытая после двух пропусков сбора не должна
-- оставаться видимой через своё направление — аудит 2026-10-04).
create policy ee_programme_field_public_read on ee_programme_field
  for select using (
    exists (select 1 from programme p where p.id = ee_programme_field.programme_id)
  );

-- Права на запись у анонимного и вошедшего пользователя отозваны по
-- умолчанию миграцией 20261010120000; чтение — явно.
grant select on ee_programme_field to anon, authenticated;
