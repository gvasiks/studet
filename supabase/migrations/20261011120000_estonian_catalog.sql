-- Эстонский каталог (фаза 1, docs/PLAN-ESTONIA.md).
--
-- Что меняется:
-- 1. Страна вуза: к 'LV' и 'LT' добавляется 'EE'.
-- 2. Название на эстонском у вуза и программы. Правило прежнее: у записи
--    обязано быть название хотя бы на одном языке.
-- 3. Степень и описание программы на эстонском — как degree_awarded_lt /
--    description_lt у литовских.
-- 4. Язык обучения: добавляется эстонский ('et').
-- 5. Форма обучения может быть пустой. Государственный портал Эстонии, из
--    которого берётся каталог, формы обучения не сообщает: она указана
--    только на странице конкурса в системе подачи SAIS, а конкурс открыт не
--    у каждой программы. Пустое значение — «источник не сообщает»;
--    подставлять 'full_time' было бы выдуманным фактом. У латвийских и
--    литовских программ значение по-прежнему заполняет сборщик.
--
-- Права доступа (RLS) не меняются: новые колонки публичные, как соседние.
-- Существующие строки не затрагиваются.

alter table university drop constraint university_country_check;
alter table university
  add constraint university_country_check
  check (country in ('LV', 'LT', 'EE'));

alter table university add column name_et text;
alter table university drop constraint university_name_present;
alter table university
  add constraint university_name_present
  check (name_lv is not null or name_lt is not null or name_et is not null);

alter table programme
  add column name_et text,
  add column description_et text,
  add column degree_awarded_et text;

alter table programme drop constraint programme_name_present;
alter table programme
  add constraint programme_name_present
  check (name_lv is not null or name_en is not null or name_lt is not null or name_et is not null);

alter table programme drop constraint programme_language_of_instruction_check;
alter table programme
  add constraint programme_language_of_instruction_check
  check (language_of_instruction in ('lv', 'en', 'lt', 'ru', 'pl', 'de', 'fr', 'et'));

alter table programme alter column study_mode drop not null;

comment on column university.name_et is 'Название на эстонском — у эстонских учреждений.';
comment on column programme.name_et is 'Название на эстонском — у эстонских программ.';
comment on column programme.study_mode is
  'full_time | part_time | distance. NULL — источник не сообщает (эстонские программы без открытого конкурса).';
