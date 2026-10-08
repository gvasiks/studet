-- Литва, фаза 4: цифры прошлого приёма по программе.
--
-- Источник — открытый набор LAMA BPO на data.gov.lt (набор 2914): каждая
-- строка заявления с этапом приёма, номером приоритета, видом места и
-- отметками «приглашён» и «подписал договор». В набор входят обезличенные,
-- но построчные данные о людях, поэтому в базу попадают ТОЛЬКО суммы по
-- программе: ни идентификаторов людей, ни заявлений здесь нет. Считает
-- pipeline/src/lt_load_admission_stats.py, читая файл потоком и не сохраняя.
--
-- Чего в источнике нет и чего нет в таблице: проходных баллов и числа мест
-- по программе (бюджетные места в Литве делятся по направлениям). Поэтому
-- блок на карточке — факты прошлого приёма без оценки шансов.

-- Государственный код программы («6011GX004») из карточки реестра AIKOS.
-- По нему строка приёма находится в открытом наборе: номера калькулятора и
-- идентификаторы набора между собой не совпадают.
alter table lt_admission_unit
  add column state_code text check (state_code ~ '^[0-9A-Z]{9}$');

create table lt_admission_stat (
  programme_id uuid not null references programme (id) on delete cascade,
  admission_year integer not null check (admission_year between 2024 and 2100),
  -- state — место за счёт государства (VF), stipend — место со стипендией
  -- на обучение в негосударственной школе (ST), paid — платное (VNF)
  funding text not null check (funding in ('state', 'stipend', 'paid')),
  -- Только основной приём (pagrindinis priėmimas). Одна программа в одном
  -- заявлении на место одного вида — одна строка набора.
  applications integer not null check (applications >= 0),
  first_priority integer not null check (first_priority between 0 and applications),
  invited integer not null check (invited between 0 and applications),
  signed integer not null check (signed between 0 and invited),
  source_url text not null,
  extracted_at timestamptz not null default now(),
  primary key (programme_id, admission_year, funding)
);

alter table lt_admission_stat enable row level security;

-- Суммы из открытого набора — видны всем, как и сама программа.
create policy lt_admission_stat_public_read on lt_admission_stat
  for select using (true);
