# Связи «программа ↔ код приёма statistika.vupp.lv» — проверка перед подтверждением

2026-10-18. Шаг 3 блока «Прошлогодний конкурс» (разведка и шаги 1–2 —
`VUPP-RECON-2026-10-18.md`). Черновики записаны в `programme_vupp_link`
скриптом `pipeline/src/vupp_link_drafts.py`; посетителям не видны, пока
связь не подтверждена (`verified_at`).

Ошибка связи — чужие цифры конкурса на карточке. Поэтому, как с
направлениями программ, подтверждение — решение владельца по правилу,
после просмотра этого списка.

## Что в базе

- `vupp_admission_stat`: 1882 строки портала — 2024 (630), 2025 (632),
  2026 (618); все восемь вузов единой подачи. Срез каждого года — после
  второго тура, дата обновления у строки.
- `programme_vupp_link`: **127 черновиков** — ЛУ 35, РТУ 92.

## Правила

| Вуз | Откуда код | Проверка |
|---|---|---|
| ЛУ | ссылка на каталог курсов на странице программы lu.lv (`…[program]=207B7`) | код есть в статистике портала; язык программы не спорит с пометкой «(angļu val.)» в названии портала |
| РТУ | код в адресе программы (`…/atvert/MBS?…`); у портала он в середине кода приёма (`RMBS0`, `LMCE0`, `NGCS0`) | середина кода и **город** строки портала совпадают с программой; язык — так же, как у ЛУ |

Код, найденный у двух программ каталога сразу, не связывается ни с одной.

## ЛУ — все 35 связей

Названия в каталоге ЛУ английские, на портале латышские, поэтому список
целиком:

| Программа каталога | Код | Название на портале |
|---|---|---|
| Business Process Management (lv) | 21902 | Biznesa procesu vadība |
| Business Process Management (en) | 21903 | Biznesa procesu vadība (angļu valodā) |
| Business Administration (lv) | 207B7 | Biznesa vadība |
| Business Administration (en) | 207B9 | Biznesa vadība (angļu val.) |
| E-business Management | 207BF | E-biznesa vadība |
| Industrial Engineering and Management (lv) | 207BG | Industriālā inženierija un vadība |
| Industrial Engineering and Management (en) | 207BH | Industriālā inženierija un vadība (angļu val.) |
| International Economics and Commercial Diplomacy (lv) | 207BK | Starptautiskā ekonomika un komercdiplomātija |
| International Economics and Commercial Diplomacy (en) | 207BL | … (angļu val.) |
| Accounting, Analysis and Audit | 207BA | Grāmatvedība, analīze un audits |
| Economics | 20771 | Ekonomika |
| Financial Management | 20796 | Finanšu menedžments |
| Finance (lv) | 21920 | Finanses |
| International Finance (en) | 21921 | Starptautiskās finanses (angļu valodā) |
| Finance Management Information Systems (en) | 21922 | Finanšu pārvaldības informācijas sistēmas (angļu valodā) |
| Accountancy and Finance (колледж) | 21913 | Grāmatvedība un finanses |
| Law | 20208 | Tiesību zinātne |
| Physics | 21023 | Fizika |
| Chemistry | 21212 | Ķīmija |
| Mathematics | 21069 | Matemātika |
| Mathematician Statistician | 21052 | Matemātiķis statistiķis |
| Biotechnology and Bioengineering (en) | 20913 | Biotehnoloģija un bioinženierija (angļu val.) |
| Biology and biomedicine | 20915, 20916 | две подпрограммы: Bioloģija, Biomedicīna |
| Pharmacy | 28405 | Farmācija |
| Nursing | 28413 | Māszinības |
| Medicine (lv) | 28401 | Ārstniecība |
| Dentistry (lv) | 28422 | Zobārstniecība |
| Dentistry (en) | 28415 | Zobārstniecība (angļu val.) |
| Latvian Studies | 22562 | Latvistika |
| Philology (en) | 22553, 22555, 22557 | три подпрограммы: французская, русская, немецкая (на английском) |
| Cultural and Social Anthropology (lv) | 29639 | Kultūras un sociālā antropoloģija |
| Social work (Rīga and UL branches) | 29607 | Sociālais darbs (только Рига; коды филиалов на странице не названы) |

## РТУ — 92 связи

Латышские названия каталога и портала совпадают у всех, кроме двух
программ «Būvniecība» (колледж в Лиепае и Резекне): на портале к названию
добавлена специализация («…būvdarbu vadītājs», «…transportbūvju būvdarbu
vadītājs») — это та же программа. Одна программа может получить несколько
кодов: очная и заочная форма набираются под разными буквами (`LGCS0` и
`NGCS0` — «Skolotājs», Лиепая).

## Не связано — остаётся без цифр, пока не решено иначе

**Язык спорит с порталом (5):**

| Программа | Код со страницы | Почему не связано |
|---|---|---|
| ЛУ Philology (en) | 22540 | на портале — латышско-русская подпрограмма; три английские связаны |
| ЛУ Cultural and Social Anthropology (en) | 29639 | это код латышской программы; английская на портале — 29646, на странице его нет |
| ЛУ English, European Languages and Business Studies (en) | 22537 | на портале «Anglistikas, Eiropas valodu un biznesa studijas» без пометки об английском — скорее всего та же программа, но правило осторожное |
| РТУ dcp-33000 (en в каталоге) | RDCP0 | на портале без пометки об английском |
| РТУ hcf-33000 (en в каталоге) | RHCF0 | так же |

**Без кода (57):** у 29 программ ЛУ на странице нет ссылки на каталог
курсов (психология, информатика, педагоги, филиалы и др.) — их коды на
портале есть (91 код ЛУ без пары), но связать их можно только по
названию; у ЛУ в каталоге английские названия, поэтому это отдельная
работа. У РТУ без пары — английский реестр (кода в адресе нет) и
программы, которых не было в единой подаче 2024–2026 годов. Коды РТУ с
буквой «D» — филиал в Даугавпилсе, был только в 2024 году, в каталоге его
нет.

## Что решить владельцу

1. Подтвердить 127 черновиков по правилу (выше) — или указать связи,
   которые исключить.
2. Пять спорных по языку — оставить без цифр или связать вручную
   (вероятно, верны 22537 и, после проверки, РТУ dcp/hcf).
3. 29 программ ЛУ без кода на странице — сопоставлять по названию сейчас
   или после показа на карточке.

## Решение (2026-10-18)

Владелец: «Подтвердить все 127» — подтверждено скриптом
`pipeline/src/confirm_vupp_links_by_rule.py` (он сверяет, что черновиков
ровно столько, сколько было в просмотренном списке). Спорные по языку (5)
остаются без связи. 29 программ ЛУ без кода на странице — сопоставление по
названию после блока на карточке.

## Вторая партия — по латышскому названию (2026-10-18)

Скрипт `pipeline/src/vupp_link_by_name.py`. Связь предлагается, только если
сходится всё: латышское название программы в каталоге = название на портале
без пометки языка; пометка языка («(angļu valodā)», «(ENG)», «(LV)») не
спорит с языком программы; вид подходит уровню (бакалавру — «Bakalaura…» и
«Pirmā cikla profesionālā», колледжу — «Īsā cikla profesionālā»); город
совпадает. Записано **42 черновика**: Ventspils 9, ViA 7, LBTU 20, DU 6.
Названия совпадают дословно у всех, кроме двух переименований — код тот же:

| Программа каталога | Код | На портале |
|---|---|---|
| ViA «Mehatronika» | 10136 | 2024–2025 «Mehatronika», **2026 «Robotika un automatizācija»** — на карточке будут цифры 2026 года под новым названием |
| LBTU «Ēdināšanas un viesnīcu vadība» (lv) | G0608 | 2024 «Ēdināšanas un viesnīcu uzņēmējdarbība», с 2025 — нынешнее |

Ventspils (у него 7 подтверждённых формул): Biznesa vadība V0114,
Datorzinātnes V0601 и английская V0608, Elektronikas inženierija V0607,
Jaunuzņēmumu vadība (en) V0118, Programmēšanas speciālists V0606,
Vadībzinātne — латышская V0121 и английская V0111, Valodas, saziņa un
kultūrvide V0227 (только 2026).

DU — Fizioterapija D0154, Sākumizglītības skolotājs D139S, Māszinības D01BZ,
Informācijas tehnoloģijas (колледж) D01BR, Pirmsskolas skolotājs D139P,
Mākslas menedžments D04A3. ViA и LBTU — латышские названия совпадают
дословно, список в выводе скрипта.

Без пары остались (51): английские названия в каталоге (EKA целиком, RNU
целиком, 11 программ DU, 3 английские программы LBTU), английские потоки
LBTU (на портале у LBTU нет пометки языка) и программы DU с подпрограммами
на портале («Skolotājs» — 24 кода «Skolotājs (…)», «Mūzika» — 7). Их можно
связать только ручной таблицей соответствий. У RNU коды меняются каждый год
(«1B2026», «1RZA2026»), у EKA код включает форму обучения — связь по коду у
них придётся обновлять ежегодно.

**Решение по второй партии (2026-10-18):** владелец — «Подтвердить все 42»;
подтверждено `confirm_vupp_links_by_rule.py --batch name`. Наружу видно 169
связей. Остальные программы — ручная таблица соответствий (решение того же
дня), третьей партией.

## Третья партия — ручная таблица соответствий (2026-10-18)

Скрипт `pipeline/src/vupp_link_manual.py`, таблица `MANUAL`: программа
каталога → латышские названия на портале (не коды: у RNU код меняется
каждый год, у EKA он включает форму обучения). Составил я по названиям;
решает владелец. Записано **178 черновиков у 60 программ** (ЛУ 31, DU 14,
EKA 10, RNU 5); опечаток в таблице и конфликтов кодов нет.

На карточке филиалы ЛУ («Pirmsskolas skolotājs (Cēsis)») идут одной таблицей
с Ригой — город стоит в строке. Если подпрограмм больше трёх («Skolotājs» у
DU — 24, «Mūzika» — 7, учитель ЛУ — 10), каждая свёрнута под своим
названием.

**ЛУ (31):**

| Каталог | Портал |
|---|---|
| Art | Māksla |
| Communication Science | Komunikācijas zinātne |
| Computer Science (lv / en) | Datorzinātnes / Datorzinātnes (angļu valodā) — двойной диплом с Линкольном (22317) не связан |
| Cultural and Social Anthropology (en) | Kultūras un sociālā antropoloģija (angļu val.) |
| English, European Languages and Business Studies (en) | Anglistikas, Eiropas valodu un biznesa studijas — **проверить**: на портале без пометки языка |
| Environmental Science | Vides zinātne |
| Geography / Geoinformatics / Geology | Ģeogrāfija / Ģeoinformātika / Ģeoloģija |
| History and Archeology | Vēsture un arheoloģija |
| Information Management | Informācijas pārvaldība |
| Labour Protection (колледж) | Darba aizsardzība |
| Occupational Health and Safety at Work | Arodveselība un drošība darbā |
| Optometry (lv / en) | Optometrija / Optometrija (angļu val.) |
| Philology (lv) | пять латышских подпрограмм: французская, классическая, русская, финно-угорская, немецкая |
| Philosophy / Political Science / Psychology / Sociology | Filozofija / Politikas zinātne / Psiholoģija / Socioloģija |
| Preschool teacher (колледж) | Pirmsskolas skolotājs + 6 филиалов |
| Primary Education Teacher | Sākumizglītības skolotājs + 6 филиалов |
| Professional Bachelor ‘Teacher’ | 10 программ «… skolotājs» (английского, математики, информатики и т. д.) |
| Programming and Computer Network Administration (колледж) | Programmēšana un datortīklu administrēšana |
| Research and protection of Cultural and Environmental Heritage | Kultūrvides mantojuma izpēte un aizsardzība |
| Social work (Rīga and UL branches) | + 4 филиала (Рига уже связана) |
| Sports Coach (колледж) | Sporta treneris + 4 филиала |
| Sports, Technology and Public Health | Sports, tehnoloģijas un sabiedrības veselība |
| Theology and Religious Studies | Teoloģija un reliģijpētniecība |
| Pre-Trial Investigation | Pirmstiesas izmeklēšana — **проверить**: на lu.lv код 20221, на портале 20220 |

**DU (14):** Psychology → Psiholoģija; History → Vēsture; Science of Law →
Tiesību zinātne; Strategic risks and crisis management → Stratēģiskie riski
un krīžu vadība; Biology → Bioloģija; Chemistry → Ķīmija (atjaunojamo
resursu ķīmija vai praktiskā bioanalītika); Environmental Science (lv) →
Vides zinātne; Language and culture studies (lv) → три «Valodu un kultūras
studijas (…)»; Grafikas dizains → Dizains (grafikas dizains); Biznesa un
finanšu procesi (lv) → … (finansists vai ekonomists); Informācijas
tehnoloģijas (бакалавр) → … (programmēšanas inženieris); Civilā drošība
un aizsardzība (колледж) → три специализации; Mūzika (lv) → 7 «Mūzika (…)»;
Skolotājs → 24 «Skolotājs (…)».

**EKA (10, латышские потоки):** Management → Vadības zinības; Culture
Management → Kultūras vadība; Business Economics → Biznesa ekonomika;
Information Technologies (Programming) → Informācijas tehnoloģijas
(Programmēšanas inženieris); International Trade and Logistics (колледж) →
Starptautiskie tirdzniecības darījumi un loģistika; Law → Tiesību zinātne;
Interior Design → Interjera dizains; Accounting and Finance Management →
Grāmatvedība un finanšu vadība; Marketing → Mārketings; Computer Game
Design → Datorspēļu dizains.

**RNU (5, латышские потоки):** Business Administration → Uzņēmējdarbības
vadība; Business Administration in Tourism → Uzņēmējdarbības vadība
tūrismā (2024 — Tūrisma uzņēmējdarbības vadība); Information Systems →
Informācijas sistēmas; Psychology → Psiholoģija; Tourism Service
Organisation (колледж) → Tūrisma pakalpojumu organizēšana.

**Не связано намеренно:** английские потоки, если портал не помечает язык
(EKA 4, RNU 4, DU 4, LBTU 6); ЛУ «Asian and Intercultural Studies» (на
портале «Āzijas studijas, modulis …» и «Austrumu-Rietumu starpkultūru
studijas» — неясно, что из этого); DU «Eastern European Culture and Business
Relations» (на портале «Austrumeiropas kultūras sakari un integrācijas
procesi» — похоже, но не наверняка); ЛУ Medicine (en) и Radiography — на
портале их нет.

**Решение по третьей партии (2026-10-18):** владелец — «Все 60 программ»
(включая два помеченных); подтверждено `confirm_vupp_links_by_rule.py
--batch manual`. Наружу видно 347 связей у 206 программ всех восьми вузов
единой подачи; цифры рядом с баллом — у 52 из 72 программ с подтверждённой
формулой (все ЛУ и Ventspils; RSU на портале нет, у двух формул РТУ нет
кода приёма).

**Ежегодно (август, после второго тура):** `vupp_stats.py --years <год>
--apply`, затем три скрипта черновиков (по коду, по названию, по таблице) —
у RNU и EKA коды новые каждый год; новые черновики — новой партией в
`confirm_vupp_links_by_rule.py` после решения владельца.
