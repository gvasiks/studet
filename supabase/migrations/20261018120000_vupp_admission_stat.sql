-- Прошлогодний конкурс рядом с баллом (решение владельца 2026-09-30;
-- разведка — docs/checks/VUPP-RECON-2026-10-18.md).
--
-- vupp_admission_stat — строки открытой статистики приёма
-- statistika.vupp.lv как есть: программа × вид × форма × финансирование ×
-- город и четыре числа (места, заявления, с 1-м приоритетом,
-- предварительно прошли конкурс). Баллов и проходных портал не даёт.
-- Пишет pipeline/src/vupp_stats.py. Это открытые данные — чтение публичное.
--
-- programme_vupp_link — какая программа каталога соответствует коду
-- приёма портала. Ошибка сопоставления показала бы чужие цифры, поэтому
-- связь, как направление программы, подтверждает владелец по правилу
-- (verified_at); наружу видны только подтверждённые связи. Черновики пишут
-- pipeline/src/vupp_link_*.py, verified_at они не трогают.

create table vupp_admission_stat (
  id uuid primary key default gen_random_uuid(),
  -- год приёма (лето): 2026 — приём в 2026/27 учебный год
  admission_year int not null check (admission_year between 2010 and 2100),
  -- вуз — наш код (lu, rtu…); null — вуза нет в каталоге (Banku augstskola 2025)
  university_slug text,
  portal_university_name text not null,
  -- факультет или филиал — заголовок таблицы на портале
  unit text,
  programme_code text not null,
  programme_name text not null,
  -- как на портале: «Bakalaura akadēmiskā», «Pilna laika (dienas)», «Budžets»
  programme_kind text not null,
  study_mode text not null,
  funding text not null,
  city text not null,
  -- заголовок страницы портала: какой это срез приёма («2. kārtas
  -- apstiprinātie pieteikumi…» — после второго тура) и когда портал его
  -- обновил в последний раз (только день — время портал пишет по Риге
  -- без пояса); на сайте показываются рядом с числами
  stage text not null,
  portal_updated_on date,
  -- пусто — портал числа не дал; places_unlimited — вместо числа «*»
  -- («neierobežots vietu skaits», так у EKA)
  places int check (places >= 0),
  places_unlimited boolean not null default false,
  applications int check (applications >= 0),
  first_priority int check (first_priority >= 0),
  passed int check (passed >= 0),
  source_url text not null,
  extracted_at timestamptz not null,
  unique (admission_year, portal_university_name, programme_code, programme_kind, study_mode, funding, city)
);

create index vupp_admission_stat_code_idx on vupp_admission_stat (university_slug, programme_code);

alter table vupp_admission_stat enable row level security;
create policy vupp_admission_stat_public_read on vupp_admission_stat for select using (true);
grant select on vupp_admission_stat to anon, authenticated;

create table programme_vupp_link (
  id uuid primary key default gen_random_uuid(),
  programme_id uuid not null references programme (id) on delete cascade,
  university_slug text not null,
  programme_code text not null,
  -- как найдена связь: 'code_from_page' (код на странице программы вуза),
  -- 'code_from_slug' (код в адресе), 'name' (по названию) — для отчёта
  method text not null,
  -- откуда взят код (страница вуза) — правило 5
  source_url text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  unique (programme_id, university_slug, programme_code)
);

alter table programme_vupp_link enable row level security;
-- наружу — только связи, подтверждённые человеком
create policy programme_vupp_link_public_read on programme_vupp_link
  for select using (verified_at is not null);
grant select on programme_vupp_link to anon, authenticated;

comment on table vupp_admission_stat is 'Строки statistika.vupp.lv как есть; см. описание в миграции.';
comment on table programme_vupp_link is 'Связь программы каталога с кодом приёма портала; наружу — только подтверждённые.';
