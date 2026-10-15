-- Эстония: правила конкурса (docs/PLAN-ESTONIA.md, раздел 9, шаги 7.1–7.2).
--
-- criteria_text — раздел «Vastuvõtukriteeriumid» со страницы конкурса SAIS
-- как есть, по-эстонски: из него разбирается правило, и по нему же видно,
-- почему правило пустое. info_url — ссылка «Rohkem infot» оттуда же: на
-- страницу программы на сайте вуза.
--
-- rule — разобранное правило, пока только у бакалавриата и цельного
-- обучения Тартуского университета и TalTech (pipeline/src/ee_rules.py,
-- там же форма):
--   {"model": "weighted", "variants": [[{"exam": "estonian", "weight": 40}, …]],
--    "apply_min": 66, "guarantee_min": 80, "wide_math_bonus": 16,
--    "medal_bonus": 3, "requirements": {"english": "B2"}}
--   {"model": "thresholds", "apply": {"math": 35, "estonian": 35, "estonian_second": 45},
--    "guarantee": {…}, "places": 60, "ranking": true, "wide_math": true}
-- NULL — правило не разобрано: вуз ещё не поддержан или в тексте есть
-- то, чего разборщик не понимает. Сайт тогда условий не показывает.
--
-- rule_source_url — страница вуза, с которой взяты пороги (у ТÜ — ut.ee);
-- у TalTech всё правило со страницы SAIS, колонка пустая.
--
-- Факты без подтверждения человеком, с пометкой «извлечено автоматически»
-- (решение владельца 2026-10-11, как в Литве).
--
-- Права доступа не меняются: колонки публичные, как соседние.
-- Пишут pipeline/src/ee_load_admission_details.py (текст и ссылка) и
-- pipeline/src/ee_load_rules.py (правило).

alter table ee_admission
  add column criteria_text text,
  add column info_url text,
  add column rule jsonb check (rule is null or jsonb_typeof(rule) = 'object'),
  add column rule_source_url text,
  add column rule_extracted_at timestamptz;

comment on column ee_admission.criteria_text is 'Раздел «Vastuvõtukriteeriumid» со страницы SAIS, по-эстонски, как есть.';
comment on column ee_admission.info_url is 'Ссылка «Rohkem infot» из условий SAIS — страница программы на сайте вуза.';
comment on column ee_admission.rule is 'Разобранное правило конкурса — см. описание в миграции; NULL — не разобрано.';
comment on column ee_admission.rule_source_url is 'Страница вуза, откуда взяты пороги (ut.ee); у TalTech пусто.';
comment on column ee_admission.rule_extracted_at is 'Когда правило разобрано; NULL — ещё не разбиралось.';
