"""Эстония: город программы — по месту учёбы со страницы конкурса в SAIS.

Каталог берёт город из адреса учреждения (sources/ee_haridusportaal.py), а у
вуза с филиалами это город головного здания: программа Нарвского колледжа
Тартуского университета числилась бы в Тарту. Страница конкурса в SAIS
называет место учёбы прямо («Narva kolledž», «Kohtla-Järve»). Решение
владельца 2026-10-13: «переносим город».

Город меняется, только если место учёбы называет ровно один знакомый город.
Несколько городов («Tallinn/Tartu»), «e-õpe» или незнакомое место — город в
каталоге остаётся прежним: выбирать за источник нельзя.

Сбор каталога каждый раз возвращает город из адреса учреждения, поэтому этот
шаг идёт после него и после чтения условий конкурса — последним в
ee_refresh.py. Запустили только сбор каталога — запустите и этот шаг.

Запуск:
  python src/ee_apply_cities.py --selftest
  python src/ee_apply_cities.py            # показать, что изменится, без записи
  python src/ee_apply_cities.py --apply
"""

from __future__ import annotations

import re
import sys
from collections import Counter

# Название города, как его пишут на страницах SAIS, -> ключ города в каталоге
# (programme.city; подпись — в словарях сайта, catalog.city). Новый город
# сначала добавляется сюда, в профиль страны (src/lib/country.ts) и в словари.
CITIES = {
    "Tallinn": "tallinn",
    "Tartu": "tartu",
    "Viljandi": "viljandi",
    "Narva": "narva",
    "Pärnu": "parnu",
    "Haapsalu": "haapsalu",
    "Kohtla-Järve": "kohtla-jarve",
    "Kuressaare": "kuressaare",
    "Reola": "reola",
    "Mõdriku": "modriku",
    "Kukruse": "kukruse",
    "Väimela": "vaimela",
}

# Название как целое слово: «Tartumaa» (уезд) — не «Tartu».
_PATTERNS = {key: re.compile(rf"(?<![\w-]){re.escape(name)}(?![\w-])") for name, key in CITIES.items()}


def city_of_location(location: str | None) -> str | None:
    """Ключ города, если место учёбы называет ровно один знакомый город."""
    if not location:
        return None
    found = [key for key, pattern in _PATTERNS.items() if pattern.search(location)]
    return found[0] if len(found) == 1 else None


def _selftest() -> None:
    assert city_of_location("Tartu") == "tartu"
    assert city_of_location("Tallinn, Kännu 67") == "tallinn"
    assert city_of_location("Narva kolledž") == "narva"
    assert city_of_location("Viljandi kultuuriakadeemia") == "viljandi"
    assert city_of_location("Pärnu kolledž") == "parnu"
    assert city_of_location("Kohtla-Järve") == "kohtla-jarve"
    # уезд — не город: «Tartumaa» не даёт Тарту
    assert city_of_location("Reola küla, Tartumaa") == "reola"
    assert city_of_location("Reola küla, Kambja vald, Tartumaa") == "reola"
    assert city_of_location("Mõdriku, Lääne-Virumaa") == "modriku"
    assert city_of_location("Kukruse, Ida-Virumaa") == "kukruse"
    assert city_of_location("e-õpe, Tartu") == "tartu"
    # несколько городов, не город, незнакомое место — город не меняется
    assert city_of_location("Tallinn/Tartu") is None
    assert city_of_location("Kohtla-Järve/Tartu") is None
    assert city_of_location("Tallinn, Kohtla-Järve") is None
    assert city_of_location("Tallinn, Paikuse, Narva") is None
    assert city_of_location("e-õpe") is None
    assert city_of_location("Rakvere") is None
    assert city_of_location("") is None and city_of_location(None) is None
    assert len(set(CITIES.values())) == len(CITIES)
    print("ee_apply_cities selftest: ok")


def main() -> None:
    args = sys.argv[1:]
    sys.stdout.reconfigure(encoding="utf-8")
    if "--selftest" in args:
        _selftest()
        return
    from dotenv import load_dotenv

    from db import fetch_all, get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()
    rows = fetch_all(
        lambda: client.table("ee_admission")
        .select("programme_id, location, programme(city)")
        .not_.is_("location", "null")
        .order("programme_id")
    )

    changes: dict[str, list[str]] = {}
    moves: Counter = Counter()
    unresolved: Counter = Counter()
    for row in rows:
        city = city_of_location(row["location"])
        if city is None:
            unresolved[row["location"]] += 1
            continue
        current = (row.get("programme") or {}).get("city")
        if current != city:
            changes.setdefault(city, []).append(row["programme_id"])
            moves[f"{current} -> {city}"] += 1

    total = sum(len(ids) for ids in changes.values())
    print(f"конкурсов с местом учёбы: {len(rows)} | город меняется у программ: {total}")
    for move, count in moves.most_common():
        print(f"  {count:3} × {move}")
    if unresolved:
        print("место учёбы не даёт одного города (город в каталоге остаётся прежним):")
        for location, count in unresolved.most_common():
            print(f"  {count:3} × {location}")

    if "--apply" not in args:
        print("\nзаписи не было (добавьте --apply)")
        return
    for city, ids in changes.items():
        for start in range(0, len(ids), 200):
            execute(client.table("programme").update({"city": city}).in_("id", ids[start : start + 200]))
    print(f"записано: {total}")


if __name__ == "__main__":
    main()
