# Глоссарий терминов (план 2026-09-21, пункт 13)

Список ключевых терминов с закреплённым переводом. Латышский — источник
(CLAUDE.md: «Английский пишется с латышского»), английский — то, что уже
используется в `src/i18n/dictionaries/{lv,en}.json` на сегодня, сверено на
внутреннюю согласованность (см. «Как собран список» внизу). Носитель ещё
**не вычитывал** ни латышский, ни английский столбец — это первый черновик,
не подтверждённая версия; отмечено в каждом разделе отдельно.

Назначение: при добавлении нового текста в словари брать перевод термина
отсюда, а не придумывать заново — иначе на сайте появятся два разных
английских слова для одного и того же латышского понятия («competition
score» в одном месте и «competitive rank» в другом), и это подорвёт доверие
быстрее, чем опечатка.

## 1. Юридические и предметные термины

Источник — `glossary.items` в обоих словарях (страница `/glossary`, у
каждого термина указан правовой источник в самих словарях). Список ниже —
просто выжимка «термин → закреплённый перевод» для использования вне
страницы глоссария (в анкете, калькуляторе, карточке программы и т.д.).

| LV (в правилах приёма) | Закреплённый EN | Куда уже используется |
|---|---|---|
| akreditēta studiju programma | Accredited study programme | `/glossary` |
| licencēšana | Licensing | `/glossary` |
| reflektants | Applicant | `/glossary` |
| uzņemšanas noteikumi | Admission rules | `/glossary`, `programme.deadlinesTitle` (контекстно) |
| uzņemšanas komisija | Admission committee | `/glossary`, `docs/checks/ADMISSION-COMMITTEE-QUESTIONS.md` |
| konkurss | Competition | `/glossary` |
| centralizētais eksāmens (CE) | Centralised exam (CE) | `/glossary`, `survey.exams`, `calculator` |
| mācību satura apguves līmenis | Level of study content | `/glossary`, `calculator.levels` (как «Highest/Optimal/General level») |
| līmeņa koeficients | Level coefficient | `/glossary` |
| CE kopvērtējums procentos | Total CE result in per cent | `/glossary` |
| konkursa punkti, rangs | Competition score | `/glossary`, `calculator.totalLabel`, `match.scoreLabel` — **не** «rank», «score», «points» по отдельности |
| gada atzīme | Annual mark | `/glossary`, `calculator.termKinds.certificate` (там — «Certificate grade», см. раздел 4 про расхождение) |
| STIP (starptautiskais tests) | International language test (STIP) | `/glossary` |
| papildu prasības | Additional requirements | `/glossary` |
| iestājpārbaudījums | Entrance test / entrance exam | `/glossary` использует «Entrance test», `calculator.termKinds.entrance_exam` — «Entrance exam». **Расхождение, см. раздел 4** |
| ārpus konkursa | Admission outside the competition | `/glossary` |
| prioritātes | Priorities | `/glossary` |
| budžeta vieta | Budget place | `/glossary`, `catalog.funding.budget` — «Budget places» (множественное число в фильтре, единственное в глоссарии — это нормально, не расхождение) |
| maksas vieta | Paid place | `/glossary`, `catalog.funding.paid` — «Paid studies» (см. раздел 4) |
| studiju līgums | Study contract | `/glossary` |
| imatrikulācija | Matriculation | `/glossary` |
| kredītpunkts (KP) | Credit point | `/glossary` |
| pilna laika / nepilna laika | Full-time / part-time studies | `/glossary`, `catalog.studyMode` |
| īsā cikla / pirmā cikla programma | Short-cycle / first-cycle programme | `/glossary`, `catalog.degreeLevel` (там — «College studies» для īsā cikla, см. раздел 4) |

## 2. Уровни, форма и финансирование обучения (`catalog.*`, `programme.*`)

| LV | Закреплённый EN |
|---|---|
| Koledžas studijas | College studies |
| Bakalaura studijas | Bachelor's studies |
| Maģistra studijas | Master's studies |
| Doktora studijas | Doctoral studies |
| Sagatavošanas programma | Foundation programme |
| Pilna laika | Full-time |
| Nepilna laika | Part-time |
| Tālmācība | Distance learning |
| Budžeta vietas | Budget places |
| Maksas studijas | Paid studies |
| Budžeta un maksas vietas | Budget and paid places |

## 3. Предметы CE (`survey.exams.subjects`, те же ключи — `formula_term.subject`)

| LV | Закреплённый EN |
|---|---|
| Latviešu valoda | Latvian language |
| Angļu valoda | English language |
| Vācu valoda | German |
| Matemātika | Mathematics |
| Fizika | Physics |
| Ķīmija | Chemistry |
| Bioloģija | Biology |
| Vēsture | History |
| Latviešu literatūra | Latvian literature |
| Sociālās zinātnes | Social studies |

Уровень CE (`calculator.levels`): Augstākais līmenis → **Highest level**,
Optimālais līmenis → **Optimal level**, Vispārīgais līmenis → **General
level**.

## 4. Направления (`fields.areas`) — не путать с категориями анкеты

Это код направления ИЗМ/CSP (3 цифры, `programme_field.field_code`), не то
же самое, что упрощённые категории интересов в анкете (следующая таблица).
Смешивать два набора в тексте — сама по себе ошибка, не только вопрос
перевода: у них разные ключи и разная зернистость.

| Код | LV | Закреплённый EN |
|---|---|---|
| 14 | Izglītība | Education |
| 21 | Māksla | Arts |
| 22 | Humanitārās zinātnes | Humanities |
| 31 | Sociālās un uzvedības zinātnes | Social and behavioural sciences |
| 32 | Žurnālistika un informācija | Journalism and information |
| 34 | Bizness un pārvaldība | Business and administration |
| 38 | Tiesības | Law |
| 42 | Dzīvās dabas zinātnes | Life sciences |
| 44 | Fizikālās zinātnes | Physical sciences |
| 46 | Matemātika un statistika | Mathematics and statistics |
| 48 | Datorzinātnes | Computing |
| 52 | Inženierzinātnes | Engineering |
| 54 | Ražošana un pārstrāde | Manufacturing and processing |
| 58 | Arhitektūra un būvniecība | Architecture and construction |
| 62 | Lauksaimniecība un mežsaimniecība | Agriculture and forestry |
| 64 | Veterinārija | Veterinary |
| 72 | Veselības aprūpe | Health |
| 76 | Sociālie pakalpojumi | Social services |
| 81 | Personiskie pakalpojumi (tūrisms, sports) | Personal services (tourism, sport) |
| 84 | Transporta pakalpojumi | Transport services |
| 85 | Vides aizsardzība | Environmental protection |
| 86 | Drošības pakalpojumi | Security services |

## 5. Категории интересов анкеты (`survey.interests.categories`)

Отдельная, более крупная группировка — специально для фильтра в анкете, не
для отображения официального направления программы.

| Ключ | LV | Закреплённый EN |
|---|---|---|
| business | Bizness un ekonomika | Business and economics |
| it | IT un tehnoloģijas | IT and technology |
| law | Tiesības un drošība | Law and security |
| health | Veselība un sociālā joma | Health and social care |
| engineering | Inženierzinātnes un būvniecība | Engineering and construction |
| science | Dabaszinātnes un vide | Natural sciences and environment |
| humanities | Humanitārās zinātnes un komunikācija | Humanities and communication |
| arts | Māksla un dizains | Arts and design |
| society | Psiholoģija, sociālās zinātnes un izglītība | Psychology, social sciences and education |
| services | Tūrisms un sports | Tourism and sport |

## 6. Слагаемые формулы (`calculator.termKinds`)

| LV | Закреплённый EN |
|---|---|
| Vidējais % visos CE | Average % across all exams |
| Vidējais % visos CE (ar līmeņa koeficientu) | Average % across all exams (with level coefficient) |
| Atestāta vērtējums | Certificate grade |
| Iestājpārbaudījums | Entrance exam |
| Angļu valodas zināšanu pārbaude | English proficiency test |
| Strukturētā intervija | Structured interview |
| Matemātikas iestājpārbaudījums | Mathematics entrance exam |
| Praktiskais pārbaudījums vizuālajā mākslā | Visual arts practical exam |
| Profesionālās piemērotības pārbaudījums OSPPP (0–10) | Professional aptitude test OSPPP (0–10) |
| Atestāta gada atzīme fizikā (1–10) | School certificate annual mark in physics (1–10) |
| Atestāta gada atzīme ģeogrāfijā (1–10) | School certificate annual mark in geography (1–10) |

## 7. Сквозные продуктовые фразы

Термины без юридического источника, но встречающиеся на многих экранах —
разъехаться так же легко, как и с юридическими.

| LV | Закреплённый EN | Не писать так |
|---|---|---|
| katalogs | catalogue | ~~catalog~~ (американское написание — только как ключ JSON, не в тексте) |
| konkursa punktu kalkulators | Competition score calculator | ~~competitive score~~, ~~ranking calculator~~ |
| Kur tiešām varu iestāties? | Where can I actually get in? | — |
| aptauja | survey / questionnaire | оба варианта в ходу (`nav.survey` = «Survey», `home.description` = «Questionnaire») — **не расхождение**, разные контексты (пункт меню vs. описание продукта), но не смешивать внутри одного экрана |
| mans saraksts | My list (как подпись кнопки/страницы) | «favourites» само по себе — не ошибка (законно встречается в `privacy` как общее слово о механизме), ошибка — заменить им подпись кнопки/пункта меню |
| pārbaudīts (cilvēka) | Verified | ~~checked~~, ~~confirmed~~ |
| iegūts automātiski | Auto-extracted | ~~automatically collected~~ |

## Решено (владелец, 2026-09-24): два расхождения — это не расхождения

Проверка нашла два места, где один и тот же LV-термин на разных экранах
переведён по-разному, и я думал, что это могло быть недосмотром:

1. **iestājpārbaudījums**: на `/glossary` — «Entrance test», в
   `calculator.termKinds.entrance_exam` — «Entrance exam».
2. **gada atzīme**: на `/glossary` — «Annual mark», в
   `calculator.termKinds.certificate` — «Certificate grade».

Владелец подтвердил: «iestājpārbaudījums» и «gada atzīme» — две разные
величины (вступительное испытание/оценка за него — это не то же самое, что
годовая оценка аттестата), и решение по каждой — сохранить оба английских
варианта как есть, не сводить к одному. Оставляю оба: «Entrance
test»/«Entrance exam» — раздел 1 и раздел 6 этого файла соответственно,
«Annual mark»/«Certificate grade» — та же пара разделов. Автопроверка (см.
ниже) их не путает — в чёрный список не попали.

## Как собран список

Термины взяты из уже реализованных `lv.json`/`en.json` (не придуманы
заново) — я прошёл по каждому разделу словарей и сверил, что один и тот же
LV-термин везде даёт одно и то же EN-слово (`grep`/`sort`/`uniq` по
основным кандидатам на расхождение — «catalog(ue)», «competition score»,
«budget place», «study mode», «degree level», «centralised exam»,
«admission rule»: реальных текстовых расхождений не нашлось, только
JSON-ключи вроде `"catalog": {...}`, которые не видны пользователю). Два
найденных контекстных расхождения — выше.

## Проверка при добавлении текста — решено (владелец, 2026-09-24): автоматическая

`scripts/check-glossary-terms.mjs` — список запрещённых альтернативных
формулировок (раздел 7, колонка «Не писать так») и проверка по строковым
ЗНАЧЕНИЯМ словарей (не по ключам JSON — `"catalog": {...}` не в счёт), в CI
через `npm run check:glossary-terms`. Ловит только то, что явно занесено в
список ниже — не ловит новую формулировку того же понятия, которой в
списке ещё нет; это осознанный компромис (грубая, но безопасная защита от
разъезда, без ложных срабатываний на обычной прозе).

Текущий чёрный список (регулярка → что писать вместо):
- `catalog` без «ue» → *catalogue*
- `competitive score` → *competition score*
- `ranking calculator` → *competition score calculator*

Автопроверка ловит только то, что явно занесено в этот список — не заменяет
носителя языка. **Носитель ещё не вычитывал** ни латышский, ни английский
столбец (строка плана: «носитель вычитывает словари один раз») — это
отдельный шаг, автоматизации не подлежит.
