-- Ревью 2026-09, пункт 06: различить «у вуза нет конкурсного балла»
-- и «мы его ещё не собрали». Сейчас программа без формулы выглядит
-- одинаково пусто в обоих случаях — а у восьми из четырнадцати вузов
-- (все частные) конкурсного балла нет в принципе, это факт об их
-- приёме, а не наш недоработанный участок.
--
-- Уровень вуза, не программы: сама характеристика "как здесь поступают"
-- задаётся приёмной политикой вуза в целом, не отдельной программой
-- (как и с application_round — см. её миграцию). Отдельная таблица,
-- а не колонка на university: та же причина, что и с application_round
-- — university_public_read сейчас открыт всем без гейта на verified_at,
-- расширять эту политику ради одного нового поля рискованнее, чем
-- завести таблицу со своей политикой с нуля.
create table university_admission_type (
  university_id uuid primary key references university (id) on delete cascade,
  selection_type text not null check (
    selection_type in ('competitive_score', 'entrance_exam', 'open_admission', 'interview')
  ),
  source_url text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger university_admission_type_set_updated_at
before update on university_admission_type
for each row execute function set_updated_at();

alter table university_admission_type enable row level security;

-- Гейт на verified_at — тот же паттерн, что и application_round/formula:
-- anon key публичный, без политики прямой запрос к REST API в обход
-- Next.js вернул бы неподтверждённую классификацию.
create policy university_admission_type_public_read on university_admission_type
  for select using (verified_at is not null);
