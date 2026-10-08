"""Литва: что стало с выпускниками — показатели по направлению и ступени (lt_field_outcome).

Источник — приложение № 4 («lydinčioji informacija») к проекту постановления
правительства Литвы о местах за счёт государства на 2026 год, подготовлено
министерством образования 2026-02-19, данные NŠA. В нём четыре таблицы:
университетская первая ступень, коллегии, цельные программы и отдельно
медицина. Строка таблицы — направление (studijų kryptis), три показателя
через 12 месяцев после окончания у выпускников 2021/22–2023/24 годов,
которые не продолжили учёбу:

- доля работающих (по найму или на себя) от тех, кто должен работать;
- доля работающих там, где нужна квалификация высшего образования;
- доход в процентах от среднего дохода выпускников этой ступени.

Чего в документе нет: числа выпускников в направлении и разреза по вузам и
программам. Поэтому показатель — по направлению по всей стране, и строки с
долей ровно 0 % или 100 % не загружаются: такие значения получаются только
в очень маленьких группах, а проверить размер группы нечем.

Сайт lrv.lt закрыт проверкой «вы не робот», поэтому файл не скачивается:
его сохраняет человек в docs/sources/lt/ (см. PDF_PATH), скрипт читает с диска.

Таблица — миграция 20261008200000_lt_field_outcome.sql.

Запуск:
  python src/lt_load_field_outcomes.py --selftest
  python src/lt_load_field_outcomes.py            # разобрать файл, показать сводку
  python src/lt_load_field_outcomes.py --apply
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PDF_PATH = Path(__file__).resolve().parents[2] / "docs" / "sources" / "lt" / "dTkpkNxT2eM.pdf"
SOURCE_URL = "https://lrv.lt/media/viesa/saugykla/2026/3/dTkpkNxT2eM.pdf"
# Дата создания документа (из свойств файла) — дата, на которую верны цифры.
PUBLISHED_ON = "2026-02-19"
# Выпуски, по которым посчитаны показатели: учебные годы 2021/22–2023/24.
COHORT_FROM, COHORT_TO = 2022, 2024

# Номер таблицы в документе -> уровень программы каталога (programme.degree_level).
LEVEL_BY_TABLE = {"2": "bachelor", "3": "college", "4": "integrated", "5": "integrated"}
EXPECTED_ROWS = {"2": 92, "3": 52, "4": 6, "5": 1}

_TABLE = re.compile(r"^([2-5]) lentelė\.")
_HEADER_END = "vidutinių pajamų"
_TABLE_END = "Duomenų šaltinis"
_NUMBER = r"(\d{1,3},\d{2})\s*%"
_ROW = re.compile(rf"^(.*?)\s*{_NUMBER}\s+{_NUMBER}\s+{_NUMBER}\s*$")
_AVERAGES = re.compile(
    r"koleginių studijų pajamų vidurkis – ([\d ]+) eur.*?universitetinių studijų – ([\d ]+) eur.*?vientisųjų studijų – ([\d ]+) eur"
)


@dataclass(frozen=True)
class Outcome:
    level: str
    field_name: str
    employed_percent: float
    qualified_percent: float
    income_percent: float


def _percent(text: str) -> float:
    return float(text.replace(",", "."))


def parse_outcomes(text: str) -> dict[str, list[Outcome]]:
    """Текст документа -> строки таблиц по номерам таблиц.

    Название направления иногда разбито на две-три строки: начало стоит
    выше строки с числами. Всё, что накопилось между концом шапки (или
    прошлой строкой) и строкой с числами, — название."""
    tables: dict[str, list[Outcome]] = {}
    table: str | None = None
    in_body = False
    pending: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        started = _TABLE.match(line)
        if started:
            table, in_body, pending = started.group(1), False, []
            tables[table] = []
            continue
        if table is None:
            continue
        if line.startswith(_TABLE_END):
            table = None
            continue
        if not in_body:
            in_body = line == _HEADER_END
            continue
        # номер страницы, пустая строка, разделитель страниц
        if not line or line.isdigit() or line.startswith("====="):
            continue
        if line.startswith("Iš viso"):
            pending = []
            continue
        row = _ROW.match(line)
        if row is None:
            pending.append(line)
            continue
        name = " ".join([*pending, row.group(1)]).strip()
        pending = []
        tables[table].append(
            Outcome(LEVEL_BY_TABLE[table], name, _percent(row.group(2)), _percent(row.group(3)), _percent(row.group(4)))
        )
    return tables


def parse_averages(text: str) -> dict[str, int]:
    """Средний доход выпускников ступени, евро — с ним сравнивается доход направления."""
    found = _AVERAGES.search(" ".join(text.split()))
    if found is None:
        raise ValueError("в документе не найдена строка со средними доходами по ступеням")
    college, bachelor, integrated = (int(value.replace(" ", "")) for value in found.groups())
    return {"college": college, "bachelor": bachelor, "integrated": integrated}


# Одно и то же направление, названное в документе длиннее, чем в списке
# общего приёма. Только явные пары: похожие по смыслу названия (например,
# «Gyvulininkystė» и «Gyvūnų mokslai») сюда не добавлять — это догадка.
ALIASES = {
    "filologija pagal kalbą (diplome nurodant konkrečią kalbą)": "filologija pagal kalbą",
}


def normalize(name: str) -> str:
    plain = " ".join(name.lower().split())
    return ALIASES.get(plain, plain)


def is_reliable(outcome: Outcome) -> bool:
    """Доля ровно 0 % или 100 % — признак очень маленькой группы (у двух
    выпускников доли бывают только 0, 50 и 100). Числа выпускников в
    документе нет, поэтому такие строки не показываем вовсе."""
    return all(0 < value < 100 for value in (outcome.employed_percent, outcome.qualified_percent)) and outcome.income_percent > 0


def match_fields(
    outcomes: list[Outcome], catalog: dict[tuple[str, str], str]
) -> tuple[list[tuple[str, Outcome]], list[Outcome], list[Outcome]]:
    """Строки документа -> код направления каталога.

    catalog: (уровень, название направления в нижнем регистре) -> код.
    Возвращает (совпавшие с кодом, ненадёжные, без пары в каталоге)."""
    matched: list[tuple[str, Outcome]] = []
    unreliable: list[Outcome] = []
    unknown: list[Outcome] = []
    for outcome in outcomes:
        if not is_reliable(outcome):
            unreliable.append(outcome)
            continue
        code = catalog.get((outcome.level, normalize(outcome.field_name)))
        if code is None:
            unknown.append(outcome)
        else:
            matched.append((code, outcome))
    return matched, unreliable, unknown


_SAMPLE = """
Pirmosios pakopos koleginių studijų pajamų vidurkis – 1 865 eurai; pirmosios pakopos universitetinių studijų – 2 085 eurai; vientisųjų studijų – 2 814 eurai.

2 lentelė. Pirmosios pakopos absolventų įsidarbinimo rodikliai pagal studijų kryptis (universitetinės studijos).
Studijų pakopa: Pirmosios pakopos studijos
Studijų kryptis
Dalis % nuo
vidutinių pajamų
Aeronautikos inžinerija 92,96% 56,28% 115,04%
Edukologija 100,00% 0,00% 67,05%

===== page 3 =====
3

Filologija pagal kalbą
(diplome nurodant konkrečią
kalbą)
87,18% 53,63% 90,70%
Polimerų ir tekstilės
technologijos 87,50% 50,00% 62,34%
Saugos inžinerija 0,00% 0,00% 0,00%
Iš viso:  89,35 % 63,40 %
Duomenų šaltinis – NŠA.

4 lentelė. Vientisųjų studijų absolventų įsidarbinimo rodikliai pagal studijų kryptis.
Dalis % nuo
vidutinių pajamų
Teisė 90,92% 61,66% 78,55%
Iš viso: 91,96% 65,05%
Duomenų šaltinis – NŠA.
"""


def _selftest() -> None:
    tables = parse_outcomes(_SAMPLE)
    assert list(tables) == ["2", "4"], list(tables)
    assert [o.field_name for o in tables["2"]] == [
        "Aeronautikos inžinerija",
        "Edukologija",
        "Filologija pagal kalbą (diplome nurodant konkrečią kalbą)",
        "Polimerų ir tekstilės technologijos",
        "Saugos inžinerija",
    ], tables["2"]
    assert tables["2"][0] == Outcome("bachelor", "Aeronautikos inžinerija", 92.96, 56.28, 115.04)
    assert tables["2"][2].employed_percent == 87.18 and tables["2"][3].income_percent == 62.34
    assert tables["4"] == [Outcome("integrated", "Teisė", 90.92, 61.66, 78.55)], "итоговая строка не считается"
    assert parse_averages(_SAMPLE) == {"college": 1865, "bachelor": 2085, "integrated": 2814}

    assert is_reliable(tables["2"][0])
    assert not is_reliable(tables["2"][1]), "100 % и 0 % — маленькая группа"
    assert not is_reliable(tables["2"][4]), "все нули — данных нет"
    assert not is_reliable(Outcome("bachelor", "x", 100.0, 50.0, 90.0))

    catalog = {
        ("bachelor", "aeronautikos inžinerija"): "E14",
        ("integrated", "teisė"): "K01",
        ("bachelor", "teisė"): "K01",
    }
    matched, unreliable, unknown = match_fields(tables["2"] + tables["4"], catalog)
    assert [(code, o.level) for code, o in matched] == [("E14", "bachelor"), ("K01", "integrated")], matched
    assert [o.field_name for o in unreliable] == ["Edukologija", "Saugos inžinerija"]
    assert [o.field_name for o in unknown] == [
        "Filologija pagal kalbą (diplome nurodant konkrečią kalbą)",
        "Polimerų ir tekstilės technologijos",
    ]
    # длинное название из документа находит направление каталога
    catalog[("bachelor", "filologija pagal kalbą")] = "N04"
    matched, _, unknown = match_fields(tables["2"], catalog)
    assert ("N04", tables["2"][2]) in matched and [o.field_name for o in unknown] == ["Polimerų ir tekstilės technologijos"]
    try:
        parse_averages("нет такой строки")
    except ValueError:
        pass
    else:
        raise AssertionError("нет строки со средними доходами — ошибка")
    print("selftest: OK")


def read_document() -> tuple[dict[str, list[Outcome]], dict[str, int]]:
    import pypdf

    text = "\n".join(page.extract_text() for page in pypdf.PdfReader(PDF_PATH).pages)
    tables = parse_outcomes(text)
    counts = {number: len(rows) for number, rows in tables.items()}
    # Документ один и не меняется: если разбор дал другое число строк,
    # значит, он что-то потерял или склеил — в базу такое не идёт.
    if counts != EXPECTED_ROWS:
        raise ValueError(f"строк в таблицах {counts}, а должно быть {EXPECTED_ROWS}")
    return tables, parse_averages(text)


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute

    load_dotenv()
    tables, averages = read_document()
    outcomes = [outcome for rows in tables.values() for outcome in rows]
    print(f"строк в документе: {len(outcomes)} | средние доходы по ступеням, евро: {averages}")

    client = get_service_client()
    catalog: dict[tuple[str, str], str] = {}
    programmes: dict[tuple[str, str], int] = {}
    for start in range(0, 100000, 1000):
        page = execute(
            client.table("lt_programme_field")
            .select("field_code, field_name, programme(degree_level)")
            .order("programme_id")
            .range(start, start + 999)
        ).data
        for row in page:
            key = (row["programme"]["degree_level"], normalize(row["field_name"]))
            catalog[key] = row["field_code"]
            programmes[key] = programmes.get(key, 0) + 1
        if len(page) < 1000:
            break

    matched, unreliable, unknown = match_fields(outcomes, catalog)
    covered = sum(programmes[(outcome.level, normalize(outcome.field_name))] for _, outcome in matched)
    print(f"направлений с показателями: {len(matched)} | программ каталога под ними: {covered} из {sum(programmes.values())}")
    print(f"не загружены как ненадёжные (доля 0 % или 100 %): {len(unreliable)}")
    for outcome in unreliable:
        print(f"   {outcome.level}: {outcome.field_name} — {outcome.employed_percent} / {outcome.qualified_percent} / {outcome.income_percent}")
    print(f"в документе есть, в каталоге на этой ступени нет: {len(unknown)}")
    for outcome in unknown:
        print(f"   {outcome.level}: {outcome.field_name}")
    with_data = {(outcome.level, normalize(outcome.field_name)) for outcome in outcomes}
    missing = sorted(key for key in catalog if key not in with_data)
    print(f"в каталоге есть, в документе нет: {len(missing)} направлений, {sum(programmes[key] for key in missing)} программ")
    for level, name in missing:
        print(f"   {level}: {name} ({programmes[(level, name)]})")

    if "--apply" not in args:
        print("\nзаписи не было (добавьте --apply)")
        return
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        {
            "degree_level": outcome.level,
            "field_code": code,
            "field_name": outcome.field_name,
            "cohort_from": COHORT_FROM,
            "cohort_to": COHORT_TO,
            "employed_percent": outcome.employed_percent,
            "qualified_percent": outcome.qualified_percent,
            "income_percent": outcome.income_percent,
            "level_average_income_eur": averages[outcome.level],
            "source_url": SOURCE_URL,
            "published_on": PUBLISHED_ON,
            "extracted_at": now,
        }
        for code, outcome in matched
    ]
    execute(client.table("lt_field_outcome").upsert(rows, on_conflict="degree_level,field_code,cohort_to"))
    # Строки этого выпуска, которых в новом разборе нет, — удалить.
    kept = {(row["degree_level"], row["field_code"]) for row in rows}
    existing = execute(client.table("lt_field_outcome").select("degree_level, field_code").eq("cohort_to", COHORT_TO)).data
    stale = [row for row in existing if (row["degree_level"], row["field_code"]) not in kept]
    for row in stale:
        execute(
            client.table("lt_field_outcome")
            .delete()
            .eq("cohort_to", COHORT_TO)
            .eq("degree_level", row["degree_level"])
            .eq("field_code", row["field_code"])
        )
    print(f"записано: {len(rows)} | удалено устаревших: {len(stale)}")


if __name__ == "__main__":
    main()
