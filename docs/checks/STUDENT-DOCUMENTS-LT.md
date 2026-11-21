# Списки документов для иностранцев — Литва, источники

Решение владельца 2026-11-19 (`docs/PLAN-FOREIGNERS.md`, Р1): страница `/…/student-documents` и блок
«Documents to prepare» на карточке английской программы есть и у Литвы. Строки показываются **без
подтверждения человеком**, с пометкой «извлечено автоматически» — как остальные литовские факты. Доступ
открывает миграция `20261120120000_foreign_documents_lt_ee.sql` (политика пропускает неподтверждённые строки
только у вузов Литвы и Эстонии; у Латвии — по-прежнему только подтверждённые).

Строки — `pipeline/src/seed_document_requirements.py`, блок «Литва». Выписаны 2026-11-20 со страниц вузов
для английских программ первой ступени (у колледжей — профессиональный бакалавр). У каждой строки дословная
цитата; 2026-11-20 все цитаты найдены на своих страницах скриптом (страница скачивается, текст сверяется без
учёта пробелов и регистра). `robots.txt` каждого сайта проверен на правила для агентов Anthropic.

## Что вошло

| Вуз | Уровень | Источник |
|---|---|---|
| VDU | бакалавр | vdu.lt/en/studies/degree-studies/, …/qualification-recognition/requirements-for-documents/ |
| KU | бакалавр | ku.lt/en/studies-admission/admission/application-procedure/… |
| MRU | бакалавр | mruni.eu/en/admission/ |
| KTU | бакалавр | admissions.ktu.edu/academic-recognition/ |
| VILNIUS TECH | бакалавр | vilniustech.lt/en/international-students/admission-requirements/, …/application-procedure/ |
| ISM | бакалавр | ism.lt/en/admission |
| LCC | бакалавр | lcc.lt/admissions |
| LMTA | бакалавр | old.lmta.lt/…/bachelor-application/ — **приём 2026 года**, старый поддомен: перечитать, когда выйдет страница 2027 |
| VIKO (vk) | колледж | en.viko.lt/for-students/how-to-apply/, …/admission-requirements/ |
| Vilniaus verslo kolegija (vvk) | колледж | kolegija.lt/en/application-steps-for-international-students/ |
| LTVK | колледж | ltvk.lt/en/…/recognition-of-education-…/ и правила приёма 2026 (PDF) |

## Что не вошло и почему

- **VU** — английской страницы приёма нет (адреса дают 404); PDF со списком документов описывает общий приём
  LAMA BPO, а не английские программы.
- **EHU** — страница приёма отвечает 404.
- **ILK** — сайт отдаёт текст только с JavaScript.
- **KSU** — `robots.txt` запрещает обход агентам Anthropic (ClaudeBot, anthropic-ai, Claude-Web).
- **KTU, легализация и справка о несудимости** — названы только на страницах программ `apply.ktu.edu`, а там
  `robots.txt` тоже запрещает обход агентам Anthropic.
- **VILNIUS TECH, колледж** и **интегрированные программы** (KTU, VILNIUS TECH — по одной): в таблице нет
  уровня `integrated`, а страница колледжа не читалась.
- **Суммы** (взнос за заявление, средства) — в примечания не пишутся: это поля правила 6.

Эти вузы можно добавить вручную — строкой в тот же скрипт с цитатой со страницы.

## Расхождения, которые стоит знать

- VILNIUS TECH: срок действия паспорта — «at least two years» на странице подачи и «at least one year from the
  date of first entry» на странице требований; в примечании сказано, что надо уточнить у вуза.
- Сроки приёма на страницах VVK, LTVK и LMTA — 2026 года; списки документов от года к году почти не
  меняются, но к сезону 2027 их стоит перечитать.

## Обновление

Перечитать к запуску Литвы (1 июня 2027): `python src/seed_document_requirements.py` — сухой прогон, затем
`--apply`. Скрипт сверки цитат лежал во временной папке сессии; при повторе — скачать страницу и найти цитату.
