-- Жильё в общежитии вуза — диапазоном и с источником (docs/PLAN-FOREIGNERS.md,
-- шаг 1: «Жильё — диапазоном и с источником… Где источника нет, строки нет»).
-- Применять после 20261108120000_foreign_costs.sql.
--
-- Одна строка — цена места в общежитиях вуза за месяц, от самой дешёвой
-- комнаты до самой дорогой, по странице вуза. Стоимость — поле правила 6:
-- строка видна публично только после того, как владелец проставит
-- verified_at в Studio. Черновики пишет pipeline/src/seed_housing_costs.py.
--
-- Своей оценки аренды на рынке здесь нет и не будет (правило 5): только то,
-- что вуз публикует о своих общежитиях.

create table housing_cost (
  id uuid primary key default gen_random_uuid(),
  university_id uuid not null references university (id) on delete cascade,
  amount_min numeric(10, 2) not null check (amount_min >= 0),
  amount_max numeric(10, 2) not null check (amount_max >= amount_min),
  currency text not null default 'EUR',
  -- цена за место в месяц; другие периоды появятся вместе с источником, которому они нужны
  period text not null default 'month' check (period in ('month')),
  -- с какой даты цены действуют; новые цены — новой строкой
  valid_from date not null,
  -- что на странице: «LU dormitories, rental fees per month»
  source_title text not null,
  source_url text not null,
  source_excerpt text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (university_id, valid_from)
);

create trigger housing_cost_set_updated_at
before update on housing_cost
for each row execute function set_updated_at();

-- RLS без исключений (OWASP A01); гейт на verified_at — в политике.
alter table housing_cost enable row level security;

create policy housing_cost_public_read on housing_cost
  for select using (verified_at is not null);

revoke insert, update, delete, truncate, references, trigger on housing_cost from anon, authenticated;

-- verified_by закрыт от публичного ключа (решение 2026-10-24): чтение — по колонкам.
revoke select on housing_cost from anon, authenticated;
grant select (
  id, university_id, amount_min, amount_max, currency, period, valid_from,
  source_title, source_url, source_excerpt, verified_at, created_at, updated_at
) on housing_cost to anon, authenticated;
