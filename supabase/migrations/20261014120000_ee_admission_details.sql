-- Эстония: условия конкурса со страницы SAIS (docs/PLAN-ESTONIA.md, фаза 6).
--
-- Государственный портал называет у программы только сроки и ссылку на
-- конкурс. Сама страница конкурса в SAIS (sais.ee/AdmissionSearch/View/N,
-- открыта без входа) сообщает то, чего в данных портала нет: форму обучения,
-- место учёбы, начало занятий, нагрузку и финансирование с ценой.
--
-- Значения хранятся как на странице, по-эстонски (study_form — «päevane
-- õpe», «sessioonõpe»; location — «Tallinn», «Reola küla, Tartumaa»): форм
-- обучения и мест немного, но закрытого списка у SAIS нет, и подставлять
-- ближайшее знакомое значение было бы догадкой. Сайт переводит знакомые
-- значения, незнакомые показывает как есть.
--
-- funding — список вариантов нагрузки, каждый со своим финансированием:
--   [{"load": "full" | "part" | "unspecified",
--     "paid": true | false,
--     "prices": [{"amount": 1050, "currency": "EUR",
--                 "period": "semester" | "year" | "credit" | "other",
--                 "period_text": "semester", "target": "Kõik" | null}]}]
-- У одного конкурса бывает несколько вариантов (полная нагрузка бесплатно,
-- неполная платно), поэтому это список, а не две колонки.
--
-- У большинства программ конкурс прошлый (см. 20261013120000): это условия
-- прошлого приёма, и сайт так их и подписывает.
--
-- Права доступа не меняются: колонки публичные, как соседние.
-- Пишет pipeline/src/ee_load_admission_details.py.

alter table ee_admission
  add column title text,
  add column study_form text,
  add column location text,
  add column starts_on date,
  add column funding jsonb check (funding is null or jsonb_typeof(funding) = 'array'),
  add column details_fetched_at timestamptz;

comment on column ee_admission.title is 'Название конкурса на странице SAIS, по-эстонски.';
comment on column ee_admission.study_form is 'Форма обучения как на странице SAIS: «päevane õpe», «sessioonõpe».';
comment on column ee_admission.location is 'Место учёбы как на странице SAIS, без страны.';
comment on column ee_admission.funding is 'Варианты нагрузки с финансированием и ценами — см. описание в миграции.';
comment on column ee_admission.details_fetched_at is 'Когда страница конкурса в SAIS была прочитана; NULL — ещё не читалась.';
