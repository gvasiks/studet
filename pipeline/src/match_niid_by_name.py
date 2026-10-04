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

Три уточнения (2026-10-04, разбор 25 несопоставленных программ):
- тип NIID «programma ar kodu 44» (профессиональная программа 6-го уровня
  после короткого цикла) считается бакалавриатом — так эти программы
  записаны в каталоге;
- у РТУ несколько программ с одним названием различает вторая буква кода
  программы (RTU_TYPE_CODES) — она однозначно соответствует типу программы
  в NIID;
- названия, которые автоматически не совпадают, привязаны вручную
  (MANUAL_PAGES): два отличаются от NIID одним словом, ещё у четырёх
  программ (EKrA, RAI) в NIID в названии стоит специализация.
Специализация в скобках («(pilots)», «(Ikonogrāfija)») — НЕ хвост: такие
программы автоматически не привязываются, только по решению владельца.

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

# Вторая буква кода программы РТУ (slug «bcb-31000» -> «C») -> код типа
# программы в NIID. Проверено 2026-10-04 на 151 уже привязанной программе:
# соответствие без единого исключения. Нужно только там, где в NIID у РТУ
# несколько программ с одним названием на одном уровне.
RTU_TYPE_CODES = {"B": "43", "C": "42", "M": "45", "G": "47", "K": "41", "D": "51"}

# Привязка вручную: (university.slug, programme.slug) -> страница NIID.
# Только для названий, которые отличаются от NIID одним словом и потому не
# совпадают автоматически. Страница принимается, только пока она есть в
# списке вуза в NIID на том же уровне.
MANUAL_PAGES: dict[tuple[str, str], str] = {
    # «Eiropas valodu un kultūras studijas» у нас, «…kultūru studijas» в NIID
    ("rtu", "hbe"): "https://www.niid.lv/niid_search/program/435",
    # «…savstarpēji saistītu sistēmu…» у нас, «…savienotu… (MERIT)» в NIID
    ("rtu", "dms-33000"): "https://www.niid.lv/niid_search/program/28240",
    # Решение владельца 2026-10-04: в NIID у этих программ в названии стоит
    # специализация, а другой записи программы у вуза нет — привязываем к ней.
    # «Bībeles māksla» -> «Bībeles māksla (Ikonogrāfija)»
    ("ekra", "biblijas-maksla-bachelor"): "https://www.niid.lv/niid_search/program/189",
    ("ekra", "biblijas-maksla-master"): "https://www.niid.lv/niid_search/program/17277",
    # «Gaisa transportsistēmu vadība un ekspluatācija» -> «… (pilots)»
    ("rai", "gtve-lv"): "https://www.niid.lv/niid_search/program/8377",
    ("rai", "gtve-en"): "https://www.niid.lv/niid_search/program/8377",
}

# Хвосты в скобках, которые сборщики вузов добавляют к названию, а NIID нет.
_LANGUAGE_SUFFIX = re.compile(r"\((?:angļu|latviešu|krievu)\s+valodā\)", re.IGNORECASE)
# Пометки в скобках, не относящиеся к названию: «(kopīga programma ar Banku
# augstskolu)» у РТУ, «(uzņemšana plānota 2027./28. studiju gadā)» в NIID.
# Специализации («(pilots)») сюда не входят и остаются частью названия.
_NOTE_SUFFIX = re.compile(r"\((?:kopīga programma|uzņemšana plānota)[^)]*\)", re.IGNORECASE)


def type_code(kind: str) -> str | None:
    """«… - 6. LKI (programma ar kodu 44)» -> «44»."""
    match = re.search(r"kodu\s+(\d+)", kind)
    return match.group(1) if match else None


def extra_level(kind: str) -> str | None:
    """Уровень каталога для типов NIID, которых не знает сборщик колледжей."""
    return "bachelor" if type_code(kind) == "44" else None


def rtu_type_code(slug: str) -> str | None:
    """Slug программы РТУ («bcb-31000») -> код типа программы в NIID («42»)."""
    return RTU_TYPE_CODES.get(slug[1].upper()) if len(slug) > 1 else None


def normalize(name: str) -> str:
    """Название для сравнения: без регистра, кавычек, хвоста про язык и лишних пробелов."""
    text = _LANGUAGE_SUFFIX.sub(" ", name)
    text = _NOTE_SUFFIX.sub(" ", text)
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


def find_match(
    index: dict[tuple[str, str], set[str]],
    level: str,
    name_lv: str,
    type_codes: dict[str, str | None] | None = None,
    wanted_code: str | None = None,
) -> tuple[str | None, str]:
    """Адрес страницы или None и причина: 'ok' | 'нет в NIID' | 'несколько в NIID'.

    type_codes (адрес -> код типа программы в NIID) и wanted_code — подсказка
    для случая «несколько»: если ровно у одной из страниц нужный тип, это она.
    """
    urls = index.get((level, normalize(name_lv)), set())
    if len(urls) > 1 and type_codes and wanted_code:
        urls = {url for url in urls if type_codes.get(url) == wanted_code} or urls
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
            type_codes: dict[str, str | None] = {}
            for provider in providers:
                for niid_level in NIID_LEVELS:
                    found, _ = base._scrape_provider(page, provider, niid_level)
                    for entry in found:
                        kind = entry["fields"].get("Programmas veids", "")
                        level = base._college_level(kind) or extra_level(kind)
                        if level is not None:
                            url = clean_url(entry["href"], base.BASE_URL)
                            entries.append((level, entry["name"], url))
                            type_codes[url] = type_code(kind)
            index = build_index(entries)
            levels_by_url = {url: level for level, _, url in entries}

            matched: list[tuple[dict, str]] = []
            skipped: dict[str, list[str]] = defaultdict(list)
            for programme in programmes:
                manual = MANUAL_PAGES.get((slug, programme["slug"]))
                if manual:
                    # ручная привязка действует, пока страница есть у вуза в NIID на том же уровне
                    if levels_by_url.get(manual) == programme["degree_level"]:
                        url, reason = manual, "ok"
                    else:
                        url, reason = None, "страницы из MANUAL_PAGES нет в NIID"
                else:
                    url, reason = find_match(
                        index,
                        programme["degree_level"],
                        programme["name_lv"],
                        type_codes,
                        rtu_type_code(programme["slug"]) if slug == "rtu" else None,
                    )
                if url:
                    matched.append((programme, url))
                else:
                    skipped[reason].append(f"{programme['name_lv']} [{programme['degree_level']}]")

            print(
                f"\n{slug} ({', '.join(providers)}): в NIID {len({url for _, _, url in entries})} программ; "
                f"у нас {len(programmes)}; найдено {len(matched)}"
            )
            for programme, url in matched:
                print(f"  найдено: {programme['name_lv']} [{programme['degree_level']}] ({programme['slug']}) -> {url}")
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

    # пометки в скобках — не часть названия; специализация — часть
    assert normalize("Finanšu pārvaldības informācijas sistēmas (kopīga programma ar Banku augstskolu)") == normalize("Finanšu pārvaldības informācijas sistēmas")
    assert normalize("Datorzinātne un organizāciju tehnoloģijas (uzņemšana plānota 2027./28. studiju gadā)") == normalize("Datorzinātne un organizāciju tehnoloģijas")
    assert normalize("Gaisa transportsistēmu vadība un ekspluatācija (pilots)") != normalize("Gaisa transportsistēmu vadība un ekspluatācija")
    assert normalize("Bībeles māksla (Ikonogrāfija)") != normalize("Bībeles māksla")

    kind_44 = "Pirmā cikla profesionālā studiju programma pēc īsā vai pirmā cikla - 6. LKI (programma ar kodu 44)"
    assert type_code(kind_44) == "44" and extra_level(kind_44) == "bachelor"
    assert extra_level("Arodizglītība - 3. LKI (programma ar kodu 22)") is None
    assert type_code("bez koda") is None

    assert rtu_type_code("bcb-31000") == "42" and rtu_type_code("bbb-31000") == "43"
    assert rtu_type_code("dmd-33000") == "45" and rtu_type_code("dgd-33000") == "47"
    assert rtu_type_code("uiv-0j000-riga") is None, "неизвестная буква — подсказки нет"

    codes = {"https://niid/3": "45", "https://niid/4": "47"}
    assert find_match(index, "master", "Tiesību zinātne", codes, "47") == ("https://niid/4", "ok")
    assert find_match(index, "master", "Tiesību zinātne", codes, "45") == ("https://niid/3", "ok")
    assert find_match(index, "master", "Tiesību zinātne", codes, "51") == (None, "несколько в NIID"), "нужного типа нет — не угадываем"
    assert find_match(index, "master", "Tiesību zinātne", codes, None) == (None, "несколько в NIID")
    assert find_match(index, "master", "Tiesību zinātne", {"https://niid/3": "45", "https://niid/4": "45"}, "45") == (None, "несколько в NIID")
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        main("--apply" in sys.argv)
