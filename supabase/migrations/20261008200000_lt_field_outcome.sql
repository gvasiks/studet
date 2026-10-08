-- Литва, фаза 4: что стало с выпускниками — по направлению и ступени.
--
-- Источник — приложение № 4 к проекту постановления правительства Литвы о
-- местах за счёт государства на 2026 год (министерство образования,
-- 2026-02-19, данные NŠA): выпускники 2021/22–2023/24 учебных годов, не
-- продолжившие учёбу, через 12 месяцев после окончания. Строка источника —
-- направление на ступени ПО ВСЕЙ СТРАНЕ: разреза по вузам и программам и
-- числа выпускников в нём нет. Поэтому таблица привязана к направлению
-- (lt_programme_field.field_code) и уровню программы, а не к программе.
--
-- Строки, где доля работающих равна ровно 0 % или 100 %, загрузчик не
-- пишет: такие значения дают только очень маленькие группы. Пишет
-- pipeline/src/lt_load_field_outcomes.py из файла docs/sources/lt/.

create table lt_field_outcome (
  degree_level text not null check (degree_level in ('bachelor', 'college', 'integrated')),
  field_code text not null check (field_code ~ '^[A-Z][0-9]{2}$'),
  -- название направления, как оно стоит в источнике
  field_name text not null,
  -- годы выпуска, по которым посчитаны показатели
  cohort_from integer not null check (cohort_from between 2015 and 2100),
  cohort_to integer not null check (cohort_to between cohort_from and 2100),
  -- доля работающих по найму или на себя — от тех, кто должен работать
  employed_percent numeric(5, 2) not null check (employed_percent > 0 and employed_percent < 100),
  -- доля работающих там, где нужна квалификация высшего образования
  qualified_percent numeric(5, 2) not null check (qualified_percent > 0 and qualified_percent < 100),
  -- средний доход в процентах от среднего дохода выпускников этой ступени
  income_percent numeric(6, 2) not null check (income_percent > 0),
  -- сам средний доход ступени, евро — как в источнике
  level_average_income_eur integer not null check (level_average_income_eur > 0),
  source_url text not null,
  published_on date not null,
  extracted_at timestamptz not null default now(),
  primary key (degree_level, field_code, cohort_to)
);

alter table lt_field_outcome enable row level security;

-- Опубликованные показатели по направлению — видны всем.
create policy lt_field_outcome_public_read on lt_field_outcome
  for select using (true);
