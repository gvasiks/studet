"""Латвия: цифры прошлого приёма с statistika.vupp.lv (vupp_admission_stat).

Портал единой подачи публикует по каждому году итог приёма: строка —
программа × вид × форма × финансирование × город и четыре числа (места,
заявления, с 1-м приоритетом, предварительно прошли конкурс). Баллов и
проходных там нет. Разведка — docs/checks/VUPP-RECON-2026-10-18.md.

Страницы обычные HTML, robots.txt обход не запрещает. Год —
/enrolment/{год}_Vasara (список вузов), вуз — /{год}_Vasara/{номер}.
Заголовок страницы называет срез («2. kārtas apstiprinātie pieteikumi…» —
после второго тура), рядом — дата последнего обновления. Оба сохраняются
и показываются рядом с числами.

Строки пишутся как есть, без сопоставления с каталогом: какая программа
каталога соответствует коду приёма, решают черновики связей
(programme_vupp_link) и подтверждение владельца.

Таблица — миграция 20261018120000_vupp_admission_stat.sql.

Запуск:
  python src/vupp_stats.py --selftest
  python src/vupp_stats.py                    # скачать 2024–2026, показать сводку
  python src/vupp_stats.py --years 2026 --apply
"""

from __future__ import annotations

import re
import sys
import time
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from html.parser import HTMLParser

BASE_URL = "https://statistika.vupp.lv"
DEFAULT_YEARS = (2024, 2025, 2026)
PAUSE_SECONDS = 2.0

# Название вуза на портале -> наш код (university.slug). Banku augstskola
# до 2025 года шла отдельно, теперь это часть ЛУ; в каталоге её нет.
UNIVERSITY_SLUG = {
    "Daugavpils Universitāte": "du",
    "Ekonomikas un kultūras augstskola": "eka",
    "Latvijas Biozinātņu un tehnoloģiju universitāte": "lbtu",
    "Latvijas Universitāte": "lu",
    "Rīgas Tehniskā universitāte": "rtu",
    "Rīgas Ziemeļvalstu augstskola": "rnu",
    "Ventspils Augstskola": "venta",
    "Vidzemes Augstskola": "via",
    "Banku augstskola": None,
    # в 2024 году ещё отдельно; в каталоге её нет
    "Rēzeknes Tehnoloģiju akadēmija": None,
}

# «Biznesa vadība (angļu val.) (207B9), Bakalaura akadēmiskā, Pilna laika
# (dienas), Maksa, Rīga» — название может само содержать скобки и запятые,
# поэтому код берётся последний перед «, вид, форма, финансирование, город».
# Коды бывают короткие и со строчными буквами: «1F» (Banku augstskola),
# «BVzP» (EKA), «22523JapS» (ЛУ, 2024),
# поэтому «(dienas)» в форме обучения тоже похоже на код — после кода
# требуются ровно четыре поля без запятых.
_ROW = re.compile(r"^(?P<name>.+) \((?P<code>[A-Za-z0-9]{2,12})\), (?P<rest>[^,]+, [^,]+, [^,]+, [^,]+)$")
_UNIVERSITY_LINK = re.compile(r'href="/(?P<year>\d{4})_Vasara/(?P<id>\d+)"[^>]*>(?P<name>[^<]+)</a>')
_UPDATED = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")

Key = tuple[int, str, str, str, str, str, str]


class _PageParser(HTMLParser):
    """Собирает из страницы вуза заголовок среза, дату обновления, название
    вуза и строки таблиц с факультетом, к которому они относятся."""

    def __init__(self) -> None:
        super().__init__()
        self.stage = ""
        self.updated = ""
        self.university = ""
        self.rows: list[tuple[str, list[str]]] = []
        self._unit = ""
        self._capture: str | None = None  # что сейчас собираем: stage, university, unit, updated, cell
        self._text: list[str] = []
        self._cells: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = dict(attrs).get("class") or ""
        if tag == "h2":
            self._start("university" if "uni-heading" in classes else ("stage" if not self.stage else None))
        elif tag == "h4":
            self._start("unit")
        elif tag == "sup" and self._capture == "unit":
            # «Kopā: 8403/1264» — сумма факультета, не часть названия
            self._finish()
        elif tag == "bold" and not self.updated:
            self._start("updated")
        elif tag == "tr":
            # строка «kopā» под таблицей факультета — итог, не программа
            self._cells = None if "table-borderless" in classes else []
        elif tag == "td" and self._cells is not None:
            self._start("cell")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("h2", "h4", "bold", "td"):
            self._finish()
        elif tag == "tr" and self._cells is not None:
            # до заголовка вуза стоит сводная таблица по всем вузам — не программы
            if self._cells and self.university:
                self.rows.append((self._unit, self._cells))
            self._cells = None

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._text.append(data)

    def _start(self, what: str | None) -> None:
        self._finish()
        self._capture = what
        self._text = []

    def _finish(self) -> None:
        if self._capture is None:
            return
        text = " ".join("".join(self._text).split())
        if self._capture == "stage":
            self.stage = text
        elif self._capture == "university":
            self.university = text
        elif self._capture == "unit":
            self._unit = text
        elif self._capture == "updated":
            self.updated = text
        elif self._capture == "cell" and self._cells is not None:
            self._cells.append(text)
        self._capture = None
        self._text = []


def _number(text: str) -> int | None:
    """Число из ячейки; пустая ячейка, прочерк или «*» — нет числа, а не ноль."""
    return int(text) if text.isdigit() else None


# «*» вместо числа мест — «neierobežots vietu skaits» (сноска под таблицей)
UNLIMITED = "*"


def portal_date(text: str) -> date | None:
    match = _UPDATED.search(text)
    if match is None:
        return None
    day, month, year = (int(part) for part in match.groups())
    return date(year, month, day)


def university_pages(year_html: str, year: int) -> list[tuple[str, str]]:
    """Список вузов года: (название на портале, адрес страницы)."""
    pages = []
    for match in _UNIVERSITY_LINK.finditer(year_html):
        if int(match["year"]) == year:
            pages.append((match["name"].strip(), f"{BASE_URL}/{year}_Vasara/{match['id']}"))
    return pages


def parse_page(html: str, year: int, source_url: str) -> tuple[list[dict], list[str]]:
    """Строки таблицы для базы. Второе значение — строки, которые не удалось
    разобрать: они не пишутся, а попадают в отчёт (лучше пробел, чем
    угаданная форма обучения)."""
    parser = _PageParser()
    parser.feed(html)
    parser.close()
    if not parser.stage or not parser.university:
        raise ValueError(f"{source_url}: не найден заголовок среза или название вуза — разметка портала изменилась?")
    if parser.university not in UNIVERSITY_SLUG:
        raise ValueError(f"{source_url}: незнакомый вуз «{parser.university}» — добавьте его в UNIVERSITY_SLUG")
    updated = portal_date(parser.updated)
    rows: list[dict] = []
    problems: list[str] = []
    for unit, cells in parser.rows:
        if len(cells) != 5:
            problems.append(f"{len(cells)} ячеек: {cells}")
            continue
        match = _ROW.match(cells[0])
        parts = match["rest"].split(", ") if match else []
        if match is None or len(parts) != 4:
            problems.append(cells[0])
            continue
        kind, mode, funding, city = parts
        rows.append(
            {
                "admission_year": year,
                "university_slug": UNIVERSITY_SLUG[parser.university],
                "portal_university_name": parser.university,
                "unit": unit or None,
                "programme_code": match["code"],
                "programme_name": match["name"],
                "programme_kind": kind,
                "study_mode": mode,
                "funding": funding,
                "city": city,
                "stage": parser.stage,
                "portal_updated_on": updated.isoformat() if updated else None,
                "places": _number(cells[1]),
                "places_unlimited": cells[1] == UNLIMITED,
                "applications": _number(cells[2]),
                "first_priority": _number(cells[3]),
                "passed": _number(cells[4]),
                "source_url": source_url,
            }
        )
    return rows, problems


def row_key(row: dict) -> Key:
    return (
        row["admission_year"], row["portal_university_name"], row["programme_code"],
        row["programme_kind"], row["study_mode"], row["funding"], row["city"],
    )


def duplicate_keys(rows: list[dict]) -> list[Key]:
    """Ключи, которые встречаются дважды: в базе вторая строка затёрла бы
    первую, поэтому такой прогон не записывается."""
    counts = Counter(row_key(row) for row in rows)
    return [key for key, count in counts.items() if count > 1]


_SAMPLE_YEAR = """
<option value="/enrolment/2025_Vasara">2025./2026.</option>
<a href="/2026_Vasara/2">Latvijas Universitāte</a>
<a href="/2026_Vasara/1">Rīgas Tehniskā universitāte</a>
"""

_SAMPLE_PAGE = """
<h1 style="text-align: center">Statistika par pieteikumiem pamatstudiju programmās</h1>
<h2 style="text-align: center">2. kārtas apstiprinātie pieteikumi uzņemšanai pamatstudiju programmās</h2>
<p>Statistika pēdējo reizi atjaunota: <bold>03.08.2026 9:00</bold></p>
<table><tr><td>1</td><td>Latvijas Universitāte</td><td>28161</td><td>6091</td></tr></table>
<h2 style="text-align: center" class="uni-heading">Latvijas Universitāte</h2>
<h4 style="text-align: left">Ekonomikas un sociālo zinātņu fakultāte  <sup class="badge">Kopā: 8403/1264</sup></h4>
<table class="table"><thead><tr><th>Studiju programma</th><th>vietas</th><th>pieteikumi</th>
<th>ar 1.prioritāti</th><th>Provizoriski konkursu izturējuši</th></tr></thead>
<tbody><tr style="text-align: center">
  <td style="text-align: left">Biznesa vadība (207B7), Bakalaura akadēmiskā, Pilna laika (dienas), Budžets, Rīga</td>
  <td style="text-align: right">
        23
  </td>
  <td>831</td><td>174</td><td>23</td></tr>
<tbody><tr>
  <td>Biznesa vadība (angļu val.) (207B9), Bakalaura akadēmiskā, Pilna laika (dienas), Maksa, Rīga</td>
  <td></td><td>114</td><td>19</td><td>-</td></tr>
<tbody><tr>
  <td>Vadības zinības (BVzP), Bakalaura akadēmiskā, Pilna laika (dienas), Maksa, Rīga</td>
  <td> * </td><td>26</td><td>0</td><td>1</td></tr>
<tr class="table-borderless"><td class="footnote"><div><p><sup>* - neierobežots vietu skaits</sup></p> <p>kopā</p></div></td>
  <td>- </td><td>549</td><td>47</td><td>60</td></tr>
</table>
<h4 style="text-align: left">Juridiskā fakultāte <sup class="badge">Kopā: 1/1</sup></h4>
<table><tr><td>Tiesību zinātne (bez koda), Bakalaura akadēmiskā, Rīga</td><td>1</td><td>1</td><td>1</td><td>1</td></tr></table>
<h2>Kontakti</h2>
"""


def _selftest() -> None:
    url = f"{BASE_URL}/2026_Vasara/2"
    assert university_pages(_SAMPLE_YEAR, 2026) == [
        ("Latvijas Universitāte", url),
        ("Rīgas Tehniskā universitāte", f"{BASE_URL}/2026_Vasara/1"),
    ]
    assert university_pages(_SAMPLE_YEAR, 2025) == [], "ссылка на другой год — не вуз этого года"

    rows, problems = parse_page(_SAMPLE_PAGE, 2026, url)
    assert [(r["programme_code"], r["programme_name"], r["funding"], r["places"], r["passed"]) for r in rows] == [
        ("207B7", "Biznesa vadība", "Budžets", 23, 23),
        ("207B9", "Biznesa vadība (angļu val.)", "Maksa", None, None),
        ("BVzP", "Vadības zinības", "Maksa", None, 1),
    ], rows
    assert [r["places_unlimited"] for r in rows] == [False, False, True], "«*» — неограниченно, пусто — неизвестно"
    first = rows[0]
    assert first["unit"] == "Ekonomikas un sociālo zinātņu fakultāte", first["unit"]
    assert first["stage"].startswith("2. kārtas apstiprinātie"), first["stage"]
    assert first["portal_updated_on"] == "2026-08-03"
    assert first["university_slug"] == "lu" and first["study_mode"] == "Pilna laika (dienas)" and first["city"] == "Rīga"
    assert (first["applications"], first["first_priority"]) == (831, 174)
    # строка без кода и без формы обучения не угадывается, а попадает в отчёт
    assert problems == ["Tiesību zinātne (bez koda), Bakalaura akadēmiskā, Rīga"], problems

    assert duplicate_keys(rows) == []
    assert duplicate_keys([first, dict(first, places=1)]) == [row_key(first)]

    try:
        parse_page(_SAMPLE_PAGE.replace("Latvijas Universitāte", "Nezināma augstskola"), 2026, url)
    except ValueError as error:
        assert "UNIVERSITY_SLUG" in str(error)
    else:
        raise AssertionError("незнакомый вуз должен останавливать прогон")
    assert portal_date("11.08.2025 11:00") == date(2025, 8, 11) and portal_date("") is None
    print("selftest: OK")


def _fetch(url: str, agent: str, robots) -> str:  # type: ignore[no-untyped-def]
    if not robots.can_fetch(agent, url):
        raise RuntimeError(f"robots.txt запрещает {url}")
    request = urllib.request.Request(url, headers={"User-Agent": agent})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def _years(args: list[str]) -> tuple[int, ...]:
    if "--years" not in args:
        return DEFAULT_YEARS
    return tuple(int(year) for year in args[args.index("--years") + 1].split(","))


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    import polite
    from lt_load_admission_stats import robots_from

    load_dotenv()
    agent = polite.user_agent()
    robots = robots_from(_fetch_robots(agent))
    pause = max(PAUSE_SECONDS, float(robots.crawl_delay(agent) or 0))
    extracted_at = datetime.now(timezone.utc).isoformat()

    rows: list[dict] = []
    for year in _years(args):
        year_html = _fetch(f"{BASE_URL}/enrolment/{year}_Vasara", agent, robots)
        pages = university_pages(year_html, year)
        if not pages:
            raise ValueError(f"{year}: на странице года нет ни одного вуза — разметка портала изменилась?")
        for name, url in pages:
            time.sleep(pause)
            page_rows, problems = parse_page(_fetch(url, agent, robots), year, url)
            for row in page_rows:
                row["extracted_at"] = extracted_at
            rows.extend(page_rows)
            stage = page_rows[0]["stage"] if page_rows else "—"
            updated = page_rows[0]["portal_updated_on"] if page_rows else "—"
            print(f"{year} | {name}: строк {len(page_rows)} | срез: {stage} | обновлено {updated}")
            for problem in problems:
                print(f"    не разобрано: {problem}")
        time.sleep(pause)

    duplicates = duplicate_keys(rows)
    if duplicates:
        for key in duplicates:
            print(f"дважды одна и та же строка: {key}")
        raise SystemExit("в данных портала повторяются ключи — ничего не записано")
    print(f"всего строк: {len(rows)}")

    if "--apply" not in args:
        print("пробный прогон — в базу ничего не записано; запишет --apply")
        return
    from db import get_service_client
    from db_retry import execute

    client = get_service_client()
    conflict = "admission_year,portal_university_name,programme_code,programme_kind,study_mode,funding,city"
    for start in range(0, len(rows), 500):
        execute(client.table("vupp_admission_stat").upsert(rows[start : start + 500], on_conflict=conflict))
    print(f"записано: {len(rows)}")


def _fetch_robots(agent: str) -> str | None:
    """robots.txt портала; ответ 4xx — файла нет, ограничений нет (RFC 9309)."""
    import urllib.error

    try:
        request = urllib.request.Request(f"{BASE_URL}/robots.txt", headers={"User-Agent": agent})
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        if error.code >= 500:
            raise SystemExit(f"robots.txt портала не получен (ответ {error.code}) — обход отложен")
        return None


if __name__ == "__main__":
    main()
