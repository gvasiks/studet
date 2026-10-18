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
