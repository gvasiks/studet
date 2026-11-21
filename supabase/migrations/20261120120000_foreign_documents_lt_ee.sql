-- Списки документов для иностранцев у Литвы и Эстонии (решение владельца
-- 2026-11-19, docs/PLAN-FOREIGNERS.md, Р1): факты этих стран показываются без
-- подтверждения человеком, с пометкой «извлечено автоматически» — как
-- остальные литовские и эстонские факты. У Латвии всё как было: строка видна
-- только после verified_at (правило 6 и решение 2026-11-14).
-- Применять после 20261114140000_english_requirement.sql.

-- 1. Новый ключ документа: академическое признание иностранного образования
--    вне Латвии (в Литве его делает вуз или SKVC; у Латвии — aic_statement).
--    Список совпадает с DOCUMENT_KEYS в src/lib/foreign-documents.ts.
alter table foreign_document_requirement drop constraint foreign_document_requirement_document_check;

alter table foreign_document_requirement add constraint foreign_document_requirement_document_check
  check (document in (
    'passport', 'photo', 'secondary_diploma', 'bachelor_diploma', 'transcript',
    'enrolment_letter', 'english_translation', 'legalisation', 'aic_statement', 'recognition',
    'english_certificate', 'motivation_letter', 'cv', 'recommendation_letters', 'criminal_record',
    'minor_documents', 'proof_of_funds', 'application_fee_receipt'
  ));

-- 2. Публичное чтение: подтверждённые строки любого вуза, неподтверждённые —
--    только у вузов Литвы и Эстонии. Страна берётся из university (её колонки
--    country и id открыты публичному ключу). RLS остаётся включённой (A01).
drop policy foreign_document_requirement_public_read on foreign_document_requirement;

create policy foreign_document_requirement_public_read on foreign_document_requirement
  for select using (
    verified_at is not null
    or exists (
      select 1 from university
      where university.id = foreign_document_requirement.university_id
        and university.country in ('LT', 'EE')
    )
  );
