# Язык обучения: сверка с NIID

**Статус:** ждёт решения владельца. Ничего из этого документа в базу не записано.

## Зачем

Пять сборщиков подставляют язык обучения, потому что сайт вуза его не
называет: RNU, DU, LKA, TSI и Ventspils Augstskola (у неё язык берётся из
названия программы). Владелец решил (2026-10-10) искать язык таких программ в
NIID — государственной базе, где поле «Valoda» заполнено у каждой программы.

## Как собрано

Два замера 2026-10-10, оба только на чтение:

- сырое значение поля языка у каждой программы на сайте вуза;
- список программ каждого из пяти учреждений в NIID с полем «Valoda»
  (DU — 49 записей, RNU — 11, LKA — 19, TSI — 17, Ventspils — 13).

Сопоставление «наша программа — запись NIID»:

- **Ventspils** — по ссылке на страницу NIID, которая уже лежит в базе
  (`details_source_url`); ручного труда нет.
- **RNU, DU, LKA, TSI** — вручную по смыслу названия и уровню: на сайтах этих
  вузов названия английские, в NIID латышские. Это суждение, а не факт из
  источника; номер записи NIID стоит в таблице, чтобы пару можно было
  проверить. У DU пары совпадают с давно принятым списком `COVERED` в
  `pipeline/src/sources/niid_universities.py`.

В таблицах ниже — только программы, по которым есть что решать: сайт язык не
называет, либо NIID говорит иное, чем сайт. Программы, где сайт называет язык
и NIID с ним согласен, опущены.

## Итог

| Что показала сверка | Программ |
|---|---|
| NIID подтверждает язык, который у нас стоит | 15 |
| NIID называет два языка, у нас один | 15 |
| NIID и сайт вуза расходятся | 2 |

## Что нужно решить

1. **Программы, где NIID подтверждает подставленный язык.** Предлагаю считать
   источником языка NIID и записать это в коде сборщика рядом с номером записи.
   Данные не меняются.
2. **Программы, где NIID называет два языка, а у нас один.** Здесь та же
   ловушка, что была у РТУ: «latviešu/angļu» в реестре означает, что программу
   разрешено вести на двух языках, но не обязательно, что набор идёт на обоих.
   У РТУ из 83 таких записей в реестре для поступающих оказалось 55. Варианты:
   - **а)** две записи на программу (как у Turība и LKA) — рискуем показать
     поток, на который не набирают;
   - **б)** оставить одну запись и не трогать язык — остаётся подстановка;
   - **в)** спросить вуз. Для RNU и TSI это по одному письму.
3. **Два расхождения сайта и NIID** — «Environmental Science» у DU (сайт
   называет оба языка, NIID только латышский) и «Digitālā kultūra un
   tekstveide» у Ventspils (у нас латышский, NIID называет только английский;
   на сайте вуза рядом с названием стоит звёздочка). По каждому нужен взгляд
   человека на страницу вуза; какой источник прав, отсюда не видно.

## Таблицы

### RNU

| Программа (как на сайте вуза) | Уровень | Язык на сайте вуза | У нас сейчас | Запись NIID | Язык в NIID | Итог |
|---|---|---|---|---|---|---|
| INFORMATION SYSTEMS | bachelor | не указан | lv | Informācijas sistēmas (117) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| TOURISM SERVICE ORGANISATION | college | не указан | lv | Tūrisma pakalpojumu organizēšana (11948) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| COMPUTER SYSTEMS | master | не указан | lv | Datorsistēmas (115) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| BUSINESS ADMINISTRATION | bachelor | не указан | lv | Uzņēmējdarbības vadība (28450) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| BUSINESS ADMINISTRATION | master | не указан | lv | Uzņēmējdarbības vadība (116) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| BUSINESS ADMINISTRATION IN TOURISM | bachelor | не указан | lv | Uzņēmējdarbības vadība tūrismā (114) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |

### DU

| Программа (как на сайте вуза) | Уровень | Язык на сайте вуза | У нас сейчас | Запись NIID | Язык в NIID | Итог |
|---|---|---|---|---|---|---|
| Biology | bachelor | не указан | lv | Bioloģija (59) | latviešu (LV) | совпадает |
| Chemistry | bachelor | не указан | lv | Ķīmija (12652) | latviešu (LV) | совпадает |
| Eastern European Culture and Business Relations | bachelor | не указан | lv | Austrumeiropas kultūras sakari un integrācijas procesi (4900) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| Environmental Science | bachelor | «Latvian (for studies in Latvian); English (for studies in English)» | en, lv | Vides zinātne (52) | latviešu (LV) | **расходится** |
| History | bachelor | не указан | lv | Vēsture (27857) | latviešu (LV) | совпадает |
| Language and culture studies | bachelor | не указан | lv | Valodu un kultūras studijas (60) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| Psychology | bachelor | не указан | lv | Psiholoģija (57) | latviešu (LV) | совпадает |
| Science of Law | bachelor | не указан | lv | Tiesību zinātne (25603) | latviešu (LV) | совпадает |
| Strategic risks and crisis management | bachelor | не указан | lv | Stratēģiskie riski un krīžu pārvaldība (28329) | latviešu (LV) | совпадает |

### LKA

| Программа (как на сайте вуза) | Уровень | Язык на сайте вуза | У нас сейчас | Запись NIID | Язык в NIID | Итог |
|---|---|---|---|---|---|---|
| Creative Industries | bachelor | не указан | lv | Radošās industrijas (uzņemšana 2026./27. gadā) (24464) | latviešu (LV) | совпадает |
| Audiovisual and Performing Art | master | не указан | lv | Audiovizuālā un skatuves māksla (Uzņemšana 2026./27. gadā) (24944) | latviešu (LV) | совпадает |
| Creative Industries and Growth Management | master | «Latvian» | lv | Radošās industrijas un izaugsmes menedžments (uzņemšana 2026./27. gadā) (25733) | latviešu un angļu (LV-EN) | **NIID называет ещё язык** |
| Cultural and Arts Management | master | не указан | lv | Kultūras un mākslas pārvaldība (uzņemšana 2026./27. gadā) (172) | latviešu (LV) | совпадает |

### TSI

| Программа (как на сайте вуза) | Уровень | Язык на сайте вуза | У нас сейчас | Запись NIID | Язык в NIID | Итог |
|---|---|---|---|---|---|---|
| Intelligent Transport and Smart Logistics | master | не указан | en | Intelektisks transports un viedā loģistika (17576) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| Telematics and Logistics | doctoral | не указан | en | Telemātika un loģistika (575) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| Digital Economy and Business | doctoral | не указан | en | Digitālā ekonomika un uzņēmējdarbība (26819) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |

### Ventspils

| Программа (как на сайте вуза) | Уровень | Язык на сайте вуза | У нас сейчас | Запись NIID | Язык в NIID | Итог |
|---|---|---|---|---|---|---|
| Programmēšanas speciālists | college | не указан | lv | Programmēšanas speciālists (24592) | latviešu (LV) | совпадает |
| Datorzinātnes | bachelor | не указан | lv | Datorzinātnes (919) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| Elektronikas inženierija | bachelor | не указан | lv | Elektronikas inženierija (24950) | latviešu (LV) | совпадает |
| Biznesa vadība | bachelor | не указан | lv | Biznesa vadība (19738) | latviešu (LV) | совпадает |
| Valodas, saziņa un kultūrvide | bachelor | не указан | lv | Valodas, saziņa un kultūrvide (28568) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| Datorzinātnes | master | не указан | lv | Datorzinātnes (922) | latviešu/angļu (LV/EN) | **NIID называет ещё язык** |
| Uzņēmējdarbības vadība | master | не указан | lv | Uzņēmējdarbības vadība (584) | latviešu (LV) | совпадает |
| Tulkošana un terminoloģija | master | не указан | lv | Tulkošana un terminoloģija (28502) | latviešu (LV) | совпадает |
| Elektronika | master | не указан | lv | Elektronika (27060) | latviešu (LV) | совпадает |
| Digitālā kultūra un tekstveide | master | не указан | lv | Digitālā kultūra un tekstveide (28569) | angļu (EN) | **расходится** |

## Что замечено попутно

- У **RNU** все восемь программ собираются с английского раздела сайта, а в
  базе стоят латышскими: у шести язык на странице не указан и подставлялся
  «латышский». NIID у этих шести называет оба языка.
- У **TSI** три программы без языка на странице подставлялись английскими;
  NIID называет оба языка.
- Записи NIID у LKA содержат в названии год набора («Uzņemšana 2026./27.
  gadā»), а у четырёх программ — «Uzņemšanas gads tiks precizēts»: набор на
  них в этом году может не идти. В каталоге это сейчас не отражено.
