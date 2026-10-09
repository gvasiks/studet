"""Литва: цифры прошлого приёма по программе (lt_admission_stat).

Источник — открытый набор LAMA BPO на data.gov.lt (набор 2914), две таблицы:

- Programa (около 1 МБ): программа набора -> год, государственный код,
  самоуправление;
- Prasymas (около 76 МБ): строка заявления -> этап приёма, номер
  приоритета, программа, вид места, приглашён ли, подписал ли договор.

В Prasymas лежат обезличенные, но построчные данные о людях. Поэтому файл
читается потоком и НЕ сохраняется на диск; в памяти и в базе остаются
только суммы по программе. Третью таблицу набора, Profilis (сведения о
людях), этот скрипт не трогает и трогать не должен.

Считается только основной приём (pagrindinis priėmimas) последнего года,
который есть в наборе. С каталогом суммы сходятся по государственному коду
программы (lt_admission_unit.state_code, его пишет lt_load_formulas.py) и
городу. В наборе программа одна на все формы и языки обучения в городе —
строки каталога, которые различаются только формой или языком, получают
одни и те же числа, и на карточке об этом сказано.

Таблица — миграция 20261008120000_lt_admission_stat.sql.

Запуск:
  python src/lt_load_admission_stats.py --selftest
  python src/lt_load_admission_stats.py            # скачать, посчитать, показать сводку
  python src/lt_load_admission_stats.py --apply
"""

from __future__ import annotations

import csv
import io
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone

DATASET_URL = "https://data.gov.lt/datasets/2914/"
_RESOURCE = "https://data.gov.lt/datasets/2914/versions/729/dynamic-resource/{table}/csv/download/"
PROGRAMA_URL = _RESOURCE.format(table="Programa")
PRASYMAS_URL = _RESOURCE.format(table="Prasymas")

MAIN_STAGE = "Pagrindinis priėmimas"

# Вид места в наборе -> значение lt_admission_stat.funding.
FUNDING = {"VF": "state", "ST": "stipend", "VNF": "paid"}

# Самоуправление в наборе -> город каталога (programme.city).
CITY_BY_MUNICIPALITY = {
    "Vilniaus miesto savivaldybė": "vilnius",
    "Kauno miesto savivaldybė": "kaunas",
    "Klaipėdos miesto savivaldybė": "klaipeda",
    "Šiaulių miesto savivaldybė": "siauliai",
    "Panevėžio miesto savivaldybė": "panevezys",
    "Utenos rajono savivaldybė": "utena",
    "Alytaus miesto savivaldybė": "alytus",
    "Telšių rajono savivaldybė": "telsiai",
    "Marijampolės savivaldybė": "marijampole",
    "Tauragės rajono savivaldybė": "taurage",
}

# Ключ суммы: (государственный код, город каталога, вид места).
Key = tuple[str, str, str]


def latest_year(programa: Iterable[dict[str, str]]) -> int:
    return max(int(row["programos_metai"][:4]) for row in programa)


def programmes_of_year(programa: Iterable[dict[str, str]], year: int) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """Программа набора -> (государственный код, город каталога), только за
    нужный год. Второе значение — самоуправления, которых нет в таблице
    городов: их программы пропускаются, а не приписываются наугад."""
    result: dict[str, tuple[str, str]] = {}
    unknown: set[str] = set()
    for row in programa:
        if int(row["programos_metai"][:4]) != year:
            continue
        city = CITY_BY_MUNICIPALITY.get(row["savivaldybe"])
        if city is None:
            unknown.add(row["savivaldybe"])
            continue
        result[row["programos_id"]] = (row["programos_valst_kodas"], city)
    return result, sorted(unknown)


def count_applications(rows: Iterable[dict[str, str]], programmes: dict[str, tuple[str, str]]) -> dict[Key, Counter]:
    """Суммы по строкам заявлений основного приёма. Из строки берутся только
    программа, этап, вид места, номер приоритета и две отметки; идентификаторы
    человека и заявления не читаются."""
    totals: dict[Key, Counter] = {}
    for row in rows:
        if row["priemimo_etapas"] != MAIN_STAGE:
            continue
        programme = programmes.get(row["programos_id"])
        funding = FUNDING.get(row["finansavimas"])
        if programme is None or funding is None:
            continue
        counter = totals.setdefault((programme[0], programme[1], funding), Counter())
        counter["applications"] += 1
        if row["prioriteto_nr"] == "1":
            counter["first_priority"] += 1
        if row["ar_pakviete"] == "True":
            counter["invited"] += 1
        if row["ar_pasirase"] == "True":
            counter["signed"] += 1
    return totals


def stats_for_catalog(
    catalog: dict[str, tuple[set[str], str | None]], totals: dict[Key, Counter]
) -> tuple[list[dict], Counter]:
    """Программа каталога (её государственные коды и город) -> строки таблицы.
    Второе значение — сколько программ осталось без чисел и почему.

    Программа с двумя разными кодами или без кода пропускается: складывать
    числа двух программ реестра под одним названием — значит выдумывать."""
    rows: list[dict] = []
    skipped: Counter = Counter()
    for programme_id, (codes, city) in catalog.items():
        if len(codes) == 0:
            skipped["нет государственного кода"] += 1
            continue
        if len(codes) > 1:
            skipped["несколько государственных кодов"] += 1
            continue
        if city is None:
            skipped["нет города"] += 1
            continue
        code = next(iter(codes))
        found = False
        for funding in FUNDING.values():
            counter = totals.get((code, city, funding))
            if counter is None:
                continue
            found = True
            rows.append(
                {
                    "programme_id": programme_id,
                    "funding": funding,
                    "applications": counter["applications"],
                    "first_priority": counter["first_priority"],
                    "invited": counter["invited"],
                    "signed": counter["signed"],
                }
            )
        if not found:
            skipped["нет в наборе за этот год"] += 1
    return rows, skipped


def _selftest() -> None:
    programa = [
        {"programos_id": "main25", "programos_metai": "2025-01-01", "programos_valst_kodas": "6011GX004", "savivaldybe": "Vilniaus miesto savivaldybė"},
        {"programos_id": "extra25", "programos_metai": "2025-01-01", "programos_valst_kodas": "6011GX004", "savivaldybe": "Vilniaus miesto savivaldybė"},
        {"programos_id": "main24", "programos_metai": "2024-01-01", "programos_valst_kodas": "6011GX004", "savivaldybe": "Vilniaus miesto savivaldybė"},
        {"programos_id": "alytus25", "programos_metai": "2025-01-01", "programos_valst_kodas": "6531GX040", "savivaldybe": "Alytaus miesto savivaldybė"},
        {"programos_id": "nowhere25", "programos_metai": "2025-01-01", "programos_valst_kodas": "6531GX099", "savivaldybe": "Kėdainių rajono savivaldybė"},
    ]
    assert latest_year(programa) == 2025
    programmes, unknown = programmes_of_year(programa, 2025)
    assert programmes == {
        "main25": ("6011GX004", "vilnius"),
        "extra25": ("6011GX004", "vilnius"),
        "alytus25": ("6531GX040", "alytus"),
    }, programmes
    assert unknown == ["Kėdainių rajono savivaldybė"]

    def row(programme: str, stage: str, funding: str, priority: str, invited: bool, signed: bool) -> dict[str, str]:
        return {
            "programos_id": programme, "priemimo_etapas": stage, "finansavimas": funding,
            "prioriteto_nr": priority, "ar_pakviete": str(invited), "ar_pasirase": str(signed),
            "asmens_id": "не читается", "prasymo_id": "не читается",
        }

    applications = [
        row("main25", MAIN_STAGE, "VF", "1", True, True),
        row("main25", MAIN_STAGE, "VF", "1", True, False),
        row("main25", MAIN_STAGE, "VF", "3", False, False),
        row("main25", MAIN_STAGE, "VNF", "2", True, True),
        row("extra25", "Papildomas priėmimas", "VF", "1", True, True),  # дополнительный приём не считается
        row("main24", MAIN_STAGE, "VF", "1", True, True),  # прошлый год не считается
        row("alytus25", MAIN_STAGE, "ST", "1", False, False),
        row("main25", MAIN_STAGE, "??", "1", False, False),  # незнакомый вид места не считается
    ]
    totals = count_applications(applications, programmes)
    assert totals == {
        ("6011GX004", "vilnius", "state"): Counter(applications=3, first_priority=2, invited=2, signed=1),
        ("6011GX004", "vilnius", "paid"): Counter(applications=1, invited=1, signed=1),
        ("6531GX040", "alytus", "stipend"): Counter(applications=1, first_priority=1),
    }, totals

    catalog = {
        "p-full": ({"6011GX004"}, "vilnius"),
        "p-part": ({"6011GX004"}, "vilnius"),  # та же программа, другая форма — те же числа
        "p-kaunas": ({"6011GX004"}, "kaunas"),  # в этом городе набора нет
        "p-two": ({"6011GX004", "6531GX040"}, "vilnius"),
        "p-none": (set(), "vilnius"),
        "p-nocity": ({"6011GX004"}, None),
    }
    rows, skipped = stats_for_catalog(catalog, totals)
    assert [(r["programme_id"], r["funding"], r["applications"], r["first_priority"], r["invited"], r["signed"]) for r in rows] == [
        ("p-full", "state", 3, 2, 2, 1),
        ("p-full", "paid", 1, 0, 1, 1),
        ("p-part", "state", 3, 2, 2, 1),
        ("p-part", "paid", 1, 0, 1, 1),
    ], rows
    assert skipped == Counter(
        {"нет в наборе за этот год": 1, "несколько государственных кодов": 1, "нет государственного кода": 1, "нет города": 1}
    ), skipped
    for r in rows:
        assert set(r) == {"programme_id", "funding", "applications", "first_priority", "invited", "signed"}, "в базу идут только суммы"

    resource = "https://data.gov.lt/datasets/2914/versions/729/dynamic-resource/Programa/csv/download/"
    allowed = robots_from("User-agent: *\nCrawl-delay: 5\nDisallow: /login\nDisallow: /datasets/stats\n")
    assert allowed.can_fetch("StudyPick", resource) and allowed.crawl_delay("StudyPick") == 5
    assert not allowed.can_fetch("StudyPick", "https://data.gov.lt/datasets/stats/x")
    assert robots_from(None).can_fetch("StudyPick", resource), "robots.txt не получен — ограничений нет"
    assert not robots_unreachable_means_stop(404) and not robots_unreachable_means_stop(403), "4xx — ограничений нет"
    assert robots_unreachable_means_stop(500) and robots_unreachable_means_stop(503), "5xx — сайт не обходим"
    assert not robots_from("User-agent: *\nDisallow: /\n").can_fetch("StudyPick", resource), "настоящий запрет остаётся запретом"
    print("selftest: OK")


ROBOTS_URL = "https://data.gov.lt/robots.txt"

REFUSED = (
    "data.gov.lt не отдал данные этому компьютеру (ответ {status} на {url}). Серверу GitHub портал "
    "отвечает ошибкой (2026-10-09: сначала отказ, потом 500 и на robots.txt, и на сам файл); с "
    "компьютера в Риге в тот же день он отвечал нормально. Набор обновляется раз в год — запустите "
    "загрузчик у себя: .venv\\Scripts\\python.exe src\\lt_load_admission_stats.py --apply"
)


def robots_unreachable_means_stop(status: int) -> bool:
    """Что делать, если сам robots.txt не получен. По RFC 9309: ответ 4xx —
    файла нет, ограничений нет; ответ 5xx — сервер недоступен, и обходить
    сайт НЕЛЬЗЯ, пока он не ответит (правила неизвестны, а не отсутствуют)."""
    return status >= 500


def robots_from(body: str | None) -> urllib.robotparser.RobotFileParser:
    """Правила обхода из текста robots.txt. None — файл получить не удалось
    (ответ 4xx): по RFC 9309 это значит «ограничений нет», так же считает и
    polite.py. Стандартный RobotFileParser.read() при 401/403 запрещает
    ВСЁ — из-за этого отказ портала выглядел как запрет в robots.txt."""
    parser = urllib.robotparser.RobotFileParser()
    parser.parse((body or "").splitlines())
    return parser


def _read_robots(agent: str) -> urllib.robotparser.RobotFileParser:
    try:
        request = urllib.request.Request(ROBOTS_URL, headers={"User-Agent": agent})
        return robots_from(urllib.request.urlopen(request, timeout=30).read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as error:
        if robots_unreachable_means_stop(error.code):
            print(REFUSED.format(status=error.code, url=ROBOTS_URL))
            sys.exit(1)
        print(f"robots.txt портала не получен (ответ {error.code}) — считаем, что ограничений нет")
        return robots_from(None)


def _open(url: str, agent: str, robots: urllib.robotparser.RobotFileParser):  # type: ignore[no-untyped-def]
    if not robots.can_fetch(agent, url):
        raise RuntimeError(f"robots.txt запрещает {url}")
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": agent}), timeout=180)
    except urllib.error.HTTPError as error:
        # Любой отказ портала — понятное сообщение вместо простыни ошибки.
        print(REFUSED.format(status=error.code, url=url))
        sys.exit(1)


def _csv_rows(response) -> csv.DictReader:  # type: ignore[no-untyped-def]
    return csv.DictReader(io.TextIOWrapper(response, encoding="utf-8", newline=""))


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    import polite
    from db import get_service_client
    from db_retry import execute
    from lt_load_formulas import ADMISSION_YEAR as CATALOG_YEAR

    load_dotenv()
    agent = polite.user_agent()
    robots = _read_robots(agent)
    # Пауза между запросами к порталу — как просит его robots.txt.
    pause = float(robots.crawl_delay(agent) or 5)

    with _open(PROGRAMA_URL, agent, robots) as response:
        programa = list(_csv_rows(response))
    year = latest_year(programa)
    programmes, unknown = programmes_of_year(programa, year)
    print(f"год набора: {year} | программ набора за этот год: {len(programmes)}")
    if unknown:
        print(f"самоуправления без города в таблице (их программы пропущены): {unknown}")

    time.sleep(pause)
    with _open(PRASYMAS_URL, agent, robots) as response:
        totals = count_applications(_csv_rows(response), programmes)
    print(f"сумм (программа, город, вид места): {len(totals)} | строк заявлений основного приёма: {sum(c['applications'] for c in totals.values())}")

    client = get_service_client()
    catalog: dict[str, tuple[set[str], str | None]] = {}
    for start in range(0, 100000, 1000):
        page = execute(
            client.table("lt_admission_unit")
            .select("programme_id, state_code, programme(city)")
            .eq("admission_year", CATALOG_YEAR)
            .order("id")
            .range(start, start + 999)
        ).data
        for unit in page:
            codes, _ = catalog.setdefault(unit["programme_id"], (set(), (unit["programme"] or {}).get("city")))
            if unit["state_code"]:
                codes.add(unit["state_code"])
        if len(page) < 1000:
            break

    rows, skipped = stats_for_catalog(catalog, totals)
    with_stats = len({row["programme_id"] for row in rows})
    print(f"программ каталога: {len(catalog)} | с числами: {with_stats} | строк таблицы: {len(rows)}")
    for reason, count in skipped.most_common():
        print(f"   без чисел — {reason}: {count}")

    if "--apply" not in args:
        print("\nзаписи не было (добавьте --apply)")
        return
    now = datetime.now(timezone.utc).isoformat()
    payload = [{**row, "admission_year": year, "source_url": DATASET_URL, "extracted_at": now} for row in rows]
    for start in range(0, len(payload), 500):
        execute(client.table("lt_admission_stat").upsert(payload[start:start + 500], on_conflict="programme_id,admission_year,funding"))

    # Строки этого года, которых в новом расчёте нет (программа ушла из
    # каталога или перестала сходиться с набором), — удалить.
    kept = {(row["programme_id"], row["funding"]) for row in rows}
    existing: list[dict] = []
    for start in range(0, 100000, 1000):
        page = execute(
            client.table("lt_admission_stat")
            .select("programme_id, funding")
            .eq("admission_year", year)
            .order("programme_id")
            .order("funding")
            .range(start, start + 999)
        ).data
        existing += page
        if len(page) < 1000:
            break
    stale = [row for row in existing if (row["programme_id"], row["funding"]) not in kept]
    for row in stale:
        execute(
            client.table("lt_admission_stat")
            .delete()
            .eq("admission_year", year)
            .eq("programme_id", row["programme_id"])
            .eq("funding", row["funding"])
        )
    print(f"записано: {len(payload)} | удалено устаревших: {len(stale)}")


if __name__ == "__main__":
    main()
