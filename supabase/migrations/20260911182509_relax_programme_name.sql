-- Обнаружено при подключении первого источника (Turība, английский раздел сайта):
-- у части программ пока известно только английское название. name_lv остаётся
-- приоритетным для аудитории А, но не может быть обязательным на уровне БД.
alter table programme alter column name_lv drop not null;
alter table programme add constraint programme_name_present
  check (name_lv is not null or name_en is not null);

-- Когда конвейер последний раз трогал запись — отдельно от verified_at
-- (тот значит «человек подтвердил», этот — «источник данных дал этот срез»).
alter table university add column extracted_at timestamptz;
alter table programme add column extracted_at timestamptz;
