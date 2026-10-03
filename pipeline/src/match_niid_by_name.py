"""Найти страницу NIID для программ, собранных с сайтов самих вузов.

Зачем. enrich_niid_details.py берёт диплом, описание и срок аккредитации со
страницы программы в NIID.lv, но знает её адрес только у программ, которые
из NIID и собраны (programme.source_url). У программ с собственным
сборщиком вуза такой ссылки нет. Этот скрипт находит её по ЛАТЫШСКОМУ
названию и уровню и записывает в programme.details_source_url — после
этого enrich_niid_details.py заполняет такую программу наравне с остальными.

Работает только для вузов, у программ которых в каталоге есть латышское
название (в NIID все названия латышские): РТУ, RAI, Ventspils, EKRA, LNAA,
Lutera — 209 программ на 2026-10-03. У ЛУ и других вузов названия
английские; для них нужен другой способ.

Правило сопоставления — строгое, без догадок:
- сравнивается нормализованное название (регистр, пробелы, кавычки, хвост
  вида «(angļu valodā)») и уровень обучения;
- если в NIID у этого вуза на этом уровне РОВНО одна программа с таким
  названием — это она;
- если ни одной или несколько (например, академическая и профессиональная
  программы с одним названием) — программа пропускается и попадает в отчёт.
  Неверно привязанная страница показала бы человеку чужой диплом.

  python src/match_niid_by_name.py             # только отчёт
  python src/match_niid_by_name.py --apply     # записать найденные адреса
  python src/match_niid_by_name.py --selftest  # самотест без сети и базы

Записывается только details_source_url и только там, где он пуст.
verified_at и остальные поля не трогаются.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from urllib.parse import urljoin

# level_1 в NIID: 7 — бакалавриат и короткие программы, 8 — магистратура,
# 9 — докторантура (см. sources/niid_colleges.py)
NIID_LEVELS = ("7", "8", "9")

# Название вуза в NIID, если оно отличается от university.name_lv в каталоге.
# Ключ — university.slug. Дополняется, когда отчёт покажет «в NIID 0 программ».
PROVIDER_NAMES: dict[str, list[str]] = {}

# Хвосты в скобках, которые сборщики вузов добавляют к названию, а NIID нет.
_LANGUAGE_SUFFIX = re.compile(r"\((?:angļu|latviešu|krievu)\s+valodā\)", re.IGNORECASE)


def normalize(name: str) -> str:
    """Название для сравнения: без регистра, кавычек, хвоста про язык и лишних пробелов."""
    text = _LANGUAGE_SUFFIX.sub(" ", name)
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"[\"'“”„«»`]", "", text)
    text = re.sub(r"\s*-\s*", " - ", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def build_index(entries: list[tuple[str, str, str]]) -> dict[tuple[str, str], set[str]]:
    """(уровень, нормализованное название) -> адреса страниц NIID.

    entries — (уровень каталога, название NIID, адрес). Множество, а не одно
    значение: совпадение считается, только когда адрес ровно один.
    """
    index: dict[tuple[str, str], set[str]] = defaultdict(set)
    for level, name, url in entries:
        index[(level, normalize(name))].add(url)
    return index


def find_match(index: dict[tuple[str, str], set[str]], level: str, name_lv: str) -> tuple[str | None, str]:
    """Адрес страницы или None и причина: 'ok' | 'нет в NIID' | 'несколько в NIID'."""
    urls = index.get((level, normalize(name_lv)), set())
    if len(urls) == 1:
        return next(iter(urls)), "ok"
    return None, "нет в NIID" if not urls else "несколько в NIID"


def clean_url(href: str, base_url: str) -> str:
    """Адрес страницы программы без параметров поиска (?qy=&tg=&level_1=7)."""
    return urljoin(base_url, href).split("?", 1)[0]


def main(apply: bool) -> None:
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright

    import polite
    from db import get_service_client
    from sources import niid_colleges as base

    load_dotenv()
    polite.install()
    client = get_service_client()

    rows = (
        client.table("programme")
        .select("id, slug, name_lv, degree_level, source_url, details_source_url, university:university_id(slug, name_lv)")
        .not_.is_("name_lv", "null")
        .is_("details_source_url", "null")
        .execute()
        .data
    )
    # программы, чей источник и так NIID, enrich_niid_details.py берёт сам
    rows = [row for row in rows if "niid.lv" not in (row["source_url"] or "")]
    by_university: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_university[row["university"]["slug"]].append(row)

    print(
        f"программ с латышским названием и без страницы NIID: {len(rows)}, вузов: {len(by_university)}"
        + ("" if apply else " (сухой прогон — запись только с --apply)")
    )

    total_matched = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for slug, programmes in sorted(by_university.items()):
            providers = PROVIDER_NAMES.get(slug) or [programmes[0]["university"]["name_lv"]]
            entries: list[tuple[str, str, str]] = []
            for provider in providers:
                for niid_level in NIID_LEVELS:
                    found, _ = base._scrape_provider(page, provider, niid_level)
                    for entry in found:
                        level = base._college_level(entry["fields"].get("Programmas veids", ""))
                        if level is not None:
                            entries.append((level, entry["name"], clean_url(entry["href"], base.BASE_URL)))
            index = build_index(entries)

            matched: list[tuple[dict, str]] = []
            skipped: dict[str, list[str]] = defaultdict(list)
            for programme in programmes:
                url, reason = find_match(index, programme["degree_level"], programme["name_lv"])
                if url:
                    matched.append((programme, url))
                else:
                    skipped[reason].append(f"{programme['name_lv']} [{programme['degree_level']}]")

            print(
                f"\n{slug} ({', '.join(providers)}): в NIID {len({url for _, _, url in entries})} программ; "
                f"у нас {len(programmes)}; найдено {len(matched)}"
            )
            for reason, names in skipped.items():
                unique = sorted(set(names))
                print(f"  {reason}: {len(names)} — " + "; ".join(unique[:12]) + (" …" if len(unique) > 12 else ""))

            if apply:
                # по одному адресу на несколько программ (потоки на разных
                # языках, города) — одним запросом на адрес
                ids_by_url: dict[str, list[str]] = defaultdict(list)
                for programme, url in matched:
                    ids_by_url[url].append(programme["id"])
                for url, ids in ids_by_url.items():
                    client.table("programme").update({"details_source_url": url}).in_("id", ids).execute()
            total_matched += len(matched)

        browser.close()

    print("\n" + polite.report_and_reset())
    print(f"найдено всего: {total_matched} из {len(rows)}" + (" — записано" if apply else ""))
    if apply and total_matched:
        print("Дальше: python src/enrich_niid_details.py --apply")


def selftest() -> None:
    assert normalize("  Būvniecība  (angļu valodā) ") == "būvniecība"
    assert normalize("Jūras transports – kuģa vadīšana") == normalize("Jūras transports - kuģa vadīšana")
    assert normalize("“Datorsistēmas”") == "datorsistēmas"
    assert normalize("Vides Inženierija") == normalize("vides inženierija")
    assert normalize("Būvniecība") != normalize("Būvniecības vadība")

    index = build_index(
        [
            ("bachelor", "Vides inženierija", "https://niid/1"),
            ("master", "Vides inženierija", "https://niid/2"),
            ("master", "Tiesību zinātne", "https://niid/3"),
            ("master", "Tiesību zinātne", "https://niid/4"),  # академическая и профессиональная
            ("bachelor", "Arhitektūra", "https://niid/5"),
            ("bachelor", "Arhitektūra", "https://niid/5"),  # одна запись в двух списках — не дубль
        ]
    )
    assert find_match(index, "bachelor", "Vides inženierija (angļu valodā)") == ("https://niid/1", "ok")
    assert find_match(index, "master", "Vides inženierija") == ("https://niid/2", "ok"), "уровень различает"
    assert find_match(index, "master", "Tiesību zinātne") == (None, "несколько в NIID")
    assert find_match(index, "doctoral", "Vides inženierija") == (None, "нет в NIID")
    assert find_match(index, "bachelor", "Arhitektūra") == ("https://niid/5", "ok")

    assert clean_url("/niid_search/program/743?qy=&tg=&level_1=7", "https://www.niid.lv") == "https://www.niid.lv/niid_search/program/743"
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        main("--apply" in sys.argv)
