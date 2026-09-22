# Переписка с приёмными комиссиями

План 2026-09-21, неделя 2, пункт 04. Разбор формул автоматикой (правило 5/6
CLAUDE.md: «автоматика ничего не додумывает») упёрся в места, где документ
приёма не говорит, как считать. Единственный способ сдвинуться — спросить
сам вуз. Отправка — ваше действие, не моё (правило проекта: сообщения от
вашего имени я не отправляю). Здесь: регламент учёта переписки и шесть
черновиков писем, готовых к отправке или правке.

**Почему сейчас.** Приёмная кампания 2026 года кончилась, к правилам 2027/28
(публикация обязательна до 30 ноября) вузы ещё не приступили — сентябрь
единственное спокойное окно перед декабрьской сверкой.

## Регламент учёта

Одно письмо на вуз, не на вопрос — три-четыре вопроса списком, с точной
цитатой непонятного пункта и коротким объяснением, кто мы. Таблица ниже —
единственный источник состояния переписки; заполняете при отправке и при
получении ответа.

| Вуз | Отправлено | Кому | Ответ получен | Что ответили | Ссылка на файл ответа |
|---|---|---|---|---|---|
| ЛУ | — | — | — | — | — |
| RSU | — | — | — | — | — |
| РТУ | — | — | — | — | — |
| LBTU | — | — | — | — | — |
| DU | — | — | — | — | — |
| Ventspils | — | — | — | — | — |

**Ответ вуза приравнивается к источнику фактов** (правило 5 CLAUDE.md) наравне
с утверждённым PDF: сохраните его текст (письмо целиком, со всеми
формальностями, не выжимку) рядом с документом-источником этого вуза —
`docs/source-documents/<вуз>/otbilde-YYYY-MM-DD.txt` (или скриншот/PDF письма,
если ответ пришёл не текстом) — и впишите путь в столбец «Ссылка» здесь.
Дальше я перенесу разбор формулы с новым правилом в `pipeline/src/formulas_*.py`.

**Если ответа нет к декабрьскому циклу сверки** — соответствующие программы
остаются неразобранными, страница честно говорит «формула не разобрана»,
подтверждать нечего.

## Шаблон

```
Kam: <адрес приёмной комиссии>
Tēma: Jautājumi par konkursa vērtējuma aprēķināšanu <programma/studiju virziens>

Labdien!

Veidojam bezmaksas informatīvu portālu Latvijas skolu absolventiem par
uzņemšanu augstskolās (studiju programmu katalogs, konkursa punktu
kalkulators). Strādājam pēc <Jūsu Uzņemšanas noteikumu> teksta, taču
<X> punktā mums nav skaidrs, kā aprēķina rezultātu šādā gadījumā:

<jautājumi>

Būsim pateicīgi par precizējumu — tas ļaus mums pareizi parādīt
konkursa vērtējuma aprēķinu Jūsu programmām.

Ar cieņu,
<vārds, uzvārds>
<kontakti>
```

## Черновики по вузам

### ЛУ

**Адрес:** приёмная комиссия ЛУ — уточнить на
[lu.lv/gribustudet/uznemsanas-kartiba](https://www.lu.lv/gribustudet/uznemsanas-kartiba/pamatstudijas/)
(общий адрес не найден в самом документе правил).

**Источник:** «Uzņemšanas prasības un kritēriji pamatstudiju programmās
2026./2027. akadēmiskajā gadā» (LU rīkojums Nr. 1-4/506, `docs/source-documents/lu/uzn-prasibas-pamat-2026-27.pdf`).

```
Kam: <adrese>
Tēma: Jautājumi par konkursa vērtējuma aprēķināšanu vairākās bakalaura programmās

Labdien!

Veidojam bezmaksas informatīvu portālu Latvijas skolu absolventiem par
uzņemšanu augstskolās. Strādājam pēc LU uzņemšanas prasību un kritēriju
2026./2027. akadēmiskajam gadam teksta (rīkojums Nr. 1-4/506), taču vairākos
punktos mums nav skaidrs, kā aprēķina konkursa vērtējumu:

1. Programmās, kur formulā ir "CE fizikā vai CE ķīmijā, vai CE bioloģijā"
   (piemēram, 2.7.2. "Ārstniecība"), — ja reflektants kārtojis vairākus no
   šiem eksāmeniem, konkursa vērtējumā ņem vērā tikai vienu (labāko?) vai
   summē visus?

2. Programmās "Fizika" (2.2.4.) un "Ķīmija" (2.7.8.) doti divi varianti
   ("1.a" un "1.b") ar atšķirīgiem svariem vienam un tam pašam CE komplektam.
   Pēc kāda kritērija nosaka, kurš variants attiecas uz konkrētu reflektantu?

3. Programmā "Filoloģija" (2.3.3.) un dažās citās ar apakšprogrammām katrai
   apakšprogrammai norādīta sava formula ar atšķirīgiem svariem. Vai
   apakšprogrammas uzskatāmas par atsevišķām konkursa vienībām reģistrācijā,
   vai reflektants konkurē vienā kopīgā sarakstā pēc kādas vienotas formulas?

Būsim pateicīgi par precizējumu.

Ar cieņu,
<vārds, uzvārds>
```

### RSU

**Адрес:** `uk@rsu.lv` (Uzņemšanas komisija — указан в документе правил).

**Источник:** «Uzņemšanas noteikumi īsā cikla, pirmā cikla un otrā cikla
studiju programmās 2026./2027. akadēmiskajam gadam» (RSU 1-PB-9/36/2025,
`docs/source-documents/rsu/uznemsanas-noteikumi-pamatstudijas-2026-27-rev1.pdf`).

```
Kam: uk@rsu.lv
Tēma: Jautājums par konkursa vērtēšanas kritērijiem vairākās programmās

Labdien!

Veidojam bezmaksas informatīvu portālu Latvijas skolu absolventiem par
uzņemšanu augstskolās. Strādājam pēc RSU uzņemšanas noteikumu 2026./2027.
akadēmiskajam gadam teksta (konsolidētā redakcija, 1-PB-9/36/2025), taču
vairāku programmu (piemēram, Audiologopēdija, Ergoterapija, Māszinības,
Farmācija, Medicīna, Uzturs) konkursa vērtēšanas kritērijos ir formulējums
"gala atzīme bioloģijā vai dabaszinībās" vai "CE ķīmijā vai bioloģijā".

Ja reflektantam vidējās izglītības dokumentā ir gan atzīme bioloģijā, gan
dabaszinībās (vai kārtoti abi CE — ķīmijā un bioloģijā) — konkursa vērtējumā
ņem vērā labāko no tiem, vai kādu citu kārtību?

Būsim pateicīgi par precizējumu.

Ar cieņu,
<vārds, uzvārds>
```

### РТУ

**Адрес:** уточнить на
[rtu.lv/lv/studijas/uznemsana](https://www.rtu.lv/lv/studijas/uznemsana/uznemsanas-noteikumi/uznemsanas-noteikumi-pamatstudijas)
(у РТУ нет утверждённого PDF, только страница — общий адрес на ней не
приведён).

**Источник:** «Uzņemšanas noteikumi īsā cikla un pirmā cikla studiju
programmās 2026./2027. akadēmiskajā gadā», 31.1. punkts (RTU Senāta
24.11.2025. protokollēmums Nr. 697, `docs/source-documents/rtu/uznemsanas-noteikumi-pamatstudijas-2026-27.html`).

Два независимых вопроса — по формуле и по данным каталога; можно отправить
одним письмом или сразу двумя, если у РТУ разные адреса для методических и
технических вопросов.

```
Kam: <adrese>
Tēma: Jautājumi par konkursa vērtējuma aprēķinu un studiju virzieniem pamatstudiju programmās

Labdien!

Veidojam bezmaksas informatīvu portālu Latvijas skolu absolventiem par
uzņemšanu augstskolās. Strādājam pēc RTU uzņemšanas noteikumu 2026./2027.
akadēmiskajam gadam teksta, 31.1. punkta, taču mums nav skaidrs:

1. Formulā "CE procentu kopvērtējumu fizikā un/vai ķīmijā reizina ar
   koeficientu 1,00" (31.1. punkts) — ja reflektants kārtojis abus CE
   (fizikā un ķīmijā), vērtējumā ņem vērā labāko no tiem, vai abus summē?

2. Vai ir publiski pieejams saraksts, kas katru pamatstudiju programmu
   piesaista kādam no 31.1.–31.9. punktā minētajiem studiju virzieniem
   (piemēram, "Informācijas tehnoloģija, datortehnika, elektronika,
   telekomunikācijas, datorvadība un datorzinātne")? Reģistrā
   (rtu.lv/lv/studijas/visas-studiju-programmas) šī piesaiste nav norādīta.

Būsim pateicīgi par precizējumu.

Ar cieņu,
<vārds, uzvārds>
```

### LBTU

**Адрес:** `edokuments@lbtu.lv` (адрес приёма документов из шапки правил;
если для методических вопросов есть отдельный адрес приёмной комиссии,
замените).

**Источник:** «Uzņemšanas noteikumi pamatstudijās, ņemot vērā centralizēto
eksāmenu rezultātus 2026./2027. studiju gadam» (LBTU Senāta 12.11.2025.
lēmums Nr. 12-62, `docs/source-documents/lbtu/uznemsanas-noteikumi-pamatstudijas-2026-27-arce-12052026.pdf`).

```
Kam: edokuments@lbtu.lv
Tēma: Jautājumi par konkursa balles aprēķina formulu

Labdien!

Veidojam bezmaksas informatīvu portālu Latvijas skolu absolventiem par
uzņemšanu augstskolās. Strādājam pēc LBTU uzņemšanas noteikumu (ņemot vērā
CE rezultātus) 2026./2027. studiju gadam teksta, taču divi jautājumi mums
nav skaidri:

1. Punktā par konkursa balles aprēķina formulu teikts: "Ja centralizētie
   eksāmeni ir kārtoti augstākajā mācību satura apguves līmenī, papildus
   tiek pielietots koeficients 1,25." Uz kuru formulas daļu šis koeficients
   attiecas — uz visu iegūto balli summā, vai tikai uz to CE, kas kārtots
   augstākajā līmenī?

2. Formulā ir loceklis "2 × (CE fakultātes obligāti noteiktajā mācību
   priekšmetā vai 10 × GA obligāti noteiktajā mācību priekšmetā)". Ja
   reflektantam ir gan attiecīgā CE rezultāts, gan gada atzīme šajā
   priekšmetā, — vērtējumā izmanto CE, vai to, kas dod augstāku rezultātu?

Būsim pateicīgi par precizējumu.

Ar cieņu,
<vārds, uzvārds>
```

### DU

**Адрес:** уточнить на
[du.lv/gribu-studet/uznemsana](https://du.lv/gribu-studet/uznemsana/)
(в PDF правил общий адрес не приведён; там же телефон приёмной комиссии
65421198, если нужен запасной канал).

**Источник:** «Uzņemšanas noteikumi pilna un nepilna laika pamatstudijām
2026. gadā» (DU Senāta protokols Nr. 15, 21.10.2025, grozījumi 11.06.2026,
`docs/source-documents/du/uznemsanas-noteikumi-pamatstudijas-2026-27.pdf`)
и «Studiju iespējas» (коэффициенты по программам,
`docs/source-documents/du/studiju-iespejas-pamatstudijas-2026-27-08-2026.pdf`).

```
Kam: <adrese>
Tēma: Jautājums par konkursa punktu aprēķinu vairākās programmās

Labdien!

Veidojam bezmaksas informatīvu portālu Latvijas skolu absolventiem par
uzņemšanu augstskolās. Strādājam pēc DU uzņemšanas noteikumu un "Studiju
iespējas" dokumenta 2026. gadam teksta, taču vairākās programmās (piemēram,
Informācijas tehnoloģijas, Māszinības) papildu punktu ailē ir norādīts gan
CE priekšmetā, gan "eksāmens/ieskaite atestātā" tajā pašā priekšmetā.

Ja reflektantam ir gan CE rezultāts, gan atzīme atestātā šajā priekšmetā, —
konkursa punktu summā izmanto CE, atestāta atzīmi, vai labāko no tiem?

Būsim pateicīgi par precizējumu.

Ar cieņu,
<vārds, uzvārds>
```

### Ventspils Augstskola

**Адрес:** `studijas@venta.lv`.

**Источник:** «Uzņemšanas noteikumi un imatrikulācijas kārtība Ventspils
Augstskolā 2026./2027. akadēmiskajā gadā», 1. pielikums (VeA Senāta lēmums
Nr. 25-39, ar grozījumiem Nr. 26-3 un Nr. 26-28,
`docs/source-documents/venta/uznemsanas-noteikumi-2026-27-pielikums-2-grozits-06-2026.pdf`).

```
Kam: studijas@venta.lv
Tēma: Jautājums par konkursa rezultāta aprēķinu programmā "Elektronikas inženierija"

Labdien!

Veidojam bezmaksas informatīvu portālu Latvijas skolu absolventiem par
uzņemšanu augstskolās. Strādājam pēc VeA uzņemšanas noteikumu 1. pielikuma
teksta, taču programmā "Elektronikas inženierija" mums nav skaidrs
formulas pēdējais loceklis.

Pārējiem locekļiem summa dod tieši 100 punktus (P1×0,6 + P2×0,2 + P3×0,1 +
0,1×vidējā vērtība). Papildus tam formulā ir "P4 – CE fizikā (ja ir
kārtots)" ar koeficientu 0,1, kas — ja fizika kārtota — paaugstina
maksimāli iespējamo rezultātu līdz 110 punktiem 100 punktu skalā.

Vai P4 tiešām summējas virs pārējiem locekļiem (t.i., fizikas CE dod
papildu punktus bez maksimuma), vai tas kādā gadījumā aizstāj kādu no
pārējiem locekļiem?

Būsim pateicīgi par precizējumu.

Ar cieņu,
<vārds, uzvārds>
```

## После ответа

Когда ответ придёт, пришлите мне его текст (или файл) — я:

1. сохраню его рядом с документом-источником (`docs/source-documents/<вуз>/`)
   как ещё одну часть протокола источника;
2. если ответ снимает неопределённость — расширю `pipeline/src/formulas_*.py`
   (для РТУ отдельно нужен признак «программа → направление», это не только
   про формулу, см. письмо РТУ выше);
3. если ответ не снимает — переведу соответствующие блоки в состояние
   «спорно» (план, пункт 03, следующая неделя) с причиной и ссылкой на ответ,
   а не оставлю прозой в комментариях кода.
