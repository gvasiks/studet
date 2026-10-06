# Литва: лист сверки с официальным калькулятором (2026)

Этот файл собирается скриптом `scripts/lt-check-sheet.mjs` — руками не править.
Ответы вписываются в `docs/checks/lt-calculator-cases-2026.json`, поле `official`.

Вписано ответов по строкам: **0 из 30**.

## Проведённая сверка

2026-10-06: проверено **13** случаев, все совпали.

Сообщение владельца: «Проверил выборочно 13 штук — все считает правильно». Номера случаев он не записывал, поэтому поле official у случаев не заполнено.

Порог сверки снижен с 30 до 13 случаев решением владельца 2026-10-06 («13 достаточно»).

## Зачем это нужно

Литовские формулы не подтверждает человек. Взамен наш расчёт обязан совпасть
с официальным калькулятором LAMA BPO не меньше чем на 30 наборах оценок —
иначе он не выпускается (`docs/PLAN-LITHUANIA-2027.md`, раздел 4).

Автоматически отправить эти случаи нельзя: сервис расчёта запрещает
автоматических клиентов в своём `robots.txt`. Поэтому их вводит человек —
на той же странице, которой пользуются абитуриенты.

## Как вводить

1. Откройте <https://lamabpo.lt/pirmosios-pakopos-ir-vientisosios-studijos/konkursinio-balo-skaiciuokle/>.
2. Год окончания школы — **2026**. Где учились — **Bendrojo ugdymo mokykloje**.
3. Выберите вуз и программу из строки таблицы. Если программ с таким
   названием несколько — ту, у которой совпадают город и форма.
4. Для каждого предмета из столбца «Что ввести» выберите вид оценки —
   государственный экзамен указанного уровня (**VA**, **VB** или **V**) — и
   впишите число. Остальные предметы оставьте пустыми.
5. Дополнительные достижения (олимпиады, служба и прочее) не отмечайте.
6. Нажмите расчёт и сравните итоговый балл с числом в столбце «Наш балл».

Оценки выдуманы; персональных данных на странице вводить не нужно.

## Что записать

Проще всего — написать в чат номера случаев, где число **не совпало**, и
что показал официальный калькулятор (например: «5 — 7,06; 16 — 7,22;
остальные совпали»). Если калькулятор не дал ввести оценку или показал
предупреждение — это тоже результат, запишите его словами.

Первые семь случаев и случаи 9, 14–17, 25, 27–28 проверяют допущения,
в которых я не уверен (общий курс, нижняя граница оценок, два иностранных
языка, пропущенный предмет, среднее двух предметов). Если времени мало —
начните с них.

## Случаи

| № | Вуз и программа | Что ввести | Что проверяет | Наш балл | Официальный | Итог |
|---|---|---|---|---|---|---|
| 1 | Kauno kolegija<br>**Apskaita**<br>Kaunas, Nuolatinė (NL) · Mišri | Matematika — VA **68**<br>Istorija — V **57**<br>Biologija — V **71**<br>Lietuvių kalba ir literatūra — VA **86** | полный набор, расширенный курс | **7,00** |  |  |
| 2 | Kauno kolegija<br>**Apskaita**<br>Kaunas, Nuolatinė (NL) · Mišri | Matematika — VB **68**<br>Istorija — V **57**<br>Biologija — V **71**<br>Lietuvių kalba ir literatūra — VA **86** | математика по общему курсу (B) | **6,18** |  |  |
| 3 | Kauno kolegija<br>**Apskaita**<br>Kaunas, Nuolatinė (NL) · Mišri | Matematika — VA **68**<br>Istorija — V **57**<br>Biologija — V **71**<br>Lietuvių kalba ir literatūra — VB **86** | литовский по общему курсу (B) | **6,48** |  |  |
| 4 | Kauno kolegija<br>**Apskaita**<br>Kaunas, Nuolatinė (NL) · Mišri | Istorija — V **57**<br>Biologija — V **71**<br>Lietuvių kalba ir literatūra — VA **86** | нет первого предмета | **4,28** |  |  |
| 5 | Kauno kolegija<br>**Apskaita**<br>Kaunas, Nuolatinė (NL) · Mišri | Matematika — VA **62**<br>Istorija — V **79**<br>Biologija — V **43**<br>Lietuvių kalba ir literatūra — VA **94**<br>Vokiečių kalba — V **91** | два иностранных языка | **7,76** |  |  |
| 6 | Kauno kolegija<br>**Apskaita**<br>Kaunas, Nuolatinė (NL) · Mišri | Matematika — VA **100**<br>Istorija — V **100**<br>Biologija — V **100**<br>Lietuvių kalba ir literatūra — VA **100** | все оценки 100 | **10,00** |  |  |
| 7 | Kauno kolegija<br>**Apskaita**<br>Kaunas, Nuolatinė (NL) · Mišri | Matematika — VA **30**<br>Istorija — V **30**<br>Biologija — V **30**<br>Lietuvių kalba ir literatūra — VA **30** | все оценки 30 (нижняя граница) | **3,00** |  |  |
| 8 | Kauno kolegija<br>**Automatika ir robotika**<br>Kaunas, Nuolatinė (NL) · Mišri | Matematika — VA **83**<br>Fizika — V **47**<br>Biologija — V **95**<br>Lietuvių kalba ir literatūra — VA **61** | полный набор | **7,38** |  |  |
| 9 | Kauno kolegija<br>**Automatika ir robotika**<br>Kaunas, Nuolatinė (NL) · Mišri | Matematika — VA **83**<br>Fizika — V **37**<br>Biologija — V **95**<br>Lietuvių kalba ir literatūra — VA **61** | одна оценка в интервале 30–39 | **7,18** |  |  |
| 10 | Vytauto Didžiojo universitetas<br>**Biotechnologija**<br>Kaunas, Nuolatinė (NL) · Dieninė | Matematika — VA **55**<br>Chemija — V **66**<br>Biologija — V **77**<br>Lietuvių kalba ir literatūra — VA **88** | полный набор | **6,82** |  |  |
| 11 | Vytauto Didžiojo universitetas<br>**Apskaita ir finansai**<br>Kaunas, Nuolatinė (NL) · Dieninė | Matematika — VB **73**<br>Istorija — V **49**<br>Biologija — V **58**<br>Lietuvių kalba ir literatūra — VA **64** | математика B | **5,46** |  |  |
| 12 | Kauno kolegija<br>**Kibernetinės sistemos ir sauga**<br>Alytus, Nuolatinė (NL) · Mišri | Matematika — VA **91**<br>Informatika — V **82**<br>Biologija — V **73**<br>Lietuvių kalba ir literatūra — VA **64** | полный набор | **8,02** |  |  |
| 13 | Kauno kolegija<br>**Akušerija**<br>Kaunas, Nuolatinė (NL) · Mišri | Biologija — V **76**<br>Chemija — V **59**<br>Fizika — V **84**<br>Lietuvių kalba ir literatūra — VA **67** | полный набор | **7,24** |  |  |
| 14 | Kauno kolegija<br>**Akušerija**<br>Kaunas, Nuolatinė (NL) · Mišri | Biologija — V **76**<br>Chemija — V **84**<br>Lietuvių kalba ir literatūra — VA **67** | нет второго предмета | **6,06** |  |  |
| 15 | Vytauto Didžiojo universitetas<br>**Anglų filologija**<br>Kaunas, Nuolatinė (NL) · Dieninė | Lietuvių kalba ir literatūra — VA **81**<br>Istorija — V **63**<br>Biologija — V **45**<br>Anglų kalba — V **72** | литовский первым, один иностранный | **6,84** |  |  |
| 16 | Vytauto Didžiojo universitetas<br>**Anglų filologija**<br>Kaunas, Nuolatinė (NL) · Dieninė | Lietuvių kalba ir literatūra — VA **81**<br>Istorija — V **63**<br>Biologija — V **45**<br>Anglų kalba — V **72**<br>Vokiečių kalba — V **88** | литовский первым, два иностранных | **7,70** |  |  |
| 17 | Vytauto Didžiojo universitetas<br>**Anglų filologija**<br>Kaunas, Nuolatinė (NL) · Dieninė | Lietuvių kalba ir literatūra — VB **81**<br>Istorija — V **63**<br>Biologija — V **45**<br>Anglų kalba — V **72** | литовский первым, по общему курсу | **5,87** |  |  |
| 18 | Vytauto Didžiojo universitetas<br>**Aplinkotyra ir aplinkos apsauga**<br>Kaunas, Nuolatinė (NL) · Dieninė | Matematika — VA **39**<br>Informatika — V **51**<br>Biologija — V **62**<br>Lietuvių kalba ir literatūra — VA **74** | полный набор | **5,30** |  |  |
| 19 | Kauno kolegija<br>**Skaitmeninė ir kūrybinė komunikacija**<br>Kaunas, Nuolatinė (NL) · Mišri | Lietuvių kalba ir literatūra — VA **87**<br>Istorija — V **93**<br>Biologija — V **41**<br>Anglų kalba — V **56** | полный набор | **7,28** |  |  |
| 20 | Vytauto Didžiojo universitetas<br>**Viešasis administravimas**<br>Kaunas, Nuolatinė (NL) · Dieninė | Istorija — V **69**<br>Matematika — VA **78**<br>Biologija — V **87**<br>Lietuvių kalba ir literatūra — VA **96** | история первой | **7,98** |  |  |
| 21 | Kauno kolegija<br>**Turizmo ir viešbučių vadyba**<br>Kaunas, Nuolatinė (NL) · Mišri | Istorija — V **44**<br>Matematika — VA **55**<br>Biologija — V **66**<br>Lietuvių kalba ir literatūra — VA **77** | полный набор | **5,72** |  |  |
| 22 | Vytauto Didžiojo universitetas<br>**Viešoji komunikacija**<br>Kaunas, Nuolatinė (NL) · Dieninė | Lietuvių kalba ir literatūra — VA **92**<br>Istorija — V **38**<br>Biologija — V **65**<br>Anglų kalba — V **70** | полный набор | **7,14** |  |  |
| 23 | Vytauto Didžiojo universitetas<br>**Ikimokyklinė ir priešmokyklinė pedagogika**<br>Kaunas, Nuolatinė (NL) · Dieninė | Lietuvių kalba ir literatūra — VA **58**<br>Matematika — VA **67**<br>Biologija — V **76**<br>Istorija — V **85** | литовский первым, история четвёртой | **6,88** |  |  |
| 24 | Vilniaus universitetas<br>**Akušerija**<br>Vilnius, Nuolatinė (NL) · Dieninė | Biologija — V **97**<br>Chemija — V **89**<br>Fizika — V **54**<br>Lietuvių kalba ir literatūra — VA **63** | полный набор | **8,00** |  |  |
| 25 | Kauno kolegija<br>**Socialinis darbas**<br>Kaunas, Nuolatinė (NL) · Mišri | Istorija — V **75**<br>Matematika — VA **85**<br>Lietuvių kalba ir literatūra — VA **95** | нет третьего предмета | **6,60** |  |  |
| 26 | Kauno kolegija<br>**Teisė**<br>Kaunas, Nuolatinė (NL) · Mišri | Istorija — V **61**<br>Matematika — VA **72**<br>Biologija — V **83**<br>Lietuvių kalba ir literatūra — VA **94** | право: полный набор | **7,42** |  |  |
| 27 | Vilniaus universitetas<br>**Medicina**<br>Vilnius, Nuolatinė (NL) · Dieninė | Biologija — V **90**<br>Chemija — V **80**<br>Matematika — VA **60**<br>Fizika — V **70**<br>Lietuvių kalba ir literatūra — VA **50** | медицина: среднее химии и математики | **7,40** |  |  |
| 28 | Vilniaus universitetas<br>**Medicina**<br>Vilnius, Nuolatinė (NL) · Dieninė | Biologija — V **90**<br>Chemija — V **80**<br>Matematika — VB **60**<br>Fizika — V **70**<br>Lietuvių kalba ir literatūra — VA **50** | медицина: математика B в среднем | **7,22** |  |  |
| 29 | Vilniaus kolegija<br>**Maisto technologija**<br>Vilnius, Nuolatinė (NL) · Sesijinė | Matematika — VA **66**<br>Chemija — V **99**<br>Biologija — V **33**<br>Lietuvių kalba ir literatūra — VA **77** | веса 0,4 · 0,1 · 0,3 · 0,2 | **7,48** |  |  |
| 30 | Vytauto Didžiojo universitetas<br>**Agronomija**<br>Kaunas, Nuolatinė (NL) · Dieninė | Biologija — V **52**<br>Chemija — V **64**<br>Fizika — V **78**<br>Lietuvių kalba ir literatūra — VA **91** | сельское хозяйство: веса 0,4 · 0,1 · 0,3 · 0,2 | **6,88** |  |  |
