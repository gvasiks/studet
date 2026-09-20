"""Независимая сверка полноты каталога: сколько программ у вуза по NIID.lv
(государственная база, учреждения вносят данные сами) и сколько у нас.

Зачем. Проверка порогов в main.py ловит СНИЖЕНИЕ числа программ у источника,
но не ловит то, чего сборщик не видел с самого начала: LBTU, DU и Turība
собирались с английских разделов сайтов, и латышских программ в каталоге
не было вовсе. Обнаружилось это только сверкой с независимым источником
(аудит 2026-09-20, см. docs/AUDIT-COMPLETENESS.md).

Как читать. Сравниваются числа по уровням, а не имена: у NIID названия
латышские, у части наших строк английские. NIID даёт по записи на
вариант программы (форма обучения, язык), поэтому небольшое расхождение —
норма; ищите большие дыры (у DU по магистратуре 16 против 0).

    python src/audit_completeness.py                 # все вузы, уровни 7, 8, 9
    python src/audit_completeness.py lbtu du         # только названные
    python src/audit_completeness.py --names lbtu    # ещё и названия NIID для сверки глазами

Ходит на niid.lv по правилам polite.py (у сайта Crawl-delay 10 с), поэтому
полный прогон — около получаса. Ничего не пишет в базу.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()
import polite

polite.install()
from playwright.sync_api import sync_playwright

from db import get_service_client
from sources import niid_colleges as niid

# slug вуза у нас -> название учреждения в NIID
PROVIDERS = {
    "turiba": "Biznesa augstskola Turība",
    "riseba": 'Biznesa, mākslas un tehnoloģiju augstskola "RISEBA"',
    "rtu": "Rīgas Tehniskā universitāte",
    "tsi": "Transporta un sakaru institūts",
    "bsa": "Baltijas Starptautiskā Akadēmija",
    "sse-riga": "Rīgas Ekonomikas augstskola",
    "rgsl": "Rīgas Juridiskā augstskola",
    "lu": "Latvijas Universitāte",
    "venta": "Ventspils Augstskola",
    "lbtu": "Latvijas Biozinātņu un tehnoloģiju universitāte",
    "du": "Daugavpils Universitāte",
    "eka": "Ekonomikas un Kultūras augstskola",
    "rnu": "Rīgas Ziemeļvalstu augstskola",
    "via": "Vidzemes Augstskola",
    "rsu": "Rīgas Stradiņa universitāte",
    "lka": "Latvijas Kultūras akadēmija",
    "lma": "Latvijas Mākslas akadēmija",
    "jvlma": "Jāzepa Vītola Latvijas Mūzikas akadēmija",
    "rai": "Rīgas Aeronavigācijas institūts",
    "lnaa": "Latvijas Nacionālā aizsardzības akadēmija",
    "lutera": "Lutera Akadēmija",
    "ekra": "Eiropas Kristīgā akadēmija",
}

# level_1 в NIID: 7 — бакалавриат и короткие программы, 8 — магистратура,
# 9 — докторантура и резидентура
NIID_LEVELS = ("7", "8", "9")


def _niid_counts(slugs: list[str]) -> tuple[dict[str, Counter], dict[str, list[tuple[str, str]]]]:
    counts: dict[str, Counter] = {slug: Counter() for slug in slugs}
    names: dict[str, list[tuple[str, str]]] = defaultdict(list)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for level in NIID_LEVELS:
            for slug in slugs:
                entries, _ = niid._scrape_provider(page, PROVIDERS[slug], level)
                for entry in entries:
                    ours = niid._college_level(entry["fields"].get("Programmas veids", "")) or "other"
                    counts[slug][ours] += 1
                    names[slug].append((ours, entry["name"]))
                print(f"  NIID {slug} уровень {level}: {len(entries)}", flush=True)
        browser.close()
    return counts, names


def _our_counts(slugs: list[str]) -> dict[str, Counter]:
    client = get_service_client()
    ids = {row["slug"]: row["id"] for row in client.table("university").select("id,slug").execute().data}
    result: dict[str, Counter] = {}
    for slug in slugs:
        rows = client.table("programme").select("name_lv,name_en,degree_level").eq("university_id", ids[slug]).execute().data
        # уникальные (название, уровень): lv/en-варианты и города — одна программа
        unique = {((r["name_en"] or r["name_lv"] or "").lower(), r["degree_level"]) for r in rows}
        result[slug] = Counter(level for _, level in unique)
    return result


def main() -> None:
    args = sys.argv[1:]
    show_names = "--names" in args
    slugs = [a for a in args if not a.startswith("--") and a in PROVIDERS] or list(PROVIDERS)

    niid_counts, niid_names = _niid_counts(slugs)
    our_counts = _our_counts(slugs)

    print(f"\n{'вуз':<9} | {'уровень':<9} | {'NIID':>5} | {'у нас':>5} | разница")
    for slug in slugs:
        for level in ("bachelor", "college", "master", "doctoral"):
            theirs, ours = niid_counts[slug][level], our_counts[slug][level]
            if theirs or ours:
                flag = "  <-- проверить" if theirs - ours >= 3 else ""
                print(f"{slug:<9} | {level:<9} | {theirs:>5} | {ours:>5} | {theirs - ours:+d}{flag}")

    if show_names:
        for slug in slugs:
            print(f"\n== NIID: {slug}")
            for level, name in sorted(niid_names[slug]):
                print(f"   {level:<9} {name}")


if __name__ == "__main__":
    main()
