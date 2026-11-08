-- Стоимость года для иностранных абитуриентов (выпуск 4, начат досрочно:
-- решение владельца 2026-11-08, docs/PLAN-FOREIGNERS.md, шаг 1).
--
-- Две таблицы фактов. Обе — поля правила 6 CLAUDE.md (стоимость
-- подтверждает только человек), поэтому устроены как application_channel:
-- конвейер пишет черновик с источником и дословной цитатой, публично строка
-- видна только после того, как владелец проставит verified_at в Studio.
--
-- country_cost — суммы, общие для страны: пошлины за ВНЖ, сумма
--   подтверждения средств. Источник — правила Кабинета министров.
--   Черновики пишет pipeline/src/seed_country_costs.py.
-- programme_fee — плата за обучение программы отдельно для граждан ЕС/ЕЭЗ
--   и для остальных, плюс разовые взносы вуза. Одной цены
--   programme.tuition_fee_amount для иностранцев мало: у частных вузов цена
--   для не-ЕС часто другая.
--
-- applies_to: eu — граждане ЕС, ЕЭЗ и Швейцарии; non_eu — все остальные.

create table country_cost (
  id uuid primary key default gen_random_uuid(),
  country text not null check (country in ('LV', 'LT', 'EE')),
  -- residence_permit_review       — рассмотрение документов на ВНЖ (обычный срок)
  -- residence_permit_registration — регистрация ВНЖ (обычный срок)
  -- long_stay_visa                — рассмотрение документов на долгосрочную визу
  -- means_per_month               — сколько средств в месяц нужно подтвердить
  code text not null check (
    code in ('residence_permit_review', 'residence_permit_registration', 'long_stay_visa', 'means_per_month')
  ),
  applies_to text not null check (applies_to in ('eu', 'non_eu')),
  amount numeric(10, 2) not null check (amount >= 0),
  currency text not null default 'EUR',
  -- once — разово; month — в месяц
  period text not null check (period in ('once', 'month')),
  -- с какой даты сумма действует; суммы меняются (минимальная зарплата —
  -- каждый январь, пошлины — новыми правилами), старая строка закрывается
  -- valid_to, а не переписывается
  valid_from date not null,
  valid_to date,
  -- норма: «MK noteikumi Nr. 731, 5.1.1. apakšpunkts» — показывается рядом с суммой
  source_title text not null,
  source_url text not null,
  source_excerpt text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (country, code, applies_to, valid_from)
);

create trigger country_cost_set_updated_at
before update on country_cost
for each row execute function set_updated_at();

create table programme_fee (
  id uuid primary key default gen_random_uuid(),
  programme_id uuid not null references programme (id) on delete cascade,
  -- tuition — плата за обучение; application_fee — плата за рассмотрение
  -- заявления; enrolment_fee — взнос при зачислении
  kind text not null check (kind in ('tuition', 'application_fee', 'enrolment_fee')),
  applies_to text not null check (applies_to in ('eu', 'non_eu')),
  amount numeric(10, 2) not null check (amount >= 0),
  currency text not null default 'EUR',
  -- year — за учебный год; once — разово
  period text not null check (period in ('year', 'once')),
  -- учебный год, к которому относится цена: '2027/28'
  academic_year text not null check (academic_year ~ '^\d{4}/\d{2}$'),
  source_url text not null,
  source_excerpt text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (programme_id, kind, applies_to, academic_year)
);

create index programme_fee_programme_id_idx on programme_fee (programme_id);

create trigger programme_fee_set_updated_at
before update on programme_fee
for each row execute function set_updated_at();

-- RLS без исключений (OWASP A01). Гейт на verified_at — в самой политике,
-- как у application_channel: anon-ключ публичный, без него прямой запрос к
-- REST API в обход сайта вернул бы неподтверждённую сумму.
alter table country_cost enable row level security;
alter table programme_fee enable row level security;

create policy country_cost_public_read on country_cost
  for select using (verified_at is not null);
-- Плата программы, пропавшей с сайта вуза, скрыта вместе с ней: подзапрос
-- к programme выполняется с правами читающего (как в 20261010120000).
create policy programme_fee_public_read on programme_fee
  for select using (
    verified_at is not null
    and exists (select 1 from programme p where p.id = programme_fee.programme_id)
  );

-- Запись — только сервисному ключу и владельцу в Studio. Права по умолчанию
-- уже сняты (20261010120000); повторяем явно — второй рубеж не зависит от
-- того, под какой ролью применена миграция.
revoke insert, update, delete, truncate, references, trigger
  on country_cost, programme_fee
  from anon, authenticated;

-- verified_by закрыт от публичного ключа (решение 2026-10-24): право чтения —
-- по колонкам. Новой колонке нужен свой grant select.
revoke select on country_cost, programme_fee from anon, authenticated;
grant select (
  id, country, code, applies_to, amount, currency, period, valid_from, valid_to,
  source_title, source_url, source_excerpt, verified_at, created_at, updated_at
) on country_cost to anon, authenticated;
grant select (
  id, programme_id, kind, applies_to, amount, currency, period, academic_year,
  source_url, source_excerpt, verified_at, created_at, updated_at
) on programme_fee to anon, authenticated;
