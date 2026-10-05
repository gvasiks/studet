-- Литовский каталог (фаза 2, docs/PLAN-LITHUANIA-2027.md).
--
-- Что меняется:
-- 1. Название на литовском у вуза и программы. Правило то же, что было:
--    у записи обязано быть название хотя бы на одном языке.
-- 2. Степень и описание программы на литовском — как у латвийских
--    degree_awarded_lv / description_lv.
-- 3. Язык обучения: к латышскому и английскому добавляются литовский и
--    языки, которые государственный реестр Литвы называет у программ.
-- 4. Тип финансирования может быть пустым. В Литве бюджетные места делятся
--    по группам направлений, а не по программам, и ни один из источников
--    не говорит, есть ли они у конкретной программы. Пустое значение —
--    «источник не сообщает»; угадывать 'both' было бы выдуманным фактом.
--    У латвийских программ значение по-прежнему заполняет сборщик.
--
-- Права доступа (RLS) не меняются: новые колонки публичные, как соседние.
-- Существующие строки не затрагиваются.

alter table university add column name_lt text;
alter table university alter column name_lv drop not null;
alter table university
  add constraint university_name_present
  check (name_lv is not null or name_lt is not null);

alter table programme
  add column name_lt text,
  add column description_lt text,
  add column degree_awarded_lt text;

alter table programme drop constraint programme_name_present;
alter table programme
  add constraint programme_name_present
  check (name_lv is not null or name_en is not null or name_lt is not null);

alter table programme drop constraint programme_language_of_instruction_check;
alter table programme
  add constraint programme_language_of_instruction_check
  check (language_of_instruction in ('lv', 'en', 'lt', 'ru', 'pl', 'de', 'fr'));

alter table programme alter column funding_type drop not null;

comment on column university.name_lt is 'Название на литовском — у литовских учреждений.';
comment on column programme.name_lt is 'Название на литовском — у литовских программ.';
comment on column programme.funding_type is
  'budget | paid | both. NULL — источник не сообщает (литовские программы).';
