-- Эстония: правило конкурса следующего учебного года из решения вуза
-- (docs/PLAN-ESTONIA.md, журнал 2026-11-27).
--
-- Зачем: правило в ee_admission.rule разобрано со страницы последнего
-- конкурса SAIS — это приём прошлого лета. TalTech утверждает условия
-- следующего года осенью (решение сената 24.11.2026 № 40, «I ja II
-- kõrgharidusastme üliõpilaste 2027/2028. õa vastuvõtutingimused»), а
-- конкурсы SAIS появляются только весной. Сверка 2026-11-27: из 18 правил
-- TalTech изменились 16. Решение владельца 2026-11-27: показывать условия
-- следующего года из решения сената уже сейчас, рядом с прошлым приёмом.
--
-- rule — в той же форме, что ee_admission.rule у TalTech
-- ({"model": "thresholds", "apply": …, "guarantee": …, "places": …,
--   "ranking": …, "wide_math": true}), чтобы сайт показывал его тем же
-- компонентом. new_curriculum — пометка «***» приложения: новый учебный
-- план, набор будет, только если министерство его зарегистрирует.
--
-- Одна строка на программу и учебный год. Двойники одной программы
-- (версии учебного плана, ee-variants.ts) получают одно правило.
-- Факт без подтверждения человеком, с пометкой «извлечено автоматически»
-- (решение владельца 2026-10-11).
--
-- Пишет pipeline/src/ee_load_taltech_conditions.py.

create table ee_next_rule (
  programme_id uuid not null references programme (id) on delete cascade,
  academic_year text not null check (academic_year ~ '^\d{4}/\d{4}$'),
  rule jsonb not null check (jsonb_typeof(rule) = 'object'),
  new_curriculum boolean not null default false,
  source_url text not null check (source_url ~ '^https://'),
  source_title text not null,
  decided_on date not null,
  extracted_at timestamptz not null default now(),
  primary key (programme_id, academic_year)
);

alter table ee_next_rule enable row level security;

-- Открытый факт из опубликованного решения вуза — виден всем, пока видна
-- сама программа (как ee_admission).
create policy ee_next_rule_public_read on ee_next_rule
  for select using (
    exists (select 1 from programme p where p.id = ee_next_rule.programme_id)
  );

-- Права на запись у анонимного и вошедшего пользователя отозваны по
-- умолчанию миграцией 20261010120000; чтение — явно.
grant select on ee_next_rule to anon, authenticated;
