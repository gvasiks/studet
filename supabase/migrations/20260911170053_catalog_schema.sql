-- Каталог: вузы, программы, требования по экзаменам.
-- Конкурсные формулы сюда не входят — отдельная миграция в выпуске 2
-- (схема описана в docs/PLAN.md, раздел 6).

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table university (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name_lv text not null,
  name_en text,
  kind text not null check (kind in ('public', 'private')),
  -- известные на сентябрь 2026: riga, daugavpils, valmiera, ventspils, jelgava, liepaja
  city text not null,
  website_url text,
  source_url text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger university_set_updated_at
before update on university
for each row execute function set_updated_at();

create table programme (
  id uuid primary key default gen_random_uuid(),
  university_id uuid not null references university (id) on delete cascade,
  slug text not null,
  name_lv text not null,
  name_en text,
  -- свободный текст, не enum: точный список уровней ещё не переписан
  -- (bakalaura, profesionālā bakalaura, maģistra, doktora, koledžas...)
  degree_level text not null,
  language_of_instruction text not null check (language_of_instruction in ('lv', 'en')),
  study_mode text not null check (study_mode in ('full_time', 'part_time', 'distance')),
  -- переопределяет city вуза для филиалов (например, Turība в Лиепае); null = город вуза
  city text,
  funding_type text not null check (funding_type in ('budget', 'paid', 'both')),
  tuition_fee_amount numeric(10, 2),
  tuition_fee_currency text not null default 'EUR',
  budget_places integer,
  application_deadline date,
  duration_years numeric(3, 1),
  accreditation_valid_until date,
  description_lv text,
  description_en text,
  source_url text,
  verified_at timestamptz,
  verified_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (university_id, slug)
);

create index programme_university_id_idx on programme (university_id);

create trigger programme_set_updated_at
before update on programme
for each row execute function set_updated_at();

create table programme_requirement (
  id uuid primary key default gen_random_uuid(),
  programme_id uuid not null references programme (id) on delete cascade,
  -- mathematics, latvian, english, physics, chemistry, biology, history...
  subject text not null,
  -- augstakais | optimalais | vispaarigais; null = уровень не важен
  min_level text,
  -- строки с одинаковым значением — взаимозаменяемые варианты ("любой из");
  -- null = предмет обязателен сам по себе
  alternative_group text,
  note text,
  created_at timestamptz not null default now()
);

create index programme_requirement_programme_id_idx on programme_requirement (programme_id);

-- RLS без исключений (OWASP A01). Каталог публичный, персональных данных нет —
-- открываем чтение всем; запись оставляем только сервисному ключу (Python)
-- и владельцу БД через Supabase Studio, отдельных политик на запись нет.
alter table university enable row level security;
alter table programme enable row level security;
alter table programme_requirement enable row level security;

create policy university_public_read on university for select using (true);
create policy programme_public_read on programme for select using (true);
create policy programme_requirement_public_read on programme_requirement for select using (true);
