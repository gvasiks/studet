# Подтверждение направлений программ — по правилу, не по строке

План 2026-09-21, неделя 3, пункт 01. Состояние на 2026-09-22.

**Зачем так.** Правило 6 CLAUDE.md требует человека там, где ошибка стоит
дорого. Направление программы в этот список не входит (там: конкурсная
формула, дедлайн подачи, стоимость и бюджетные места, языковое требование,
через кого подача) — ошибка в направлении означает, что программа
попала не в тот фильтр интересов на анкете, а не что человек подал
документы не туда. Подтверждать 892 строки по одной в Studio при 4 ч/нед —
почти полгода ради факта с почти нулевой ценой ошибки. Поэтому здесь
подтверждается не строка, а **правило**: вы читаете набор правил и отдельно
проверяете выборку размеченных программ, и если ошибок нет — вся
классифицированная разметка подтверждается разом.

**Что это разблокирует:** блок «что стало с выпускниками» на карточках
программ (3309 загруженных записей, сейчас скрыты), фильтр каталога по
интересам во втором шаге анкеты (сейчас читает неподтверждённые данные).

## 1. Как это устроено

Разметка — код, не человеческий выбор: `pipeline/src/programme_fields.py`
хранит 142 правила (регулярное выражение по названию программы →
1–3 кандидата кода из классификатора ИЗМ), сгруппированных в 18 тематических
разделов. Правила проверяются по порядку, срабатывает первое подходящее;
специфичные случаи стоят раньше общих.

Когда правило даёт несколько кандидатов (например, «датчик» IT-программы
может быть 481, 483 или 484), выбор между ними делает не правило, а
**реальные данные**: `choose_field()` берёт первый код, по которому для
этого вуза и уровня действительно есть строки в открытой статистике
выпускников ИЗМ/ЦСУ. Если данных нет ни по одному кандидату — берётся
первый из списка, и это видно в отчёте как «нет данных» (может значить и
«ячейка скрыта — меньше 30 выпускников», и «правило промахнулось»).

Программы, для которых ни одно правило не подошло, в базу не попадают
вовсе (раздел 4 ниже) — «автоматика ничего не додумывает».

## 2. Правила (читаете и утверждаете целиком)

142 правила в 18 разделах. Формат: **ключевые слова** → код (область).
Полный текст правил — `pipeline/src/programme_fields.py`, здесь —
пересказ для чтения, не копия синтаксиса регулярных выражений.

секций: 18, правил всего: 142

### право (2)
- **pre-trial, pirmstiesas** → 380 (Tiesības)
- **law, tiesīb, tiesību** → 380 (Tiesības)

### здоровье (26)
- **medicīnas inženierija, medical engineering** → 529 (Inženierzinātnes), 522 (Inženierzinātnes), 525 (Inženierzinātnes)
- **biomedic** → 421 (Dzīvās dabas zinātnes), 420 (Dzīvās dabas zinātnes)
- **dental hygien, zobu higiēn** → 724 (Veselības aprūpe)
- **health care, healthcare** → 720 (Veselības aprūpe), 721 (Veselības aprūpe)
- **public health, sabiedrības veselīb** → 722 (Veselības aprūpe)
- **physician assistant, ārsta palīg** → 722 (Veselības aprūpe)
- **nutrition, uztur** → 722 (Veselības aprūpe)
- **orthotics, prosthetics, ortoz, protēz** → 726 (Veselības aprūpe), 725 (Veselības aprūpe)
- **sociālā/sociālais rehabilitācij…** (правило добавлено 2026-09-22 при подготовке этой выборки — см. раздел 5) → 762 (Sociālie pakalpojumi)
- **occupational therapy, physiotherap, rehabilitation, massage, ergoterap, fizioterap, rehabilitācij, masāž** → 726 (Veselības aprūpe)
- **physical activity** → 813 (Personiskie pakalpojumi (tūrisms, sports))
- **ārstniecīb** → 723 (Veselības aprūpe), 721 (Veselības aprūpe)
- **podolo[gģ]** → 726 (Veselības aprūpe)
- **sociālā aprūpe** → 762 (Sociālie pakalpojumi)
- **radiolo[gģ]** → 725 (Veselības aprūpe)
- **sterilizācij, mākslīgā asinsrite** → 725 (Veselības aprūpe)
- **dentist, zobārst** → 724 (Veselības aprūpe)
- **nursing, māszin, midwif, vecmāt** → 723 (Veselības aprūpe)
- **radiograph** → 725 (Veselības aprūpe)
- **optometr** → 726 (Veselības aprūpe)
- **pharmac, farmāc** → 727 (Veselības aprūpe)
- **logopēd, speech therap** → 726 (Veselības aprūpe)
- **medicine, medicīna** → 721 (Veselības aprūpe)
- **social work, sociālais darbs, sociālais rehabilit, sociālā rehabilit, supervīzij** → 762 (Sociālie pakalpojumi)
- **occupational health, occupational safety, labour protection, darba aizsardzīb** → 862 (Drošības pakalpojumi)
- **sport** → 813 (Personiskie pakalpojumi (tūrisms, sports))
- **cosmetolog, kosmetolo[gģ]** → 815 (Personiskie pakalpojumi (tūrisms, sports))

### образование (3)
- **speciālā izglītība, special education** → 141 (Izglītība), 142 (Izglītība)
- **izglītības zinātn, education science, educational science** → 142 (Izglītība), 141 (Izglītība)
- **teacher, skolotāj, pedagog, pirmsskolas** → 141 (Izglītība)

### туризм (1)
- **tourism, tūrism, hospitality, hotel, viesnīc** → 812 (Personiskie pakalpojumi (tūrisms, sports)), 811 (Personiskie pakalpojumi (tūrisms, sports))

### архитектура, строительство (6)
- **architect, arhitekt** → 581 (Arhitektūra un būvniecība)
- **geoinformat** → 443 (Fizikālās zinātnes)
- **geomatic, ģeomātik** → 582 (Arhitektūra un būvniecība), 443 (Fizikālās zinātnes)
- **real estate, nekustam** → 345 (Bizness un pārvaldība), 582 (Arhitektūra un būvniecība)
- **mašīnu un aparātu** → 521 (Inženierzinātnes)
- **būves inform, inženiersistēm, būvniecīb, construction, building, būvuzņēm, transportbūv, siltuma, gāzes, heating, ēku** → 582 (Arhitektūra un būvniecība)

### искусство и дизайн (11)
- **audiovisual, film, audiovizuāl, new media, jauno mediju** → 213 (Māksla), 214 (Māksla)
- **radošās industrijas, creative industries** → 345 (Bizness un pārvaldība), 214 (Māksla)
- **industrial design, industriālais dizains** → 214 (Māksla)
- **dizaina inženierija** → 521 (Inženierzinātnes)
- **materiālu tehnoloģija un dizains, dizaina tehnoloģijas** → 542 (Ražošana un pārstrāde), 214 (Māksla)
- **stage design, scenograph, scenogrāf** → 211 (Māksla), 212 (Māksla)
- **interior, brand design, game design, computer game, digital visualization, visual communication, vizuālā komunikācija, dizain, design** → 214 (Māksla)
- **music, mūzik** → 212 (Māksla)
- **theatre, theater, teātr, acting, aktier, drama, dance, dejas, directing, režij** → 212 (Māksla)
- **painting, glezn, sculpture, tēlniec, ceramic, keramik, glass art, stikl, graphic art, drawing, zīmēšan, environmental art, restoration, restaurācij, curatorial, kuratori** → 211 (Māksla)
- **название ровно "Art"/"Arts", или содержит "māksla"** → 211 (Māksla)

### гуманитарные (11)
- **theolog, teoloģ, religio** → 221 (Humanitārās zinātnes)
- **philosoph, filozof** → 226 (Humanitārās zinātnes), 225 (Humanitārās zinātnes)
- **history, vēstur, archeolog, archaeolog** → 224 (Humanitārās zinātnes), 225 (Humanitārās zinātnes)
- **latvian studies, latvistik** → 223 (Humanitārās zinātnes)
- **cultural and environmental heritage, kultūras un vides mantojum, cultural heritage** → 227 (Humanitārās zinātnes), 224 (Humanitārās zinātnes)
- **culture management, kultūras vadīb, cultural project, kultūras projekt** → 345 (Bizness un pārvaldība), 214 (Māksla)
- **digital humanities, digitālās humanitārās** → 222 (Humanitārās zinātnes), 227 (Humanitārās zinātnes)
- **digitālā kultūra** → 222 (Humanitārās zinātnes), 321 (Žurnālistika un informācija)
- **valodas, saziņa, language and culture, eastern european** → 227 (Humanitārās zinātnes), 222 (Humanitārās zinātnes), 345 (Bizness un pārvaldība)
- **translat, tulkoš, terminolog, philolog, filolo[gģ], linguist, lingvist, valodu un literatūr, european languages, eiropas valodu, language, zīmju valod** → 222 (Humanitārās zinātnes)
- **anthropolog, asian, āzijas, cultural studies, kultūrvide** → 227 (Humanitārās zinātnes), 314 (Sociālās un uzvedības zinātnes)

### социальные науки (9)
- **psycholog, psiholo[gģ]** → 313 (Sociālās un uzvedības zinātnes)
- **sociolog, socioloģ** → 314 (Sociālās un uzvedības zinātnes)
- **political, politolog** → 312 (Sociālās un uzvedības zinātnes)
- **international relations, starptautisk… attiecīb, diplomac** → 310 (Sociālās un uzvedības zinātnes), 312 (Sociālās un uzvedības zinātnes)
- **social sciences, sociālās zinātnes** → 310 (Sociālās un uzvedības zinātnes)
- **international economics and commercial diplomacy** → 311 (Sociālās un uzvedības zinātnes), 310 (Sociālās un uzvedības zinātnes)
- **international finance and economics** → 343 (Bizness un pārvaldība), 311 (Sociālās un uzvedības zinātnes)
- **european business studies** → 345 (Bizness un pārvaldība), 311 (Sociālās un uzvedības zinātnes)
- **business economics, european economics, economics and business, ekonomika un uzņēmējdarb, digital economy, circular economy** → 311 (Sociālās un uzvedības zinātnes), 345 (Bizness un pārvaldība)

### математика, физика, химия, биология, среда (10)
- **inženiermatemāt** → 460 (Matemātika un statistika)
- **mathematic, statistic, matemāt** → 460 (Matemātika un statistika)
- **particle physics, daļiņu fizika, physics, fizika** → 441 (Fizikālās zinātnes), 440 (Fizikālās zinātnes)
- **ķīmija un ķīmijas tehnoloģija, ķīmijas tehnoloģ, chemistry, materials, ķīmija, materiālzinātne** → 524 (Inženierzinātnes), 442 (Fizikālās zinātnes)
- **biotechnolog, biotehnolo[gģ], bioengineering, bioinženier** → 524 (Inženierzinātnes), 421 (Dzīvās dabas zinātnes), 529 (Inženierzinātnes)
- **chemistry, ķīmij** → 442 (Fizikālās zinātnes)
- **biolog, bioloģ** → 421 (Dzīvās dabas zinātnes)
- **vides inženierija, environmental engineering** → 850 (Vides aizsardzība), 529 (Inženierzinātnes), 521 (Inženierzinātnes)
- **environmental science, vides zinātn** → 850 (Vides aizsardzība), 440 (Fizikālās zinātnes)
- **geograph, ģeogrāf, geolog, ģeolog** → 443 (Fizikālās zinātnes), 440 (Fizikālās zinātnes)

### финансы, учёт, маркетинг, коммуникации (8)
- **financial engineering, finanšu inženier** → 343 (Bizness un pārvaldība)
- **finanšu pārvaldības informācijas** → 343 (Bizness un pārvaldība)
- **accounting and finance, grāmatvedīb** → 344 (Bizness un pārvaldība), 343 (Bizness un pārvaldība)
- **financial management, finance, finanses, finanš, banking, banku** → 343 (Bizness un pārvaldība)
- **accounting, audit** → 344 (Bizness un pārvaldība)
- **public relations, sabiedriskās attiecības, komunikācija un sabiedr** → 321 (Žurnālistika un informācija), 342 (Bizness un pārvaldība)
- **marketing, mārketing, advertising, reklām** → 342 (Bizness un pārvaldība)
- **library, information management, informācijas pārvald** → 322 (Žurnālistika un informācija)

### ИТ (проверяется до общего «управление» — иначе «IT project management» уйдёт в 345) (6)
- **programmēšanas speciālists, programmer, programmēšana, programming** → 484 (Datorzinātnes), 481 (Datorzinātnes), 483 (Datorzinātnes)
- **programmēšanas inženieris** → 484 (Datorzinātnes), 481 (Datorzinātnes), 483 (Datorzinātnes)
- **artificial intelligence, intelektuālas robotizētas, intelligent robotic, e-studiju, e-learning, virtuālā realitāte, virtual reality, realitāt, gaming, spēļoš** → 481 (Datorzinātnes), 483 (Datorzinātnes), 523 (Inženierzinātnes)
- **cyber, kiberdrošīb** → 481 (Datorzinātnes), 483 (Datorzinātnes)
- **computer engineering, smart electronic, viedās elektronisk, electronic, elektronik, telecommunication, telekomunik, adaptron, robot, mechatronic, mehatronik, telematic, telemātik** → 523 (Inženierzinātnes), 522 (Inženierzinātnes), 481 (Datorzinātnes)
- **computer science, datorzinātn, information technolog, informācijas tehnolo[gģ], informātik, informatics, software, datorsistēm, computer systems, data analytics, viedās datortehnolo[gģ], savstarpēji saistītu sistēmu, information systems, informācijas sistēm, it project, biznesa informātika, sociotehnisk** → 481 (Datorzinātnes), 483 (Datorzinātnes), 484 (Datorzinātnes)

### энергетика, материалы, машиностроение (25)
- **electric, elektriskās iekārt, elektroenerģ, elektrotehnolo[gģ], energy, enerģ** → 522 (Inženierzinātnes)
- **materiālzinātne un nanotehnolo[gģ], nanotechn, materials science** → 524 (Inženierzinātnes), 442 (Fizikālās zinātnes), 543 (Ražošana un pārstrāde)
- **šķiedru, fibre, fiber, textile** → 542 (Ražošana un pārstrāde), 543 (Ražošana un pārstrāde)
- **materiālu inženierija, materials engineering** → 543 (Ražošana un pārstrāde), 524 (Inženierzinātnes)
- **industrial engineering and management, industriālā inženierija un vadība** → 526 (Inženierzinātnes), 521 (Inženierzinātnes), 345 (Bizness un pārvaldība)
- **laser, lāzer** → 521 (Inženierzinātnes), 442 (Fizikālās zinātnes)
- **ražošanas tehnoloģija, manufacturing** → 521 (Inženierzinātnes), 526 (Inženierzinātnes)
- **biosystems, biosistēm** → 621 (Lauksaimniecība un mežsaimniecība), 521 (Inženierzinātnes)
- **food, pārtik** → 541 (Ražošana un pārstrāde)
- **militār, military** → 863 (Drošības pakalpojumi)
- **kuģu mehānik, kuģa mehāniķ, kuģu elektro** → 525 (Inženierzinātnes)
- **kuģa vadīšan, jūras transport, pārvadājumu organizācij** → 840 (Transporta pakalpojumi)
- **autoserv** → 525 (Inženierzinātnes)
- **aukstumtehnik, refrigerat** → 522 (Inženierzinātnes), 521 (Inženierzinātnes)
- **kokapstrād** → 543 (Ražošana un pārstrāde)
- **augkopīb, lauksaimniec, agricultur** → 621 (Lauksaimniecība un mežsaimniecība)
- **tiesisk… regulēj…** → 380 (Tiesības)
- **komercdarb** → 345 (Bizness un pārvaldība)
- **pasākumu producēšan** → 345 (Bizness un pārvaldība)
- **policij** → 861 (Drošības pakalpojumi)
- **gaisa kuģ, aircraft** → 525 (Inženierzinātnes)
- **gaisa satiksm, air traffic** → 840 (Transporta pakalpojumi)
- **elektronisko iekārt** → 523 (Inženierzinātnes)
- **aviation, aviācij, aeronaut, aerokosm, aerospace, autotransport, motor vehicle** → 525 (Inženierzinātnes), 840 (Transporta pakalpojumi)
- **machine, mašīn, mechanic, mehānika, inženiertehnika, machinery** → 521 (Inženierzinātnes)

### логистика и транспорт (5)
- **transport and (business) logistics, intelligent transport, telematics and logistics** → 840 (Transporta pakalpojumi)
- **business logistics, uzņēmējdarbības loģistik, piegādes ķēd, supply chain** → 345 (Bizness un pārvaldība), 840 (Transporta pakalpojumi)
- **international trade, tirdzniec** → 341 (Bizness un pārvaldība), 345 (Bizness un pārvaldība), 840 (Transporta pakalpojumi)
- **loģistik, logistic** → 345 (Bizness un pārvaldība), 840 (Transporta pakalpojumi)
- **transport** → 840 (Transporta pakalpojumi)

### безопасность (1)
- **security, drošīb, border, robež, fire, ugunsdrošīb, civil protection, civilā aizsardzīb, crisis, krīz, risks** → 861 (Drošības pakalpojumi), 862 (Drošības pakalpojumi), 345 (Bizness un pārvaldība)

### журналистика и коммуникации (после PR и ИТ) (1)
- **journalism, žurnālist, media, mediju, communicat, komunikācij, saziņ** → 321 (Žurnālistika un informācija)

### экономика (1)
- **biznesa vides** → 345 (Bizness un pārvaldība)

### управление (самое общее — последним) (2)
- **management, vadīb, vadīšana, vadība, administration, business, uzņēmējdarb, entrepreneur, līderīb, leadership, innovation, inovācij, quality, kvalitāt, vadībzinātn, strategic, customs, muit, regional, reģionāl, urban, pilsētu, human resource, personāl, sabiedrības pārvald** → 345 (Bizness un pārvaldība)
- **economics, ekonomika, ekonomik** → 311 (Sociālās un uzvedības zinātnes)

### добор NIID: программы только с латышским названием (14)
- **mežzinātn, mežinženier, forestry** → 623 (Lauksaimniecība un mežsaimniecība)
- **koksn, būvzinātn** → 543 (Ražošana un pārstrāde), 582 (Arhitektūra un būvniecība)
- **vide un ūdenssaimniec, vides, ūdens** → 850 (Vides aizsardzība), 529 (Inženierzinātnes)
- **zemes ierīcīb, mērniecīb** → 582 (Arhitektūra un būvniecība), 443 (Fizikālās zinātnes)
- **lielo datu, datu analītik** → 481 (Datorzinātnes), 483 (Datorzinātnes), 484 (Datorzinātnes)
- **starptautiskais bizness, international business** → 345 (Bizness un pārvaldība)
- **paplašinātās kompetences māsa** → 723 (Veselības aprūpe)
- **mākslas menedžment, arts management** → 345 (Bizness un pārvaldība)
- **vides plānošan** → 850 (Vides aizsardzība)
- **juridisk** → 380 (Tiesības)
- **sociālais darbinieks** → 762 (Sociālie pakalpojumi)
- **rakstniecīb** → 222 (Humanitārās zinātnes)
- **publiskā pārvald, public administration** → 345 (Bizness un pārvaldība), 310 (Sociālās un uzvedības zinātnes)
- **komandējošā sastāva, virsnieks** → 863 (Drošības pakalpojumi)

## 3. Выборка для проверки (58 программ)

Три группы, от самой рискованной к самой спокойной. Смотрите как минимум
группу «а», остальные — если есть время.

### а. Спорные по смыслу — 13 программ, где варианты лежат в РАЗНЫХ областях

Здесь правило дало несколько кандидатов, данные ИЗМ ни один не подтвердили,
и кандидаты относятся к разным укрупнённым областям (не просто «481 или
483», а например «бизнес или инженерия») — ошибка здесь реально меняет,
в какой фильтр попадёт программа. Каждая строка — **выбранный код** и через
запятую — отклонённые варианты.

- du/strategic-risks-and-crisis-management (bachelor) «Strategic risks and crisis management» → **861 (Drošības pakalpojumi)** (варианты: 862 (Drošības pakalpojumi), 345 (Bizness un pārvaldība))
- lka/creative-industries (bachelor) «Creative Industries» → **345 (Bizness un pārvaldība)** (варианты: 214 (Māksla))
- lka/creative-industries-and-growth-management (master) «Creative Industries and Growth Management» → **345 (Bizness un pārvaldība)** (варианты: 214 (Māksla))
- rsu/digital-strategy-and-artificial-intelligence-management (master) «Digital Strategy and Artificial Intelligence Management» → **481 (Datorzinātnes)** (варианты: 483 (Datorzinātnes), 523 (Inženierzinātnes))
- rsu/niid-26496 (master) «Krievijas un Eirāzijas studijas» → **227 (Humanitārās zinātnes)** (варианты: 314 (Sociālās un uzvedības zinātnes))
- rsu/social-anthropology (master) «Social Anthropology» → **227 (Humanitārās zinātnes)** (варианты: 314 (Sociālās un uzvedības zinātnes))
- tsi/digital-economy-and-business (doctoral) «Digital Economy and Business» → **311 (Sociālās un uzvedības zinātnes)** (варианты: 345 (Bizness un pārvaldība))
- tsi/telematics-and-logistics (doctoral) «Telematics and Logistics» → **523 (Inženierzinātnes)** (варианты: 522 (Inženierzinātnes), 481 (Datorzinātnes))
- via/24930-en (master) «Virtuālā realitāte un viedās tehnoloģijas» → **481 (Datorzinātnes)** (варианты: 483 (Datorzinātnes), 523 (Inženierzinātnes))
- via/24930-lv (master) «Virtuālā realitāte un viedās tehnoloģijas» → **481 (Datorzinātnes)** (варианты: 483 (Datorzinātnes), 523 (Inženierzinātnes))
- via/25652-en (doctoral) «Ekonomika un uzņēmējdarbība» → **311 (Sociālās un uzvedības zinātnes)** (варианты: 345 (Bizness un pārvaldība))
- via/25652-lv (doctoral) «Ekonomika un uzņēmējdarbība» → **311 (Sociālās un uzvedības zinātnes)** (варианты: 345 (Bizness un pārvaldība))
- via/28259 (master) «Paplašinātās realitātes spēļošana reālās pasaules izaicinājumiem (GRACE)» → **481 (Datorzinātnes)** (варианты: 483 (Datorzinātnes), 523 (Inženierzinātnes))

### б. Спорные по номеру, но не по смыслу — 28 программ (тот же укрупнённый раздел при любом выборе)

Кандидаты здесь тоже не подтверждены данными, но лежат в ОДНОЙ и той же
области (например 481 или 483 — оба «Datorzinātnes»), поэтому даже
неточный код не собьёт фильтр по интересам. Ниже, если коротко на них
смотреть.

- alberta/26928 (college) «Uzņēmējdarbība - Grāmatvedība» → **344 (Bizness un pārvaldība)** (вариант: 343)
- lbtu/information-technologies-for-sustainable-development (bachelor) «Information Technologies for Sustainable Development» → **481** (варианты: 483, 484)
- lbtu/information_technologies (master) «Information Technologies» → **481** (варианты: 483, 484)
- lbtu/niid-209 (bachelor) «Datorvadība un datorzinātne» → **481** (варианты: 483, 484)
- lbtu/niid-240 (doctoral) «Informācijas tehnoloģijas» → **481** (варианты: 483, 484)
- lbtu/niid-26833 (bachelor) «Ģeoinformātika un tālizpēte» → **481** (варианты: 483, 484)
- lka/cultural-heritage-governance-and-communication (master) «Cultural Heritage Governance and Communication» → **227** (вариант: 224)
- lka/professional-doctoral-study-programme-in-arts… (doctoral) «…Audiovisual Arts, Theatre and Contemporary Dance» → **213** (вариант: 214)
- lu/philosophy-master (master) «Philosophy» → **226** (вариант: 225)
- malnavas-koledza/28562-en, malnavas-koledza/28562-lv (college) «Viedais tūrisms kā uzņēmējdarbība lauku teritorijās» → **812** (вариант: 811)
- psmk/642 (college) «Biomedicīnas laborants» → **421** (вариант: 420)
- riseba/niid-24939 (master) «Lielo datu analītika» → **481** (варианты: 483, 484)
- rmenk/28166-en, rmenk/28166-lv (college) «Tūrisma pakalpojumu organizēšana» → **812** (вариант: 811)
- rnu/business-administration-in-tourism-bachelor (bachelor) → **812** (вариант: 811)
- rsu/medical-engineering-and-physics (bachelor) «Medical Engineering and Physics» → **529** (варианты: 522, 525)
- rtu/gcu-0r000 (bachelor) «Speciālā izglītība» → **141** (вариант: 142)
- rtu/gdi-0r000, rtu/gdi-0r000-liepaja (doctoral), rtu/gmi-0l000-liepaja, rtu/gmi-0l000-rezekne (master) «Izglītības zinātnes» → **142** (вариант: 141)
- rtu/hbm (bachelor) «JAUNO MEDIJU MĀKSLA UN DIZAINS» → **213** (вариант: 214)
- rtu/ikg-0r000 (college) «Grāmatvedība» → **344** (вариант: 343)
- turiba/information-technology (master) «INFORMATION TECHNOLOGY» → **481** (варианты: 483, 484)
- via/17239-en, via/17239-lv (doctoral) «Sociotehnisku sistēmu inženierija» → **481** (варианты: 483, 484)
- via/24932 (master) «Kiberdrošības inženierija» → **481** (вариант: 483)

### в. Случайная выборка уверенно классифицированных — 22 программы

Взяты случайно (зерно 20260922, воспроизводимо) из 851 программ, где либо
кандидат был единственный, либо код подтверждён реальными данными ИЗМ.
Это проверка не логики выбора, а того, что правило вообще не промахнулось
мимо смысла названия.

- eka/management-lv (bachelor) «Management» → 345 (Bizness un pārvaldība) [данными]
- jvlma/arts-doctoral (doctoral) «Arts» → 211 (Māksla) [единственный вариант]
- lma/ceramics-bachelor (bachelor) «Ceramics» → 211 (Māksla) [данными]
- lu/business-process-management-en (bachelor) «Business Process Management» → 345 (Bizness un pārvaldība) [данными]
- lu/communication-science-master (master) «Communication Science» → 321 (Žurnālistika un informācija) [данными]
- lu/economics-master (master) «Economics» → 311 (Sociālās un uzvedības zinātnes) [данными]
- lu/philosophy (bachelor) «Philosophy» → 226 (Humanitārās zinātnes) [данными]
- lu/sociology (bachelor) «Sociology» → 314 (Sociālās un uzvedības zinātnes) [данными]
- malnavas-koledza/27188 (college) «Augkopība» → 621 (Lauksaimniecība un mežsaimniecība) [данными]
- rbk/20853 (college) «Inženiersistēmas» → 582 (Arhitektūra un būvniecība) [данными]
- riseba/audiovisual-arts-and-media-arts-full_time-en (bachelor) «Audiovisual Arts and Media Arts» → 213 (Māksla) [данными]
- rtk/679 (college) «Autotransports» → 525 (Inženierzinātnes) [данными]
- rtu/eco-33000-riga (bachelor) «Elektrotehnoloģiju datorvadība» → 522 (Inženierzinātnes) [данными]
- rtu/gct-0r000-liepaja, rtu/gct-0r000-rezekne (bachelor) «Sākumizglītības skolotājs» → 141 (Izglītība) [единственный вариант]
- rtu/icu-22000-riga (bachelor) «Uzņēmējdarbība un vadīšana» → 345 (Bizness un pārvaldība) [данными]
- rtu/igk-22000 (master) «Visaptverošā kvalitātes vadība» → 345 (Bizness un pārvaldība) [данными]
- rtu/igt-22000 (master) «Līderība un vadība» → 345 (Bizness un pārvaldība) [данными]
- rtu/sce-0r000 (bachelor) «Sociālais darbs un sociālā rehabilitācija» → 762 (Sociālie pakalpojumi) [единственный вариант — после исправления, см. раздел 5]
- tsi/computer-engineering-and-electronics-en (master) «Smart Electronic Systems and Robotics» → 523 (Inženierzinātnes) [данными]
- tsi/double-degree-in-management-of-information-systems-it-project-management (master) «MSc IT Project Management Double Degree with UWE Bristol» → 481 (Datorzinātnes) [данными]
- turiba/business-logistics-management (bachelor) «BUSINESS LOGISTICS MANAGEMENT» → 345 (Bizness un pārvaldība) [данными]

## 4. Не разметились вовсе (8 программ) — остаются в обычной очереди по одной

Ни одно правило не подошло, `programme_field` строка для них не создаётся
(«автоматика ничего не додумывает»); бакалавриат подтверждения по правилу
их не касается вообще.

- **lma/post-master** (master), name_en = «POST» — это не название, а обрезанные данные сборщика (баг каталога, не классификации; нужно проверить страницу LMA и поправить сбор, отдельная задача).
- **rsu/niid-28314** (master) «Digitālā transformācija veselības nozarē» — на стыке ИТ и здоровья, не берусь угадать код.
- **lka/culture-and-arts-studies** (bachelor) «Culture and Arts Studies» — возможно 211 или 227, нет уверенного правила.
- **lka/intercultural-relations** (bachelor) «Intercultural Relations» — возможно 227 или 314.
- **lka/academic-doctoral-study-programme-arts** (doctoral) «Academic doctoral study programme "Arts"» — описательное название не начинается с «Art», общее правило по «Arts» его не ловит.
- **rtu/gmd-0l000-rezekne, rtu/gmd-0l000-liepaja** (master) «Digitālās izglītības tehnoloģijas» — на стыке образования (142) и ИТ (481/483).
- **lu/spatial-planning-master** (master) «Spatial Planning» — в классификаторе ИЗМ нет очевидного кода «пространственного планирования» отдельно от архитектуры/строительства (581/582).

## 5. Найденная и исправленная ошибка правил

При составлении выборки «в» (раздел 3) — `rtu/sce-0r000` «Sociālais darbs un
sociālā rehabilitācija» — обнаружилось, что правило `rehabilitācij` (→ 726,
медицинская реабилитация) срабатывало РАНЬШЕ правила `sociālais
darbs`/`sociālā rehabilit` (→ 762, социальная работа), потому что стояло
выше в списке и «rehabilitācij» — подстрока «rehabilitācija». Затронуло
3 программы: `rtu/sce-0r000`, `dmk/29` и `psmk/639` (все три — «Sociālā
rehabilitācija»/«Sociālais darbs un sociālā rehabilitācija»). Добавлено
отдельное правило `sociālā(?:is)? rehabilit` → 762 раньше общего правила
о реабилитации (`pipeline/src/programme_fields.py`, коммит с этим файлом).
После исправления 2 из 3 программ независимо подтвердились данными ИЗМ
(762 у RTU и DMK на самом деле встречается в статистике для этих
вузов/уровней) — это не просто моя лингвистическая догадка, а совпадение
с реальной статистикой.

Заодно поймана и вторая, более мелкая: `^art\b` не ловил множественное
число «Arts» (между «art» и «s» нет границы слова) — из-за этого
докторская программа JVLMA, буквально названная «Arts», оставалась
неразмеченной. Исправлено на `^arts?\b`; `lka/academic-doctoral-study-programme-arts`
(раздел 4) всё равно не ловится — его название длиннее одного слова.

## 6. Что делать, прочитав это

1. Просмотрите раздел 2 (правила) — согласны ли с логикой в целом.
2. Просмотрите хотя бы группу «а» из раздела 3 (13 строк) — для каждой
   решите: код выбран верно / нужен другой / не уверены (тогда программа
   исключается из пакетного подтверждения и остаётся в обычной очереди).
3. Если что-то нужно исключить — назовите мне (uni/slug), впишу в
   `EXCLUDE` в `pipeline/src/confirm_programme_fields_by_rule.py` перед
   запуском.
4. Если правило само неверно (не только конкретная программа) — тоже
   скажите, поправлю `programme_fields.py` и пересоберу этот отчёт.
5. Когда готовы — я (или вы через Studio) запускаю
   `python src/confirm_programme_fields_by_rule.py --apply`: подтвердит
   разом 892 минус исключённые, `verification_method='rule'`.
   `--apply` без запуска ничего не делает.

Направление — не факт из перечня правила 6 CLAUDE.md, поэтому это
подтверждение разовое пакетное, а не построчное через Studio; тем не менее
это ваше решение, не моё — скрипт я не запускаю сам, пока вы не скажете «go».
