-- Что собрать для поступления — чек-лист документов по вузу и уровню
-- (docs/PLAN-FOREIGNERS.md, шаг 3). Независимая миграция: ссылается только
-- на university.
--
-- Одна строка — один документ, который вуз просит у иностранного
-- абитуриента на этом уровне, с условием «кому» и этапом «когда». Строка
-- видна публично только после того, как владелец проставит verified_at в
-- Studio (решение владельца 2026-11-14: списки документов в правило 6 не
-- входят, но показываются только подтверждёнными — как стоимость).
-- Черновики пишет pipeline/src/seed_document_requirements.py, у каждой
-- строки дословная цитата со страницы вуза.
--
-- Названия документов, условий и этапов — в словарях сайта по ключу; note —
-- уточнение на языке источника (английском), сайт его не переводит.

create table foreign_document_requirement (
  id uuid primary key default gen_random_uuid(),
  university_id uuid not null references university (id) on delete cascade,
  degree_level text not null check (degree_level in ('college', 'bachelor', 'master', 'doctoral')),
  -- ключ документа; список совпадает с DOCUMENT_KEYS в src/lib/foreign-documents.ts
  document text not null check (document in (
    'passport', 'photo', 'secondary_diploma', 'bachelor_diploma', 'transcript',
    'enrolment_letter', 'english_translation', 'legalisation', 'english_certificate',
    'motivation_letter', 'cv', 'recommendation_letters', 'criminal_record',
    'minor_documents', 'proof_of_funds', 'application_fee_receipt'
  )),
  -- кому нужен документ:
  --   all                    — всем иностранным абитуриентам этого уровня
  --   docs_issued_outside_eu — если документ об образовании выдан вне ЕС/ЕЭЗ/Швейцарии
  --                            (у РТУ — и вне Великобритании; это сказано в note)
  --   non_eu_citizens        — гражданам стран вне ЕС/ЕЭЗ/Швейцарии
  --   visa_required          — гражданам стран, которым для въезда нужна виза
  --   under_18               — несовершеннолетним
  --   final_year             — тем, кто ещё не окончил школу или вуз
  applies_to text not null default 'all' check (applies_to in (
    'all', 'docs_issued_outside_eu', 'non_eu_citizens', 'visa_required', 'under_18', 'final_year'
  )),
  -- когда: application — загрузить при подаче; before_arrival — подготовить до приезда
  stage text not null default 'application' check (stage in ('application', 'before_arrival')),
  -- уточнение на английском, языке источника: «on the RSU form», «notarised»…
  note text,
  sort_order integer not null default 0,
  source_url text not null,
  source_excerpt text not null,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (university_id, degree_level, document, applies_to)
);

create index foreign_document_requirement_university_id_idx on foreign_document_requirement (university_id);

create trigger foreign_document_requirement_set_updated_at
before update on foreign_document_requirement
for each row execute function set_updated_at();

-- RLS без исключений (OWASP A01); гейт на verified_at — в политике.
alter table foreign_document_requirement enable row level security;

create policy foreign_document_requirement_public_read on foreign_document_requirement
  for select using (verified_at is not null);

revoke insert, update, delete, truncate, references, trigger on foreign_document_requirement from anon, authenticated;

-- verified_by закрыт от публичного ключа (решение 2026-10-24): чтение — по колонкам.
revoke select on foreign_document_requirement from anon, authenticated;
grant select (
  id, university_id, degree_level, document, applies_to, stage, note, sort_order,
  source_url, source_excerpt, verified_at, created_at, updated_at
) on foreign_document_requirement to anon, authenticated;
