"""Разовая загрузка конкурсных формул — не источник каталога (не входит
в SOURCES, не upsert-ит university/programme), а отдельный шаг: находит
уже существующие в базе программы по (university_slug, programme_slug)
и кладёт для них formula/formula_term.

ВАЖНО при правке коэффициентов здесь: src/lib/formula-regression.test.ts
держит свою (намеренно отдельную от этого файла — TS не читает Python)
копию каждого различающегося набора коэффициентов из всех формул ниже.
Поменяли число тут — поменяйте и там, иначе тест продолжит проверять
старое значение и не заметит расхождение с тем, что реально ушло в базу.

=== Ventspils Augstskola — 8 из 13 программ каталога ===

Источник — единственный принятый правилом 6 CLAUDE.md: утверждённый
Сенатом ВеА PDF правил приёма, не страница сайта (venta.lv/program/...
даёт ту же формулу текстом, но правило явно требует PDF):

  "Uzņemšanas noteikumi un imatrikulācijas kārtība Ventspils Augstskolā
  2026./2027. akadēmiskajā gadā", 1. pielikums
  (VeA Senāta lēmums Nr. 25-39, 27.11.2025., ar grozījumiem Nr. 26-3 un
  Nr. 26-28)
  https://irp.cdn-website.com/f6b5d556/files/uploaded/26-28_Pielikums-2_Uznemsanas_noteikumi_2026-2027_grozits_06-2026.pdf

Из 13 программ Вентспилса в каталоге сюда попали 8 (все не магистерские) —
те, где формула строится из уже поддерживаемых formula_term.kind
('ce' / 'ce_average' / 'entrance_exam') без исключений:

- Не включены все магистерские и докторская программы — у них
  конкурс идёт по VSA (взвешенная средняя оценка диплома), это другая
  модель начисления, не сумма процентов ЦЭ; переиспользовать
  kind='certificate' для неё было бы натяжкой, а не честным
  прочтением документа.
- "Elektronikas inženierija" (bachelor) сначала была пропущена: в
  таблице PDF сумма коэффициентов равна 1,1 (0,6+0,2+0,1+0,1+0,1) из-за
  условного слагаемого "P4 – CE fizikā (ja ir kārtots)". После появления
  флага formula_term.optional (сентябрь 2026) добавлена с физикой как
  необязательным слагаемым — буквальное прочтение печатной формулы; что
  документ прямо этого не говорит, отмечено в комментарии у самой формулы
  ниже. Магистерские программы Ventspils (VSA — средняя оценка диплома
  бакалавра) не берутся: они не для выпускников школ.

=== Latvijas Universitāte — 15 бакалаврских программ Ekonomikas un
sociālo zinātņu fakultāte (полный список факультетов ЛУ в каталоге —
6, здесь взят только один; остальные пять — Eksakto zinātņu un
tehnoloģiju, Humanitāro zinātņu, Izglītības zinātņu un psiholoģijas,
Juridiskā, Medicīnas un dzīvības zinātņu — заметно сложнее по составу
формул и оставлены на будущий заход) ===

Источник — утверждённый документ ЛУ, не страница сайта:

  "Uzņemšanas prasības un kritēriji pamatstudiju programmās
  2025./2026. akadēmiskajā gadā", 2. sadaļa (LU rīkojums Nr. 1-4/588,
  28.11.2024., konsolidēts ar grozījumiem līdz 04.07.2025.)
  https://www.lu.lv/fileadmin/user_upload/lu_portal/gribustudet/pamatstudijas/1-4-588-2024_1._piel_kons_04.07.25.pdf

Важная оговорка: на 2026-09-13 аналогичный документ за 2026./2027.
akadēmisko gadu на сайте ЛУ уже опубликован
(lu.lv/gribustudet/normativie-dokumenti/uznemsanas-prasibas-un-kriteriji-pamatstudijas-2026/2027-akademiskaja-gada/),
но содержит пока только общий раздел ("Vispārīgie nosacījumi") — сама
таблица коэффициентов по программам (раздел 2, тот, что нужен здесь)
туда ещё не добавлена. Использован последний год, где эта таблица
существует целиком — 2025./2026. Проверить и обновить valid_from на
новый учебный год, когда ЛУ опубликует раздел 2 за 2026./2027.

15 программ отобраны по тому же принципу "лучше меньше, но точно":
формула строится только из терминов, которые уже честно
представляются нашей моделью:

- Пропущены обе "Industriālā inženierija un vadība" (LV/EN): формула
  1. варианта смешивает проценты ЦЭ с отдельной годовой оценкой по
  физике внутри одной и той же формулы — у нас kind='certificate'
  это один общий вход (весь аттестат), а не оценка по конкретному
  предмету вдобавок к ЦЭ.
- "CE sociālajās zinātnēs procentos (...; ja nav CE sociālajās
  zinātnēs, tad 0)" — это НЕ альтернатива "предмет A или B" (как у
  RTU физика/химия), а одно слагаемое по одному предмету с честным
  "нет экзамена — 0 баллов", что calculateScore() уже делает сама по
  себе для любого пропущенного ЦЭ (formula.ts). Добавлен только
  недостающий ключ предмета "socialstudies" в словари локалей —
  никакого расширения схемы/калькулятора для этого не потребовалось.
- "CE angļu valodā vai CE franču valodā, vai CE vācu valodā" — как и
  раньше (пример "Ekonomika" из docs/PLAN.md), моделируется как
  subject='english': выбор из трёх языков — не то же самое, что
  RTU-шная развилка "физика или химия" (там могло быть оба сразу и
  непонятно, суммировать или брать один), здесь один слот на один
  язык, и подавляющее большинство сдаёт именно английский.

По ходу этой партии вскрылся реальный баг в CalculatorForm.tsx: поля
'certificate' и 'entrance_exam' никогда не показывались пользователю
и не передавались в calculateScore() (extras всегда был {}) — из-за
этого уже закоммиченная формула Вентспилса "Jaunuzņēmumu vadība"
(60% веса на entrance_exam) тихо считалась в 0. Исправлено в том же
коммите, что и эта партия формул.

=== RTU — 2 программы Rīgas Biznesa skola (RBS) ===

Источник — та же страница, что и в предыдущем RTU-заходе (она
дословно воспроизводит решение Сената с номером и датой, не сторонняя
интерпретация — так уже решили при загрузке каталога):

  "Uzņemšanas noteikumi īsā cikla un pirmā cikla studiju programmās
  2026./2027. akadēmiskajā gadā", 31.7. punkts
  (RTU Senāta 24.11.2025. sēdes protokollēmums Nr. 697)
  https://www.rtu.lv/lv/studijas/uznemsana/uznemsanas-noteikumi/uznemsanas-noteikumi-pamatstudijas

Из всего каталога РТУ (без Liepāja — её отдельно и точнее покрывает
rtu_liepaja.py) это единственные 2 бакалаврские программы без
слагаемого "fizika un/vai ķīmija": почти весь остальной каталог живёт
по общему правилу п.31.1, где это слагаемое есть у всех ~20
направлений подряд, включая формально гуманитарную "Tehniskā
tulkošana un tekstveide" (п.31.6). Программы Rēzekne (RTU RA) сюда не
попали по другой причине — там принципиально другая модель (сумма
ВСЕХ сданных ЦЭ без разных весов по предметам + оценки аттестата,
делённые на 1000), не сумма поимённо взвешенных предметов, как у нас.

У RBS-формулы — три разных вступительных испытания с одинаковым весом
0,25 каждое (тест английского, собеседование, тест математики), а не
один общий балл. Раньше наша схема не могла их различить — CalculatorForm.tsx
показывал одно поле "Iestājpārbaudījums" на формулу. Решение —
переиспользовать существующее поле formula_term.subject и для
entrance_exam/certificate тоже (не только для 'ce'): там это не
предмет ЦЭ, а метка конкретного испытания ('english_test',
'interview', 'math_test'), различаемая в калькуляторе по extraKey()
(formula.ts) вместо одного жёстко зашитого имени. Миграция схемы не
потребовалась — subject уже был текстовым полем без ограничений.

verified_at везде NULL — этот скрипт заполняет только источник и
данные, подтверждает формулу исключительно человек через Supabase
Studio (правило 6 CLAUDE.md).
"""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from db import get_service_client

REPO_ROOT = Path(__file__).resolve().parents[2]


def source_protocol(number: str, doc_date: date, copy_path: str, fetched_on: date) -> dict:
    """Протокол источника (план работ, неделя 3): номер и дата документа,
    копия документа в репозитории и её хэш. Хэш считается ЗДЕСЬ, из файла,
    а не вписывается руками: подмена или порча копии станет видна при
    следующем запуске. Без файла — ошибка: формулу без копии документа
    в базу не кладём, подтвердить её всё равно нельзя (ограничение
    formula_verified_needs_protocol в БД)."""
    path = REPO_ROOT / copy_path
    if not path.exists():
        raise FileNotFoundError(f"нет копии документа {copy_path} — скачайте её в docs/source-documents/")
    return {
        "source_doc_number": number,
        "source_doc_date": doc_date.isoformat(),
        "source_copy_path": copy_path,
        "source_copy_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_copy_fetched_on": fetched_on.isoformat(),
    }


VENTA_SOURCE_URL = (
    "https://irp.cdn-website.com/f6b5d556/files/uploaded/"
    "26-28_Pielikums-2_Uznemsanas_noteikumi_2026-2027_grozits_06-2026.pdf"
)
VENTA_SOURCE_DOC = (
    "Uzņemšanas noteikumi un imatrikulācijas kārtība Ventspils Augstskolā "
    "2026./2027. akadēmiskajā gadā, 1. pielikums "
    "(VeA Senāta lēmums Nr. 25-39, 27.11.2025.)"
)
VENTA_VALID_FROM = date(2025, 11, 27)
# ВАЖНО: копия — версия документа с ДВУМЯ поправками после утверждения
# (Senāta lēmums Nr. 26-3 от 28.01.2026 и Nr. 26-28 от 18.06.2026), а
# формулы посеяны 2026-09-13 с версии, где о поправках не помнили. Совпадают
# ли коэффициенты с текущей версией, должен проверить человек при
# подтверждении. Дата документа — дата последней поправки.
VENTA_PROTOCOL = source_protocol(
    number="25-39 (grozījumi: 26-3, 26-28)",
    doc_date=date(2026, 6, 18),
    copy_path="docs/source-documents/venta/uznemsanas-noteikumi-2026-27-pielikums-2-grozits-06-2026.pdf",
    fetched_on=date(2026, 9, 20),
)

LU_SOURCE_URL = (
    "https://www.lu.lv/fileadmin/user_upload/lu_portal/gribustudet/pamatstudijas/"
    "1-4-588-2024_1._piel_kons_04.07.25.pdf"
)
LU_SOURCE_DOC = (
    "Uzņemšanas prasības un kritēriji pamatstudiju programmās 2025./2026. "
    "akadēmiskajā gadā, 2. sadaļa (LU rīkojums Nr. 1-4/588, 28.11.2024., "
    "konsolidēts ar grozījumiem līdz 04.07.2025.)"
)
LU_VALID_FROM = date(2024, 11, 28)
# УСТАРЕЛО: это правила 2025/2026. На сайте ЛУ уже лежат правила 2026/2027
# (agrā uzņemšana с 02.03.2026, vasaras — с 09.07.2026; копия страницы в
# docs/source-documents/lu/uznemsanas-prasibas-un-kriteriji-2026-27.html),
# а правила на 2027/2028 вузы обязаны опубликовать до 30 ноября 2026.
# Подтверждать эти формулы нет смысла: их надо пересеять с документа
# 2027/28 в декабрьском цикле сверки. Дата документа — дата последней
# поправки (rīkojums Nr. 1-4/298 от 04.07.2025).
LU_PROTOCOL = source_protocol(
    number="1-4/588 (grozījumi: 1-4/37, 1-4/146, 1-4/298)",
    doc_date=date(2025, 7, 4),
    copy_path="docs/source-documents/lu/1-4-588-2024-piel-kons-04.07.25-2025-26.pdf",
    fetched_on=date(2026, 9, 20),
)

RTU_SOURCE_URL = (
    "https://www.rtu.lv/lv/studijas/uznemsana/uznemsanas-noteikumi/"
    "uznemsanas-noteikumi-pamatstudijas"
)
RTU_SOURCE_DOC = (
    "Uzņemšanas noteikumi īsā cikla un pirmā cikla studiju programmās "
    "2026./2027. akadēmiskajā gadā, 31.7. punkts "
    "(RTU Senāta 24.11.2025. sēdes protokollēmums Nr. 697)"
)
RTU_VALID_FROM = date(2025, 11, 24)
# У РТУ утверждённого PDF нет: официальный текст правил (Senāta
# protokollēmums Nr. 697) опубликован только страницей сайта — копией
# служит сохранённая страница.
RTU_PROTOCOL = source_protocol(
    number="697",
    doc_date=date(2025, 11, 24),
    copy_path="docs/source-documents/rtu/uznemsanas-noteikumi-pamatstudijas-2026-27.html",
    fetched_on=date(2026, 9, 20),
)

# subject — те же ключи, что в dict.survey.exams.subjects (lv.json/en.json),
# иначе калькулятор покажет сырой ключ вместо перевода (CalculatorForm.tsx).
FORMULA_SEEDS = [
    {
        "programme_slug": "programmesanas-specialists",
        "terms": [
            ("ce", "mathematics", 0.6),
            ("ce", "english", 0.2),
            ("ce", "latvian", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "datorzinatnes-bakalaurs",
        "terms": [
            ("ce", "mathematics", 0.6),
            ("ce", "english", 0.2),
            ("ce", "latvian", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "biznesa-vadiba-bakalaurs",
        "terms": [
            ("ce", "mathematics", 0.6),
            ("ce", "english", 0.2),
            ("ce", "latvian", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "jaunuznemumu-vadiba",
        "terms": [
            ("ce", "mathematics", 0.15),
            ("ce", "english", 0.15),
            ("entrance_exam", None, 0.6),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "vadibzinatne-lv-distance",
        "terms": [
            ("ce", "mathematics", 0.4),
            ("ce", "english", 0.4),
            ("ce", "latvian", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "vadibzinatne-en-full_time",
        "terms": [
            ("ce", "mathematics", 0.4),
            ("ce", "english", 0.4),
            ("ce", "latvian", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "valodas-sazina-un-kulturvide",
        "terms": [
            ("ce", "english", 0.4),
            ("ce", "latvian", 0.4),
            ("ce", "mathematics", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        # Раньше пропущена: "P4 – CE fizikā (ja ir kārtots)" даёт сумму 1,1.
        # Теперь есть флаг optional: без физики (P1 0,6 + P2 0,2 + P3 0,1 +
        # среднее 0,1) ровно 1,0, физика добавляется сверху — так же, как у
        # ЛУ ("ja nav CE …, tad 0"). Документ этого прямо не говорит, и его
        # же фраза "результат — по шкале 100 баллов" при физике даёт до 110:
        # человек, подтверждающий формулу, решает, верно ли такое прочтение
        # (вопрос приёмной комиссии Ventspils Augstskola).
        "programme_slug": "elektronika-bakalaurs",
        "terms": [
            ("ce", "mathematics", 0.6),
            ("ce", "english", 0.2),
            ("ce", "latvian", 0.1),
            ("ce", "physics", 0.1, True),
            ("ce_average", None, 0.1),
        ],
        "excerpt": (
            "Pirmā cikla profesionālās augstākās izglītības (bakalaura) studiju programma “Elektronikas inženierija” "
            "… Vidējā izglītība; P1 - CE matemātikā; P2 - CE vai STIP angļu valodā; P3 – CE latviešu valodā; "
            "P4 – CE fizikā (ja ir kārtots); Konkursa rezultāta aprēķināšana: CE l.k*P1*0,6 + CE l.k *P2*0,2 + "
            "CE l.k*P3*0,1 + CE l.k *P4*0,1 + 0,1*visu CE kopvērtējumu vidējā vērtība. "
            "(Текст строки таблицы 1. pielikums, извлечён из PDF; таблица в PDF разбита на колонки.)"
        ),
    },
]

LU_FORMULA_SEEDS = [
    {
        "programme_slug": "business-administration-lv",
        "terms": [
            ("ce", "latvian", 1.5),
            ("ce", "english", 1.0),
            ("ce", "mathematics", 6.5),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "business-administration-en",
        "terms": [
            ("ce", "latvian", 1.0),
            ("ce", "english", 3.5),
            ("ce", "mathematics", 4.5),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "e-business-management",
        "terms": [
            ("ce", "latvian", 1.5),
            ("ce", "english", 1.0),
            ("ce", "mathematics", 6.5),
            ("ce_average", None, 1.0),
        ],
    },
    {
        # тот самый пример из docs/PLAN.md и formula.test.ts
        "programme_slug": "economics",
        "terms": [
            ("ce", "latvian", 1.5),
            ("ce", "english", 1.0),
            ("ce", "mathematics", 6.5),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "financial-management",
        "terms": [
            ("ce", "latvian", 1.5),
            ("ce", "english", 1.0),
            ("ce", "mathematics", 6.5),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "accounting-analysis-and-audit",
        "terms": [
            ("ce", "latvian", 1.5),
            ("ce", "english", 1.0),
            ("ce", "mathematics", 6.5),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "information-management",
        "terms": [
            ("ce", "latvian", 3.5),
            ("ce", "english", 3.5),
            ("ce", "mathematics", 2.0),
            ("ce_average", None, 1.0),
            ("ce", "socialstudies", 1.0),
        ],
    },
    {
        "programme_slug": "communication-science",
        "terms": [
            ("ce", "latvian", 3.5),
            ("ce", "english", 3.5),
            ("ce", "mathematics", 2.0),
            ("ce_average", None, 1.0),
            ("ce", "socialstudies", 1.0),
        ],
    },
    {
        "programme_slug": "cultural-and-social-anthropology",
        "terms": [
            ("ce", "latvian", 3.5),
            ("ce", "english", 3.5),
            ("ce", "mathematics", 2.0),
            ("ce_average", None, 1.0),
            ("ce", "socialstudies", 1.0),
        ],
    },
    {
        "programme_slug": "cultural-and-social-anthropology-en",
        "terms": [
            ("ce", "latvian", 1.0),
            ("ce", "english", 6.0),
            ("ce", "mathematics", 2.0),
            ("ce_average", None, 1.0),
            ("ce", "socialstudies", 1.0),
        ],
    },
    {
        "programme_slug": "political-science",
        "terms": [
            ("ce", "latvian", 3.5),
            ("ce", "english", 3.5),
            ("ce", "mathematics", 2.0),
            ("ce_average", None, 1.0),
            ("ce", "socialstudies", 1.0),
        ],
    },
    {
        "programme_slug": "social-work-in-riga-and-ul-branches",
        "terms": [
            ("ce", "latvian", 3.5),
            ("ce", "english", 3.5),
            ("ce", "mathematics", 2.0),
            ("ce_average", None, 1.0),
            ("ce", "socialstudies", 1.0),
        ],
    },
    {
        "programme_slug": "sociology",
        "terms": [
            ("ce", "latvian", 3.5),
            ("ce", "english", 3.5),
            ("ce", "mathematics", 2.0),
            ("ce_average", None, 1.0),
            ("ce", "socialstudies", 1.0),
        ],
    },
    {
        "programme_slug": "international-economics-and-commercial-diplomacy-lv",
        "terms": [
            ("ce", "latvian", 2.5),
            ("ce", "english", 2.5),
            ("ce", "mathematics", 4.0),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "international-economics-and-commercial-diplomacy-en",
        "terms": [
            ("ce", "latvian", 1.0),
            ("ce", "english", 3.5),
            ("ce", "mathematics", 4.5),
            ("ce_average", None, 1.0),
        ],
    },
]

# Вторая партия ЛУ — 11 программ ещё из трёх факультетов (Humanitāro
# zinātņu, Izglītības zinātņu un psiholoģijas, Medicīnas un dzīvības
# zinātņu). Тот же источник и то же ограничение valid_from/2025-2026,
# см. докстринг выше LU_SOURCE_DOC.
#
# По пути выяснилось: факультета Eksakto zinātņu un tehnoloģiju
# (Datorzinātnes, Matemātika, Fizika, Optometrija и т.д.) в каталоге
# ЛУ нет вообще ни одной строки — видимо, баг обхода ссылок в lu.py на
# этой конкретной странице факультета, не текущая (формульная) задача.
# Формулы для него добавить нечему, пока каталог не дополнят.
#
# Из оставшихся факультетов включены только программы с уже
# представимой моделью:
# - Juridiskā fakultāte — не дала ни одной: все три программы
#   (Pirmstiesas izmeklēšana × 2, Tiesību zinātne) используют цепочку
#   "gada atzīme vēsturē VAI sociālajās zinībās un vēsturē VAI
#   vēsturē un sociālajās zinātnēs VAI sociālajās zinātnēs" — это уже
#   не "нет экзамена — 0" (безопасный паттерн из первой партии), а
#   настоящая развилка "источник A или B или C", тот же класс
#   проблемы, что и RTU-шная физика/химия.
# - Humanitāro zinātņu: apakšprogrammas филологии (Franču, Krievu,
#   Vācu, Klasiskā, Somugru) НЕ имеют собственных строк в каталоге —
#   lu.py нашёл их как agregētas карточки "philology-lv"/"philology-en"
#   (сайт объединяет несколько языковых модулей на одной странице
#   программы), а у модулей разные формулы (Krievu/Vācu вдобавок несут
#   отдельную оценку по языку из аттестата — тот же грейд-в-ЦЭ-формуле
#   паттерн, что и Industriālā inženierija из первой партии). Раз
#   нельзя однозначно сказать, какая из формул относится к
#   агрегированной карточке — не трогаем "philology-lv"/"philology-en"
#   вовсе. Взяты только те apakšprogrammas, что оказались в каталоге
#   отдельной строкой: Anglistikas..., Filozofija, Latvistika, Vēsture
#   un arheoloģija, и "Āzijas studijas" (латышский вариант — совпадает
#   по языку с каталожной записью "asian-and-intercultural-studies";
#   англоязычный вариант той же apakšprogrammas, "Austrumu-Rietumu
#   starpkultūru studijas", своей строки в каталоге не имеет).
# - Izglītības zinātņu un psiholoģijas: 8 apakšprogrammas "Skolotājs"
#   и "Sporta treneris" тоже не попали — либо агрегированы в одну
#   каталожную карточку ("professional-bachelor-study-programme-
#   teacher"), либо вовсе отсутствуют в каталоге по отдельности.
#   "Pirmsskolas skolotājs" по той же причине пропущен — своей строки
#   в каталоге нет.
# - Medicīnas: "Ārstniecība", "Zobārstniecība", "Biotehnoloģija un
#   bioinženierija" несут "CE fizikā VAI ķīmijā VAI bioloģijā" —
#   тот же класс развилки, что и Juridiskā выше. "Farmācija",
#   "Māszinības" несут оценку из аттестата с развилкой ("ķīmijā VAI
#   dabaszinībās") — тоже исключены. "Ķīmija" — два варианта формулы
#   на выбор абитуриента, как и Fizika из Eksakto (была бы исключена
#   в любом случае).
#
# entrance_exam с меткой 'art_test' (Māksla) и обычный именованный
# entrance_exam (Sākumizglītības skolotājs, 'interview') — расширение
# extraKey() из RTU-партии уже покрывает оба случая без доработок.
LU_FACULTY2_FORMULA_SEEDS = [
    {
        "programme_slug": "english-european-languages-and-business-studies",
        "terms": [
            ("ce", "latvian", 2.0),
            ("ce", "english", 4.5),
            ("ce", "mathematics", 2.5),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "philosophy",
        "terms": [
            ("ce", "latvian", 3.0),
            ("ce", "english", 5.0),
            ("ce", "mathematics", 1.0),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "latvian-studies",
        "terms": [
            ("ce", "latvian", 6.0),
            ("ce", "english", 2.0),
            ("ce", "mathematics", 1.0),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "history-and-archeology",
        "terms": [
            ("ce", "latvian", 3.5),
            ("ce", "english", 3.5),
            ("ce", "mathematics", 2.0),
            ("ce_average", None, 1.0),
            ("ce", "history", 1.0),
        ],
    },
    {
        # apakšprogramma "Āzijas studijas" (studiju valoda: latviešu) —
        # совпадает языком с каталожной записью; "Austrumu-Rietumu
        # starpkultūru studijas" (angļu) своей строки в каталоге нет.
        "programme_slug": "asian-and-intercultural-studies",
        "terms": [
            ("ce", "latvian", 2.0),
            ("ce", "english", 6.0),
            ("ce", "mathematics", 1.0),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "art-1",
        "terms": [
            ("ce", "latvian", 2.5),
            ("ce", "english", 1.5),
            ("ce", "mathematics", 1.0),
            ("ce_average", None, 1.0),
            ("entrance_exam", "art_test", 0.4),
        ],
    },
    {
        "programme_slug": "psychology-1",
        "terms": [
            ("ce", "latvian", 2.5),
            ("ce", "english", 4.0),
            ("ce", "mathematics", 2.5),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "primary-education-teacher",
        "terms": [
            ("ce", "latvian", 2.0),
            ("ce", "english", 1.0),
            ("ce", "mathematics", 1.0),
            ("ce_average", None, 1.0),
            ("entrance_exam", "interview", 5.0),
        ],
    },
    {
        "programme_slug": "sports-technology-and-public-health",
        "terms": [
            ("ce", "latvian", 4.0),
            ("ce", "english", 4.0),
            ("ce", "mathematics", 1.0),
            ("ce_average", None, 1.0),
        ],
    },
    {
        "programme_slug": "occupational-health-and-safety-at-work",
        "terms": [
            ("ce", "latvian", 1.5),
            ("ce", "english", 1.0),
            ("ce", "mathematics", 6.5),
            ("ce_average", None, 1.0),
        ],
    },
    {
        # "Biology and biomedicine" в каталоге — apakšprogramma
        # "Bioloģija" (не "Biomedicīna"): у обеих apakšprogrammas формула
        # 1. varianta общая, различается только на этапе регистрации.
        "programme_slug": "biology",
        "terms": [
            ("ce", "latvian", 1.5),
            ("ce", "english", 1.0),
            ("ce", "mathematics", 2.5),
            ("ce", "biology", 4.0),
            ("ce_average", None, 1.0),
        ],
    },
]

# RBS-формула у обеих программ идентична (п.31.7 — оба названия
# программ перечислены в одном пункте документа).
_RBS_TERMS = [
    ("ce", "mathematics", 0.25),
    ("ce", "latvian", 0.25),
    ("ce", "english", 1.0),
    ("entrance_exam", "english_test", 0.25),
    ("entrance_exam", "interview", 0.25),
    ("entrance_exam", "math_test", 0.25),
    ("ce_average", None, 0.5),
]

RTU_FORMULA_SEEDS = [
    {"programme_slug": "ibx-02c60", "terms": _RBS_TERMS},  # Vadīšana starptautiskos uzņēmumos
    {"programme_slug": "dbt-02c60", "terms": _RBS_TERMS},  # Datorzinātne un organizāciju tehnoloģijas
]


def seed(
    university_slug: str,
    seeds: list[dict],
    source_url: str,
    source_doc: str,
    valid_from: date,
    protocol: dict,
) -> None:
    client = get_service_client()

    university = (
        client.table("university").select("id").eq("slug", university_slug).single().execute()
    )
    university_id = university.data["id"]

    for entry in seeds:
        programme = (
            client.table("programme")
            .select("id")
            .eq("university_id", university_id)
            .eq("slug", entry["programme_slug"])
            .single()
            .execute()
        )
        programme_id = programme.data["id"]

        already = (
            client.table("formula")
            .select("verified_at")
            .eq("programme_id", programme_id)
            .eq("variant", "ce")
            .eq("valid_from", valid_from.isoformat())
            .execute()
            .data
        )
        if already and already[0]["verified_at"]:
            # человек уже подтвердил: перезапись молча подменила бы числа
            print(f"{entry['programme_slug']}: уже подтверждена — не трогаю")
            continue

        formula_row = {
            "programme_id": programme_id,
            "variant": "ce",
            "valid_from": valid_from.isoformat(),
            "source_url": source_url,
            "source_doc": source_doc,
            **({"source_excerpt": entry["excerpt"]} if "excerpt" in entry else {}),
            **protocol,
        }
        formula = (
            client.table("formula")
            .upsert(formula_row, on_conflict="programme_id,variant,valid_from")
            .execute()
        )
        formula_id = formula.data[0]["id"]

        # formula_term не имеет собственного естественного ключа — проще
        # снести и вставить заново, чем сверять построчно при повторном
        # запуске.
        client.table("formula_term").delete().eq("formula_id", formula_id).execute()
        # слагаемое — (kind, subject, coefficient) или с четвёртым элементом
        # True для необязательного ("ja nav …, tad 0")
        term_rows = [
            {
                "formula_id": formula_id,
                "kind": term[0],
                "subject": term[1],
                "coefficient": term[2],
                "optional": len(term) > 3 and bool(term[3]),
            }
            for term in entry["terms"]
        ]
        client.table("formula_term").insert(term_rows).execute()

        print(f"{entry['programme_slug']}: {len(term_rows)} terms")


if __name__ == "__main__":
    load_dotenv()
    seed("venta", FORMULA_SEEDS, VENTA_SOURCE_URL, VENTA_SOURCE_DOC, VENTA_VALID_FROM, VENTA_PROTOCOL)
    # ЛУ здесь больше не сеется: формулы 2025/26 (LU_FORMULA_SEEDS и
    # LU_FACULTY2_FORMULA_SEEDS выше — историческая справка, 22 из них
    # совпали с документом 2026/27) закрыты, а действующие берёт из
    # документа 2026/27 formulas_lu.py. Повторный посев вернул бы старые
    # коэффициенты как действующие.
    seed("rtu", RTU_FORMULA_SEEDS, RTU_SOURCE_URL, RTU_SOURCE_DOC, RTU_VALID_FROM, RTU_PROTOCOL)
