-- Ревью 2026-09: калькулятор показывал числа, которые не подтвердил ни
-- один человек — verified_at пуст у всех 35 формул, а RLS-политика
-- отдавала их анониму без разбора (formula_public_read using (true)).
-- Гейт уже добавлен в src/lib/formula-queries.ts, но application-level
-- фильтр не защищает от прямого запроса к Supabase REST API — anon key
-- публичный, и им можно обратиться к базе мимо Next.js совсем.
--
-- Дальше защита в двух местах: приложение фильтрует для честности
-- сообщения пользователю, RLS — потому что публичный API должен быть
-- безопасен сам по себе, не полагаясь на то, что единственный клиент
-- ведёт себя правильно (A01 OWASP, правило CLAUDE.md "RLS-политики
-- на каждой новой таблице, без исключений").

drop policy formula_public_read on formula;
drop policy formula_term_public_read on formula_term;
drop policy formula_gate_public_read on formula_gate;

create policy formula_public_read on formula
  for select using (verified_at is not null);

create policy formula_term_public_read on formula_term
  for select using (
    exists (
      select 1 from formula f
      where f.id = formula_term.formula_id and f.verified_at is not null
    )
  );

create policy formula_gate_public_read on formula_gate
  for select using (
    exists (
      select 1 from formula f
      where f.id = formula_gate.formula_id and f.verified_at is not null
    )
  );

-- level_coefficient — не трогаем: это не факт про конкретный вуз,
-- который может быть ошибочно извлечён конвейером, а нормативные
-- коэффициенты уровня ЦЭ, одинаковые у всех и известные заранее.
