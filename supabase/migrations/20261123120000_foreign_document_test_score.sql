-- Чек-лист документов для иностранцев: новый ключ test_score — отчёт о
-- результате вступительного теста (GRE General Test у магистратур TalTech).
-- Решение владельца 2026-11-23: «Да, только Эстония» — документы для
-- английских магистратур Эстонии. Ключ совпадает с DOCUMENT_KEYS в
-- src/lib/foreign-documents.ts и DOCUMENTS в pipeline/src/seed_document_requirements.py.
-- Применять после 20261120120000_foreign_documents_lt_ee.sql.

alter table foreign_document_requirement drop constraint foreign_document_requirement_document_check;

alter table foreign_document_requirement add constraint foreign_document_requirement_document_check
  check (document in (
    'passport', 'photo', 'secondary_diploma', 'bachelor_diploma', 'transcript',
    'enrolment_letter', 'english_translation', 'legalisation', 'aic_statement', 'recognition',
    'english_certificate', 'test_score', 'motivation_letter', 'cv', 'recommendation_letters', 'criminal_record',
    'minor_documents', 'proof_of_funds', 'application_fee_receipt'
  ));
