-- Комментарий владельца к USER-STORIES (2026-09-30): «В карточке программы
-- необходимо ещё найти и указать описание программы и название получаемого
-- диплома». Решение 2026-10-01: брать автоматически из NIID.lv, показывать с
-- пометкой «извлечено автоматически».
--
-- На странице программы в NIID это три отдельных поля:
--   Grāds                      -> degree_awarded_lv   («Profesionālais bakalaurs mehatronikā»)
--   Profesionālā kvalifikācija -> qualification_lv    («Mehatronikas inženieris (6. PKL)»)
--   Izglītības dokuments       -> diploma_document_lv («Profesionālā bakalaura diploms un …»)
-- Все три — официальные латышские названия, поэтому с суффиксом _lv и без
-- английской пары: переводить название диплома сами мы не вправе.
--
-- Описание пишется в уже существующую колонку description_lv.
--
-- details_source_url / details_extracted_at — правило 5 CLAUDE.md: у факта
-- должны быть источник и дата. Отдельно от programme.source_url и
-- extracted_at, потому что эти сведения собирает другой скрипт
-- (pipeline/src/enrich_niid_details.py) и в другой день, а у программ с
-- собственным сборщиком вуза источник сведений о дипломе может оказаться
-- не тем же адресом, что источник самой программы.
--
-- Это не поля правила 6: подтверждения человеком не требуют, показываются
-- с пометкой об автоматическом извлечении. RLS таблицы programme уже
-- включён и действует на новые колонки так же, как на старые.
--
-- "if not exists" — миграцию можно запускать повторно.
alter table programme
  add column if not exists degree_awarded_lv text,
  add column if not exists qualification_lv text,
  add column if not exists diploma_document_lv text,
  add column if not exists details_source_url text,
  add column if not exists details_extracted_at timestamptz;
