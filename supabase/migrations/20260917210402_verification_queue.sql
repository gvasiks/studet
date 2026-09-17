-- Ревью 2026-09, пункт 03: очередь верификации вместо блуждания по
-- Supabase Studio. Список того, что ещё не подтверждено, с датой сбора
-- и ссылкой на источник — подтверждает (verified_at) по-прежнему
-- только человек через Studio (правило 6), это view только показывает,
-- что осталось, само ничего не пишет.
--
-- Почему view, а не прямой запрос из Next.js: formula/application_round/
-- university_admission_type гейтятся RLS-политикой "verified_at is not
-- null" — анонимный ключ в принципе не видит неподтверждённые строки,
-- и это правильно для публичных страниц. Очереди же нужно видеть ровно
-- обратное — то, что ЕЩЁ не подтверждено. View создаётся ролью
-- миграции и по умолчанию читает исходные таблицы в её правах, минуя
-- RLS этих таблиц (стандартное поведение Postgres для views без
-- security_invoker) — то есть отбор "какие строки показать" делается
-- внутри view (where verified_at is null), а не полагается на RLS
-- источника.
--
-- Отсюда и узкий список колонок: только то, что не является самим
-- неподтверждённым фактом — id, тип факта, к какой программе/вузу
-- относится, когда собран, ссылка на источник. Ни коэффициентов
-- формулы, ни дат раунда, ни типа отбора здесь нет — если бы очередь
-- была публично читаема (а анонимный ключ всё ещё используется для её
-- показа), она не должна утекать сами неподтверждённые значения,
-- только факт "тут есть что проверить".
create view verification_queue as
select
  f.id as fact_id,
  'formula'::text as fact_type,
  p.id as programme_id,
  coalesce(p.name_lv, p.name_en) as programme_name,
  u.slug as university_slug,
  coalesce(u.name_lv, u.name_en) as university_name,
  f.created_at as collected_at,
  f.source_url
from formula f
join programme p on p.id = f.programme_id
join university u on u.id = p.university_id
where f.verified_at is null

union all

select
  ar.id,
  'application_round',
  null,
  null,
  u.slug,
  coalesce(u.name_lv, u.name_en),
  ar.created_at,
  ar.source_url
from application_round ar
join university u on u.id = ar.university_id
where ar.verified_at is null

union all

select
  uat.university_id,
  'admission_type',
  null,
  null,
  u.slug,
  coalesce(u.name_lv, u.name_en),
  uat.created_at,
  uat.source_url
from university_admission_type uat
join university u on u.id = uat.university_id
where uat.verified_at is null;

grant select on verification_queue to anon, authenticated;
