-- Чек-лист документов: новый ключ aic_statement — справка Академического
-- информационного центра (aic.lv) о признании иностранного образования.
-- RISEBA просит её приложить к заявлению (правила приёма 2026/2027); у ЛУ и
-- RSU справку запрашивает сам вуз, поэтому у них такой строки нет.
-- Применять после 20261114120000_foreign_document_requirement.sql.
-- Список совпадает с DOCUMENT_KEYS в src/lib/foreign-documents.ts.

alter table foreign_document_requirement drop constraint foreign_document_requirement_document_check;

alter table foreign_document_requirement add constraint foreign_document_requirement_document_check
  check (document in (
    'passport', 'photo', 'secondary_diploma', 'bachelor_diploma', 'transcript',
    'enrolment_letter', 'english_translation', 'legalisation', 'aic_statement', 'english_certificate',
    'motivation_letter', 'cv', 'recommendation_letters', 'criminal_record',
    'minor_documents', 'proof_of_funds', 'application_fee_receipt'
  ));
