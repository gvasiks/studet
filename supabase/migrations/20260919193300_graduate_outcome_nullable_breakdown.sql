-- Издатель (ИЗМ/ЦСУ) скрывает разбивку занятости, когда занятых
-- меньше пяти (metodologija_atvertie_dati_2020.docx на странице
-- датасета) — в CSV эти три колонки тогда пустые (1268 из 3888 строк
-- на уровне групп программ). Пустое значение — "скрыто", а не ноль.
alter table graduate_outcome alter column unemployed_or_inactive drop not null;
alter table graduate_outcome alter column emigrated drop not null;
alter table graduate_outcome alter column no_info drop not null;
