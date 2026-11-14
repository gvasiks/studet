-- Требования к английскому у программ на английском (docs/PLAN-FOREIGNERS.md,
-- шаг 4) и третий этап чек-листа документов — «вуз делает это сам».
-- Применять после 20261114130000_foreign_document_aic_statement.sql.
--
-- 1. english_requirement. Языковое требование — поле правила 6 CLAUDE.md:
--    строка видна публично только после того, как владелец проставит
--    verified_at в Studio. Черновики пишет pipeline/src/seed_english_requirements.py.
--    Строка — на вуз и уровень (programme_id пустой) или на одну программу;
--    строка программы важнее строки вуза (src/lib/english-requirement.ts).
--    Храним только IELTS и TOEFL iBT: остальные тесты — по ссылке на страницу
--    вуза (решение владельца 2026-11-14, «чем жертвуем»).
--    TOEFL iBT с 21.01.2026 считается и по новой шкале 1–6 — toefl_ibt_band.

create table english_requirement (
  id uuid primary key default gen_random_uuid(),
  university_id uuid not null references university (id) on delete cascade,
  degree_level text not null check (degree_level in ('college', 'bachelor', 'master', 'doctoral')),
  -- пусто — требование вуза для всего уровня; иначе — только этой программы
  programme_id uuid references programme (id) on delete cascade,
  ielts_min numeric(3, 1) check (ielts_min between 0 and 9),
  toefl_ibt_min integer check (toefl_ibt_min between 0 and 120),
  -- минимум по новой шкале TOEFL iBT (1–6), если вуз его называет
  toefl_ibt_band numeric(2, 1) check (toefl_ibt_band between 1 and 6),
  -- уточнение на английском, языке источника
  note text,
  source_url text not null,
  source_excerpt text not null,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (ielts_min is not null or toefl_ibt_min is not null),
  unique nulls not distinct (university_id, degree_level, programme_id)
);

create index english_requirement_university_id_idx on english_requirement (university_id);

create trigger english_requirement_set_updated_at
before update on english_requirement
for each row execute function set_updated_at();

alter table english_requirement enable row level security;

create policy english_requirement_public_read on english_requirement
  for select using (verified_at is not null);

revoke insert, update, delete, truncate, references, trigger on english_requirement from anon, authenticated;

revoke select on english_requirement from anon, authenticated;
grant select (
  id, university_id, degree_level, programme_id, ielts_min, toefl_ibt_min, toefl_ibt_band, note,
  source_url, source_excerpt, verified_at, created_at, updated_at
) on english_requirement to anon, authenticated;

-- 2. Чек-лист документов: этап by_university — то, что вуз делает за
--    абитуриента (например, сам запрашивает справку AIC о признании
--    образования). На карточке такие строки идут отдельной группой, без отметок.

alter table foreign_document_requirement drop constraint foreign_document_requirement_stage_check;

alter table foreign_document_requirement add constraint foreign_document_requirement_stage_check
  check (stage in ('application', 'before_arrival', 'by_university'));
