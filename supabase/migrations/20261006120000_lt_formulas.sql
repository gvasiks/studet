-- Литва, фаза 3: состав конкурсного балла (docs/PLAN-LITHUANIA-2027.md,
-- docs/checks/LT-PHASE3-SCORE-RULES.md).
--
-- В Литве правило расчёта одно на страну, а не своё у каждого вуза: балл
-- складывается из составляющих (до четырёх), у каждой вес и предмет или
-- список предметов на выбор. Наборов таких составляющих — «формул» — около
-- сорока на всю страну, и у каждой строки общего приёма стоит номер своей
-- формулы. Поэтому латвийская таблица formula (одна формула на программу,
-- своя шкала у каждого вуза) сюда не подходит — таблицы отдельные.
--
-- Источник — открытые файлы официального калькулятора LAMA BPO; пишет их
-- pipeline/src/lt_load_formulas.py.
--
-- ПОКАЗ ПОСЕТИТЕЛЯМ. Литовские факты показываются без подтверждения
-- человеком (решение владельца 2026-10-05), но расчёт балла — только после
-- сверки с официальным калькулятором (раздел 4 плана). Это условие стоит в
-- самой политике доступа: формула и её составляющие видны анонимному ключу,
-- только когда у формулы заполнено checked_at. Тот же приём, что verified_at
-- у латвийской formula: ключ публичный, и без политики прямой запрос к REST
-- API отдал бы непроверенную формулу в обход сайта.

create table lt_formula (
  id uuid primary key default gen_random_uuid(),
  -- год приёма, к которому относятся правила: файл калькулятора обновляется
  -- раз в год, прошлогодние формулы остаются в таблице
  admission_year integer not null check (admission_year between 2024 and 2100),
  -- номер формулы в файле калькулятора (поле i таблицы formulas)
  number text not null,
  source_url text not null,
  extracted_at timestamptz not null default now(),
  -- когда расчёт по этой формуле сверен с официальным калькулятором;
  -- пусто — формула посетителям не видна. Сбрасывается загрузчиком, если
  -- состав формулы в файле изменился.
  checked_at timestamptz,
  checked_note text,
  created_at timestamptz not null default now(),
  unique (admission_year, number)
);

create table lt_formula_component (
  id uuid primary key default gen_random_uuid(),
  formula_id uuid not null references lt_formula (id) on delete cascade,
  position integer not null check (position between 1 and 4),
  weight numeric(4, 2) not null check (weight > 0 and weight <= 1),
  -- one_of — один предмет из списка, какой выгоднее поступающему;
  -- average — среднее всех перечисленных (медицина и одонтология)
  mode text not null check (mode in ('one_of', 'average')),
  -- ключи предметов, как в pipeline/src/lt_formulas.py (SUBJECTS)
  subjects text[] not null check (array_length(subjects, 1) >= 1),
  unique (formula_id, position)
);

create index lt_formula_component_formula_id_idx on lt_formula_component (formula_id);

-- Строка общего приёма: программа в конкретной форме, расписании и
-- специализации. Несколько строк приёма могут вести в одну строку нашего
-- каталога (она объединяет расписания и специализации). Формула записана у
-- строки приёма, а не у программы: у разных специализаций одной программы
-- она изредка разная, и тогда расчёт для такой программы не показывается.
create table lt_admission_unit (
  id uuid primary key default gen_random_uuid(),
  programme_id uuid not null references programme (id) on delete cascade,
  admission_year integer not null check (admission_year between 2024 and 2100),
  -- номер строки в файле калькулятора (поле e)
  lamabpo_id text not null,
  formula_id uuid not null references lt_formula (id) on delete restrict,
  study_form text,
  schedule text,
  -- примечание вуза к строке приёма: язык, специализация, город
  note text,
  source_url text not null,
  extracted_at timestamptz not null default now(),
  unique (admission_year, lamabpo_id)
);

create index lt_admission_unit_programme_id_idx on lt_admission_unit (programme_id);
create index lt_admission_unit_formula_id_idx on lt_admission_unit (formula_id);

alter table lt_formula enable row level security;
alter table lt_formula_component enable row level security;
alter table lt_admission_unit enable row level security;

create policy lt_formula_public_read on lt_formula
  for select using (checked_at is not null);

create policy lt_formula_component_public_read on lt_formula_component
  for select using (
    exists (select 1 from lt_formula f where f.id = lt_formula_component.formula_id and f.checked_at is not null)
  );

-- Строка приёма сама по себе — открытый факт из списка программ (форма,
-- расписание, примечание). Номер формулы без самой формулы ничего не
-- раскрывает, поэтому строки видны всем; программа, скрытая политикой
-- таблицы programme, утянет за собой и их при соединении.
create policy lt_admission_unit_public_read on lt_admission_unit
  for select using (true);
