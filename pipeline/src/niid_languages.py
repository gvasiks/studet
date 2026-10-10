"""Язык обучения программ, у которых сайт вуза его не называет, — из NIID.

Пять сборщиков (rnu, du, lka, tsi, venta) раньше подставляли язык: на
страницах этих вузов поле языка есть не у всех программ, а Ventspils
Augstskola пишет язык только в названии и только у части программ. Владелец
решил (2026-10-10) брать язык таких программ из NIID.lv — государственной
базы, где поле «Valoda» заполнено у каждой программы.

Таблица KNOWN ниже — снимок NIID на 2026-10-10: слаг нашей программы ->
(номер записи NIID, языки). Первым стоит язык, который был у программы в
каталоге, — он сохраняет слаг; второй язык даёт отдельную запись со слагом
«…-en» или «…-lv» (решение владельца 2026-10-10: программа на двух языках —
две записи). Таблица собрана из замеров скриптом, а не набрана руками;
вручную сопоставлены только названия у четырёх вузов с английскими сайтами
(у Ventspils связь идёт по ссылке на страницу NIID). Сверка и её история —
docs/checks/NIID-LANGUAGE-REVIEW.md.

Оговорка, записанная при решении: «latviešu/angļu» в NIID означает, что
программу разрешено вести на двух языках, но не обязательно, что набор идёт
на обоих. У РТУ это различие оказалось существенным (rtu_languages.py).

В таблице НЕТ двух программ, у которых NIID и сайт вуза расходятся:
«Environmental Science» у DU (сайт называет оба языка, NIID — латышский) и
«Digitālā kultūra un tekstveide» у Ventspils (NIID — только английский).
Их решает человек.

Программа этих пяти вузов, которой нет ни в таблице, ни с языком на сайте,
получает пустой язык: main.py оставит у неё прежний, а новую не запишет —
тогда её надо найти в NIID и дописать сюда.

Таблица устаревает. Сверить её с NIID:

  python src/niid_languages.py --check      # читает NIID, в базу не пишет
  python src/niid_languages.py --selftest   # самотест без сети
"""

from __future__ import annotations

import sys

# Как учреждение называется в NIID — для сверки (--check).
PROVIDERS = {
    "rnu": "Rīgas Ziemeļvalstu augstskola",
    "du": "Daugavpils Universitāte",
    "lka": "Latvijas Kultūras akadēmija",
    "tsi": "Transporta un sakaru institūts",
    "venta": "Ventspils Augstskola",
}

# сборщик -> слаг программы -> (номер записи NIID, языки; первый сохраняет слаг)
KNOWN: dict[str, dict[str, tuple[str, tuple[str, ...]]]] = {
    "rnu": {
        "information-systems-bachelor": ("117", ("lv", "en")),  # Informācijas sistēmas — latviešu/angļu (LV/EN)
        "tourism-service-organisation-college": ("11948", ("lv", "en")),  # Tūrisma pakalpojumu organizēšana — latviešu/angļu (LV/EN)
        "computer-systems-master": ("115", ("lv", "en")),  # Datorsistēmas — latviešu/angļu (LV/EN)
        "business-administration-bachelor": ("28450", ("lv", "en")),  # Uzņēmējdarbības vadība — latviešu/angļu (LV/EN)
        "business-administration-master": ("116", ("lv", "en")),  # Uzņēmējdarbības vadība — latviešu/angļu (LV/EN)
        "business-administration-in-tourism-bachelor": ("114", ("lv", "en")),  # Uzņēmējdarbības vadība tūrismā — latviešu/angļu (LV/EN)
    },
    "du": {
        "biology": ("59", ("lv",)),  # Bioloģija — latviešu (LV)
        "chemistry": ("12652", ("lv",)),  # Ķīmija — latviešu (LV)
        "eastern-european-cultural-and-business-relations": ("4900", ("lv", "en")),  # Austrumeiropas kultūras sakari un integrācijas procesi — latviešu/angļu (LV/EN)
        "history": ("27857", ("lv",)),  # Vēsture — latviešu (LV)
        "language-and-culture-studies": ("60", ("lv", "en")),  # Valodu un kultūras studijas — latviešu/angļu (LV/EN)
        "psychology": ("57", ("lv",)),  # Psiholoģija — latviešu (LV)
        "science-of-law": ("25603", ("lv",)),  # Tiesību zinātne — latviešu (LV)
        "strategic-risks-and-crisis-management": ("28329", ("lv",)),  # Stratēģiskie riski un krīžu pārvaldība — latviešu (LV)
    },
    "lka": {
        "creative-industries": ("24464", ("lv",)),  # Radošās industrijas (uzņemšana 2026./27. gadā) — latviešu (LV)
        "audiovisual-and-performing-art": ("24944", ("lv",)),  # Audiovizuālā un skatuves māksla (Uzņemšana 2026./27. gadā) — latviešu (LV)
        "creative-industries-and-growth-management": ("25733", ("lv", "en")),  # Radošās industrijas un izaugsmes menedžments (uzņemšana 2026./27. gadā) — latviešu un angļu (LV-EN)
        "cultural-and-arts-management": ("172", ("lv",)),  # Kultūras un mākslas pārvaldība (uzņemšana 2026./27. gadā) — latviešu (LV)
    },
    "tsi": {
        "transport-and-logistics": ("17576", ("en", "lv")),  # Intelektisks transports un viedā loģistika — latviešu/angļu (LV/EN)
        "telematics-and-logistics": ("575", ("en", "lv")),  # Telemātika un loģistika — latviešu/angļu (LV/EN)
        "digital-economy-and-business": ("26819", ("en", "lv")),  # Digitālā ekonomika un uzņēmējdarbība — latviešu/angļu (LV/EN)
    },
    "venta": {
        "programmesanas-specialists": ("24592", ("lv",)),  # Programmēšanas speciālists — latviešu (LV)
        "datorzinatnes-bakalaurs": ("919", ("lv", "en")),  # Datorzinātnes — latviešu/angļu (LV/EN)
        "elektronika-bakalaurs": ("24950", ("lv",)),  # Elektronikas inženierija — latviešu (LV)
        "biznesa-vadiba-bakalaurs": ("19738", ("lv",)),  # Biznesa vadība — latviešu (LV)
        "valodas-sazina-un-kulturvide": ("28568", ("lv", "en")),  # Valodas, saziņa un kultūrvide — latviešu/angļu (LV/EN)
        "datorzinatnes-magistrs": ("922", ("lv", "en")),  # Datorzinātnes — latviešu/angļu (LV/EN)
        "uznemejdarbibas-vadiba": ("584", ("lv",)),  # Uzņēmējdarbības vadība — latviešu (LV)
        "tulkosana-un-terminologija": ("28502", ("lv",)),  # Tulkošana un terminoloģija — latviešu (LV)
        "elektronika-magistrs": ("27060", ("lv",)),  # Elektronika — latviešu (LV)
    },
}


def languages_from_niid_text(text: str) -> list[str]:
    """«latviešu/angļu (LV/EN)» -> ['lv', 'en']; «angļu (EN)» -> ['en']."""
    lowered = text.lower()
    return [code for code, word in (("lv", "latvie"), ("en", "angļu")) if word in lowered]


def languages_for(source: str, slug: str, stated: list[str]) -> list[str]:
    """Языки программы: из таблицы NIID, если программа в ней есть, иначе те,
    что назвал сайт вуза (stated). Пустой список — язык неизвестен."""
    entry = KNOWN.get(source, {}).get(slug)
    return list(entry[1]) if entry else stated


def records(slug: str, languages: list[str]) -> list[tuple[str, str | None]]:
    """Слаг и язык каждой записи каталога: первый язык — со слагом программы,
    остальные — «слаг-язык». Языков нет — одна запись без языка."""
    if not languages:
        return [(slug, None)]
    return [(slug if index == 0 else f"{slug}-{language}", language) for index, language in enumerate(languages)]


def check() -> None:
    """Сверить таблицу с NIID. Код возврата 1, если что-то разошлось."""
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright

    import polite
    from sources import niid_colleges as base

    load_dotenv()
    polite.install()
    problems: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for source, provider in PROVIDERS.items():
            in_niid: dict[str, str] = {}
            for level in ("7", "8", "9"):
                entries, _website = base._scrape_provider(page, provider, level)
                for entry in entries:
                    in_niid[base._programme_id(entry["href"])] = entry["fields"].get("Valoda", "")
            for slug, (niid_id, languages) in KNOWN[source].items():
                if niid_id not in in_niid:
                    problems.append(f"{source}/{slug}: записи NIID {niid_id} больше нет в списке учреждения")
                elif sorted(languages_from_niid_text(in_niid[niid_id])) != sorted(languages):
                    problems.append(f"{source}/{slug}: в таблице {list(languages)}, в NIID «{in_niid[niid_id]}» (запись {niid_id})")
            print(f"{source}: сверено {len(KNOWN[source])} программ", flush=True)
        browser.close()
    if problems:
        print("\nТАБЛИЦА ЯЗЫКОВ РАЗОШЛАСЬ С NIID — поправьте KNOWN в niid_languages.py:")
        for line in problems:
            print("  " + line)
        sys.exit(1)
    print("OK: таблица совпадает с NIID")


def selftest() -> None:
    assert languages_from_niid_text("latviešu/angļu (LV/EN)") == ["lv", "en"]
    assert languages_from_niid_text("latviešu un angļu (LV-EN)") == ["lv", "en"]
    assert languages_from_niid_text("angļu (EN)") == ["en"] and languages_from_niid_text("") == []

    assert records("x", ["lv", "en"]) == [("x", "lv"), ("x-en", "en")]
    assert records("x", ["en", "lv"]) == [("x", "en"), ("x-lv", "lv")]
    assert records("x", ["lv"]) == [("x", "lv")] and records("x", []) == [("x", None)]

    assert languages_for("rnu", "нет-такой", ["lv"]) == ["lv"], "вне таблицы — язык с сайта"
    assert languages_for("rnu", "нет-такой", []) == [], "вне таблицы и без языка на сайте — пусто"
    some_slug, (_niid_id, some_languages) = next(iter(KNOWN["rnu"].items()))
    assert languages_for("rnu", some_slug, []) == list(some_languages)

    assert set(KNOWN) == set(PROVIDERS)
    for source, programmes in KNOWN.items():
        ids = [niid_id for niid_id, _ in programmes.values()]
        assert len(ids) == len(set(ids)), f"{source}: один номер NIID у двух программ"
        for slug, (niid_id, languages) in programmes.items():
            assert niid_id.isdigit(), (source, slug)
            assert languages and set(languages) <= {"lv", "en"} and len(set(languages)) == len(languages), (source, slug)
    total = sum(len(programmes) for programmes in KNOWN.values())
    two = sum(1 for programmes in KNOWN.values() for _, languages in programmes.values() if len(languages) == 2)
    assert (total, two) == (30, 15), (total, two)
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    elif "--check" in sys.argv:
        check()
    else:
        print("Запуск: --check (сверить с NIID) или --selftest.")
