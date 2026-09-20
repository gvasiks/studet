# Копии документов-источников формул

Протокол источника формулы (план работ, неделя 3). Формулу нельзя подтвердить
(`verified_at`), пока у неё не заполнены адрес документа, номер и дата, а
копия документа не лежит здесь: проверку делает сама база (ограничение
`formula_verified_needs_protocol`). Личный опыт поступления источником не
является — коэффициенты меняются каждый год.

Хэш копии считает `pipeline/src/seed_formulas.py` из файла при каждом
запуске, вручную его не вписывают.

| Файл | Что это | Откуда | Получено | Формулы |
|---|---|---|---|---|
| `venta/uznemsanas-noteikumi-2026-27-pielikums-2-grozits-06-2026.pdf` | Uzņemšanas noteikumi Ventspils Augstskolā 2026./2027., Senāta lēmums Nr. 25-39 (27.11.2025) **с двумя поправками**: Nr. 26-3 (28.01.2026) и Nr. 26-28 (18.06.2026); 20 страниц, 397 КБ | [irp.cdn-website.com](https://irp.cdn-website.com/f6b5d556/files/uploaded/26-28_Pielikums-2_Uznemsanas_noteikumi_2026-2027_grozits_06-2026.pdf) | 2026-09-20 | 7 |
| `lu/1-4-588-2024-piel-kons-04.07.25-2025-26.pdf` | Uzņemšanas prasības un kritēriji pamatstudijās **2025./2026.**, LU rīkojums Nr. 1-4/588 (28.11.2024) с поправками до 04.07.2025; 54 страницы, 786 КБ | [lu.lv](https://www.lu.lv/fileadmin/user_upload/lu_portal/gribustudet/pamatstudijas/1-4-588-2024_1._piel_kons_04.07.25.pdf) | 2026-09-20 | 26 — закрыты (`valid_to`), заменены формулами 2026/27 |
| `lu/uzn-prasibas-pamat-2026-27.pdf` | Uzņemšanas prasības un kritēriji pamatstudijās **2026./2027.**, LU rīkojums Nr. 1-4/506 (27.11.2025) с поправками 1-4/22, 1-4/105, 1-4/167, 1-4/195, 1-4/250 до 03.07.2026; 68 страниц, 596 КБ | [lu.lv](https://www.lu.lv/fileadmin/user_upload/LU.LV/www.lu.lv/Gribu_studet/Uznemsanas_dokumenti/uzn_prasibas_pamat_26_27.pdf) | 2026-09-20 | 47 (`pipeline/src/formulas_lu.py`) |
| `lu/uznemsanas-prasibas-un-kriteriji-2026-27.html` | То же на **2026./2027.**, страница сайта (PDF нет): agrā uzņemšana с 02.03.2026, vasaras с 09.07.2026 | [lu.lv](https://www.lu.lv/gribustudet/normativie-dokumenti/uznemsanas-prasibas-un-kriteriji-pamatstudijas-2026/2027-akademiskaja-gada/) | 2026-09-20 | справочно (общая часть; таблица по программам — в PDF выше) |
| `rtu/uznemsanas-noteikumi-pamatstudijas-2026-27.html` | Uzņemšanas noteikumi īsā cikla un pirmā cikla studiju programmās 2026./2027., Senāta protokollēmums Nr. 697 (24.11.2025). **PDF у РТУ нет**, текст опубликован только страницей | [rtu.lv](https://www.rtu.lv/lv/studijas/uznemsana/uznemsanas-noteikumi/uznemsanas-noteikumi-pamatstudijas) | 2026-09-20 | 2 |

## Что из этого следует

- **LU: формулы разобраны из PDF 2026/27** программой
  `pipeline/src/formulas_lu.py` (47 из 65 блоков документа; остальные — в
  отчёте запуска с причинами). Формулы 2025/26 закрыты. Правила на 2027/28
  вузы обязаны опубликовать **до 30 ноября 2026**: в декабре скрипт
  запускается на новом документе (путь и номера — константы в файле).
  Подтверждать формулы имеет смысл после этого, а не сейчас.
- **Ventspils: копия новее, чем формулы.** Формулы посеяны с версии до двух
  поправок; совпадают ли коэффициенты с текущей версией, проверяет человек
  при подтверждении.
- **РТУ**: копия — сохранённая страница; при смене правил её надо
  сохранить заново с новой датой.

## Как добавить или обновить документ

1. Скачать файл в `docs/source-documents/<вуз>/`, имя — по образцу выше (год
   правил в имени).
2. В `pipeline/src/seed_formulas.py` заведите `source_protocol(...)` с номером,
   датой версии (у документа с поправками — дата последней), путём и датой
   получения.
3. `python src/seed_formulas.py` — хэш посчитается, протокол запишется.
4. Очередь `/verification` покажет, чего ещё не хватает.
