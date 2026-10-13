-- Эстония: последний конкурс программы — сроки подачи и ссылка на конкурс в
-- системе подачи SAIS (docs/PLAN-ESTONIA.md, фаза 6).
--
-- Государственный портал haridusportaal.edu.ee у программы хранит её
-- последний конкурс: начало и конец подачи заявлений и ссылку на страницу
-- конкурса в SAIS (sais.ee/AdmissionSearch/View/N). Конкурс не обязательно
-- открыт сейчас: на 2026-10-13 из 546 программ с конкурсом срок подачи ещё
-- не прошёл только у 16, у остальных это приём прошлого лета или раньше.
-- Открыт ли конкурс, видно по closes_at — сайт показывает срок как
-- действующий, только пока он не прошёл.
--
-- Почему не application_round и не application_channel: там латвийские
-- сроки и каналы подачи, которые подтверждает человек (правило 6), и без
-- подтверждения они не показываются. Эстонские факты берутся с портала как
-- есть и показываются с пометкой «извлечено автоматически» (решение
-- владельца 2026-10-11, как для Литвы).
--
-- Одна строка на программу каталога: портал называет у записи один конкурс
-- и заменяет его следующим. Когда конкурс с портала пропадает, загрузчик
-- строку удаляет.
--
-- Пишет pipeline/src/ee_load_admissions.py.

create table ee_admission (
  programme_id uuid primary key references programme (id) on delete cascade,
  admission_id integer not null,
  sais_url text not null check (sais_url ~ '^https://(www\.)?sais\.ee/'),
  opens_at timestamptz,
  closes_at timestamptz,
  source_url text not null,
  extracted_at timestamptz not null default now()
);

create index ee_admission_closes_at_idx on ee_admission (closes_at);

alter table ee_admission enable row level security;

-- Открытый факт с государственного портала — виден всем, но только пока
-- видна сама программа (аудит 2026-10-04).
create policy ee_admission_public_read on ee_admission
  for select using (
    exists (select 1 from programme p where p.id = ee_admission.programme_id)
  );

-- Права на запись у анонимного и вошедшего пользователя отозваны по
-- умолчанию миграцией 20261010120000; чтение — явно.
grant select on ee_admission to anon, authenticated;
