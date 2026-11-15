-- verified_by у коэффициентов уровня ЦЭ закрыт от публичного ключа
-- (предрелизная проверка 2026-11-15, docs/checks/PRERELEASE-2026-11-15.md;
-- решение владельца «Да, пиши»).
--
-- level_coefficient пропустили в 20261024120000_hide_service_columns.sql:
-- право чтения у неё было выдано на всю таблицу, и verified_by читался
-- публичным ключом. Сейчас колонка пуста у всех трёх строк — утечки нет,
-- миграция закрывает её до первого подтверждения.
--
-- Как и там: общее право чтения снимается, выдаётся право на колонки без
-- verified_by. Сайт читает только level, coefficient, valid_from
-- (src/lib/formula-queries.ts) — проверено 2026-11-15. Права на запись у
-- публичного ключа отозваны раньше (миграция 2026-10-10), политика RLS
-- level_coefficient_public_read не меняется.
--
-- ВАЖНО на будущее: новая колонка этой таблицы публичному ключу не видна,
-- пока ей явно не выдать право: grant select (колонка) on level_coefficient
-- to anon, authenticated;

revoke select on public.level_coefficient from anon, authenticated;

grant select (level, coefficient, valid_from, source_url, verified_at)
  on public.level_coefficient to anon, authenticated;

-- Проверка после применения (в SQL Editor): ожидается одна строка на каждую
-- роль и колонку из списка выше, без verified_by.
-- select grantee, column_name
-- from information_schema.column_privileges
-- where table_schema = 'public' and table_name = 'level_coefficient'
--   and grantee in ('anon', 'authenticated') and privilege_type = 'SELECT'
-- order by grantee, column_name;
