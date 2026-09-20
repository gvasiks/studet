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
| `lu/1-4-588-2024-piel-kons-04.07.25-2025-26.pdf` | Uzņemšanas prasības un kritēriji pamatstudijās **2025./2026.**, LU rīkojums Nr. 1-4/588 (28.11.2024) с поправками до 04.07.2025; 54 страницы, 786 КБ | [lu.lv](https://www.lu.lv/fileadmin/user_upload/lu_portal/gribustudet/pamatstudijas/1-4-588-2024_1._piel_kons_04.07.25.pdf) | 2026-09-20 | 26 — **устарели** |
| `lu/uznemsanas-prasibas-un-kriteriji-2026-27.html` | То же на **2026./2027.**, страница сайта (PDF нет): agrā uzņemšana с 02.03.2026, vasaras с 09.07.2026 | [lu.lv](https://www.lu.lv/gribustudet/normativie-dokumenti/uznemsanas-prasibas-un-kriteriji-pamatstudijas-2026/2027-akademiskaja-gada/) | 2026-09-20 | справочно, формулы с неё не посеяны |
| `rtu/uznemsanas-noteikumi-pamatstudijas-2026-27.html` | Uzņemšanas noteikumi īsā cikla un pirmā cikla studiju programmās 2026./2027., Senāta protokollēmums Nr. 697 (24.11.2025). **PDF у РТУ нет**, текст опубликован только страницей | [rtu.lv](https://www.rtu.lv/lv/studijas/uznemsana/uznemsanas-noteikumi/uznemsanas-noteikumi-pamatstudijas) | 2026-09-20 | 2 |

## Что из этого следует

- **LU: 26 формул взяты из правил прошлого учебного года** и подтверждать их
  нет смысла. На сайте уже лежат правила 2026/27, где приём разделён на
  раннюю (до ЦЭ) и летнюю, а правила на 2027/28 вузы обязаны опубликовать
  **до 30 ноября 2026**. Формулы ЛУ пересеваются с документа 2027/28 в
  декабрьском цикле сверки, а не правятся сейчас.
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
