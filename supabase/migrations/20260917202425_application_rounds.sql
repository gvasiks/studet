-- Дедлайны подачи — ревью 2026-09, пункт 04. Заменяет неиспользуемый
-- programme.application_deadline (ни один сборщик его не заполнял, ни
-- один экран не читал — мёртвое поле с самого начала).
--
-- Дедлайн — это факт про приёмную кампанию вуза на определённом уровне
-- обучения (иногда ещё и в разрезе языка обучения — см. ниже), а не про
-- отдельную программу: сайт Turiba прямо это подтверждает — общая
-- таблица дат на одной странице, не по каждой программе своя (см.
-- комментарий в pipeline/src/sources/turiba.py). Поэтому отдельная
-- таблица со своим university_id, а не колонка на programme: так не
-- нужно трогать все 339 существующих строк программ, а совпадение
-- ищется на лету по (university_id, degree_level, language_of_instruction).
create table application_round (
  id uuid primary key default gen_random_uuid(),
  university_id uuid not null references university (id) on delete cascade,
  -- null = относится ко всем уровням/языкам вуза; иначе должно совпадать
  -- со значением programme.degree_level / programme.language_of_instruction
  degree_level text,
  language_of_instruction text check (language_of_instruction in ('lv', 'en')),
  -- "1. kārta", "vasaras uzņemšana", "Autumn intake" — то, что показываем
  -- рядом с датами, чтобы было понятно, к какому набору они относятся
  label text not null,
  opens_on date,
  closes_on date,
  note text,
  source_url text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  -- Даёт seed_deadlines.py естественный ключ конфликта для upsert
  -- (повторный запуск не плодит дубли и не трогает verified_at, если
  -- сам upsert не передаёт это поле — тот же приём, что и в
  -- seed_formulas.py).
  unique (university_id, label)
);

create index application_round_university_id_idx on application_round (university_id);

create trigger application_round_set_updated_at
before update on application_round
for each row execute function set_updated_at();

-- Гейт на verified_at сразу в политике, а не только в запросе
-- приложения — тот же паттерн, что и formula_public_read
-- (20260917163249_gate_unverified_formulas.sql). anon key публичный,
-- без этого прямой запрос к REST API в обход Next.js всё равно вернул
-- бы неподтверждённые даты (правило 6 CLAUDE.md: дедлайн подтверждает
-- только человек через Supabase Studio).
alter table application_round enable row level security;

create policy application_round_public_read on application_round
  for select using (verified_at is not null);

alter table programme drop column application_deadline;
