# Правила приёма 2027/28 — первый просмотр (2026-11-21)

План 2026-09-21, Д2: после 30 ноября вузы публикуют правила следующего года, формулы
переразбираются. `pipeline/src/rules_watch.py` запущен досрочно, 21 ноября: из 17 страниц
у трёх вузов правила 2027./2028. уже вышли. В базе **ничего не менялось** — это список того,
что придётся сделать в декабре, и находки, которые стоит знать заранее.

Копии документов (правило 5 — источник формулы — утверждённый документ):

| Вуз | Документ | Копия |
|---|---|---|
| RSU | Uzņemšanas noteikumi … 2027./2028. akadēmiskajam gadam, 1-PB-9/85/2026 от 13.11.2026 | `docs/source-documents/rsu/uznemsanas-noteikumi-pamatstudijas-2027-28.pdf` |
| LBTU | Uzņemšanas noteikumi pamatstudijās 2027./2028. studiju gadam, Senāts 11.11.2026, Nr. 12-112 | `docs/source-documents/lbtu/uznemsanas-noteikumi-pamatstudijas-2027-28-stg-11112026.pdf` |
| Juridiskā koledža | 2027./2028. studiju gada uzņemšanas noteikumi, JK Dome 29.10.2026, prot. Nr. 3-01/142 | `docs/source-documents/juridiska-koledza/uznemsanas-noteikumi-2027-28.html` |

`robots.txt` всех трёх сайтов чтение не запрещает (проверено 2026-11-21, в том числе для ИИ-агентов).
Пока только 2026./2027.: lu, rtu, du, venta, psmk, rnu, bsa, via, riseba, bvk, rbk, r1mk, vpk, jvlma.

## RSU

Приложения перенумерованы (было 1–28B, стало 1–26), поэтому сравнивал по названию программы,
разбирая оба документа тем же `formulas_rsu.py` (в новом документе строка критериев переносится
как «kri-tēriji» — парсеру нужна правка, см. ниже).

**Без изменений** — 13 подтверждённых формул: dental-hygiene, dentistry, dentistry-lv,
international-business-and-start-up-entrepreneurship, international-business-and-sustainable-economy,
international-marketing-and-advertising, international-relations-european-studies, journalism, law,
multimedia-communication, physiotherapy-0-lv, public-relations, social-work-0. Минимумы в приложениях
(«nevar būt zemāks par N punktiem») тоже те же.

**Изменилось — подтверждённые формулы 2026/27 к 2027/28 не переносятся:**

| Программа | 2026/27 | 2027/28 |
|---|---|---|
| Psiholoģija (`psychology-0`) | матем. 20% · латыш. 40% · ин. яз. 40% | матем. **30%** · латыш. **35%** · ин. яз. **35%** (прил. 12) |
| Sporta treneris (`sports-coach`, `sports-coach-liepaja-branch`) | OSPPP 50% + ЦЭ 15/20/15 | **испытание по физической подготовке 50%** + ЦЭ 15/20/15 (прил. 1, таблица баллов — прил. 26). Модель это испытание не выражает — формулы 2027/28 у программы не будет |
| Ārstnieciskā masāža, Ārsta palīgs (`medical-massage-liepaja-branch`, `physician-assistant-liepaja-branch`) | прил. 1 и 2 | **приложений нет**; слова «Liepāja» в новом документе нет вовсе. Приём в 2027/28, похоже, не объявлен — не вывод, а вопрос к RSU |

**Общая часть:** порог конкурса по умолчанию (п. 21.2) поднят с **30 до 35 баллов**; добавлен п. 21.4
(иностранцы без мотивационного интервью к конкурсу не допускаются); «Policijas darbs» и подпрограмма
28B по-прежнему без формулы. Порог п. 21.2 в модели не хранится, на расчёт не влияет.

## LBTU

Формула LBTU по-прежнему не разобрана (альтернативы «CE или GA», ×1,25 — `project_formula_extraction_status`).
Обязательные ЦЭ (латышский, иностранный, математика) те же. В таблице раздела 3 поменялись
необязательные предметы «papildus, ja ir» у нескольких программ (например, добавлено «CE kultūrā un
mākslā», «sociālajās zinātnēs» вместо «bioloģijā vai dabaszinībās»), Ainavu arhitektūra un plānošana
перенесена в факультет MVZF. Требования LBTU в декабре сверить с `requirements_lbtu.py` построчно.
Бюджетные места в тексте теперь «studiju vietas, kas pilnībā finansētas no augstskolas līdzekļiem»
(п. 2.2, 2.5) — новая формулировка закона, не новое правило.

## Juridiskā koledža

Требования те же: ЦЭ по математике, латышскому и иностранному (п. 8). Новое:

- **Зимний приём: документы с 5 января по 5 февраля 2027**; летний — с 1 июля 2027. Это срок
  подачи для Д1 (правило 6 — показывается только после подтверждения человеком).
- П. 7.1–7.2: расширен список английских сертификатов, для иностранцев добавлен Medium of
  Instruction — касается требований к английскому для иностранцев.

## Что сделать в декабре (Д2)

1. `formulas_rsu.py`: путь, адрес и реквизиты документа 2027/28; новая нумерация приложений в
   `RSU_SLUGS`; строка критериев с переносом «kri-tēriji». Записать черновики 2027/28 (`--apply`),
   старые закрываются `valid_to`; подтверждает владелец — по сравнению выше 13 формул совпадают
   числами, меняется одна (психология).
2. Решить, что показывать у `sports-coach*`, `medical-massage-liepaja-branch`,
   `physician-assistant-liepaja-branch`, когда начнётся приём 2027/28.
3. LBTU — сверка требований; JK — срок зимнего приёма на подтверждение.
4. 1 декабря и позже — `rules_watch.py` снова, по остальным 14 вузам.
