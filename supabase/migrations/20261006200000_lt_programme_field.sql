-- Литва, фаза 4: направление программы по официальной классификации.
--
-- В списке общего приёма LAMA BPO у каждой программы стоят группа направлений
-- (17 штук: «Inžinerijos mokslai») и направление (102: «E14 Aeronautikos
-- inžinerija»). По нему работают фильтр «интересы» в каталоге и анкета, и оно
-- показывается на карточке программы.
--
-- Почему не programme_field: там код латвийского классификатора (три
-- цифры, проверка в таблице), его подтверждает человек, и неподтверждённые
-- строки попадают в очередь проверки владельца. Литовское направление —
-- другой классификатор, берётся из официального списка как есть и
-- подтверждения человеком не ждёт (решение владельца 2026-10-05).
--
-- Пишет pipeline/src/lt_load_fields.py.

create table lt_programme_field (
  programme_id uuid primary key references programme (id) on delete cascade,
  group_code text not null check (group_code ~ '^[A-Z]$'),
  group_name text not null,
  field_code text not null check (field_code ~ '^[A-Z][0-9]{2}$'),
  field_name text not null,
  source_url text not null,
  extracted_at timestamptz not null default now(),
  check (left(field_code, 1) = group_code)
);

create index lt_programme_field_field_code_idx on lt_programme_field (field_code);

alter table lt_programme_field enable row level security;

-- Открытый факт из официального списка программ — виден всем, как и сама
-- программа.
create policy lt_programme_field_public_read on lt_programme_field
  for select using (true);
