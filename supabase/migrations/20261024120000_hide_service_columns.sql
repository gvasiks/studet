-- Служебные колонки закрыты от публичного ключа (решение владельца
-- 2026-10-24; находка аудита 2026-10-04 и агента безопасности 2026-10-17).
--
-- Что закрыто:
--   verified_by       — кто и по какому решению подтвердил факт;
--   disputed_reason   — внутренняя причина пометки «спорно»;
--   source_copy_path, source_copy_sha256, source_copy_fetched_on — где в
--                       репозитории лежит копия документа и её хеш.
-- Что остаётся видно: всё остальное, в том числе verified_at (дата «проверено
-- вручную» на карточке), source_url, source_doc_number и source_doc_date
-- (номер и дата документа — это часть ссылки на источник), disputed_at.
--
-- Как: у таблицы снимается общее право чтения и выдаётся право читать
-- перечисленные колонки (все, кроме закрытых). Сайт эти колонки не читает
-- (проверено 2026-10-24: ни одного select("*") по этим таблицам); конвейер
-- ходит сервисным ключом — его это не касается.
--
-- ВАЖНО на будущее: новая колонка в этих таблицах публичному ключу НЕ видна,
-- пока ей явно не выдать право: grant select (колонка) on таблица to anon,
-- authenticated; — иначе запрос сайта с этой колонкой получит ошибку прав.
--
-- Ограничение решения: репозиторий публичный, и снимок подтверждённых фактов
-- docs/backups/verified-facts.json (вместе с verified_by) лежит в нём и в его
-- истории. Миграция закрывает API, не снимок.
--
-- verification_queue — очередь внутренней страницы /verification, которая
-- закрыта тем же решением; в очереди есть disputed_reason.

do $$
declare
  target record;
  visible text;
begin
  for target in
    select *
    from (
      values
        ('formula', array['verified_by', 'disputed_reason', 'source_copy_path', 'source_copy_sha256', 'source_copy_fetched_on']),
        ('programme_requirement_set', array['verified_by', 'disputed_reason', 'source_copy_path', 'source_copy_sha256', 'source_copy_fetched_on']),
        ('university_admission_type', array['verified_by', 'disputed_reason']),
        ('programme_field', array['verified_by', 'disputed_reason']),
        ('application_round', array['verified_by', 'disputed_reason']),
        ('application_channel', array['verified_by', 'disputed_reason']),
        ('programme', array['verified_by']),
        ('university', array['verified_by']),
        ('programme_vupp_link', array['verified_by'])
    ) as v (table_name, hidden)
  loop
    select string_agg(quote_ident(column_name), ', ' order by ordinal_position)
    into visible
    from information_schema.columns
    where table_schema = 'public'
      and table_name = target.table_name
      and column_name <> all (target.hidden);

    if visible is null then
      raise exception 'таблица % не найдена', target.table_name;
    end if;

    execute format('revoke select on public.%I from anon, authenticated', target.table_name);
    execute format('grant select (%s) on public.%I to anon, authenticated', visible, target.table_name);
  end loop;
end
$$;

revoke select on public.verification_queue from anon, authenticated;
