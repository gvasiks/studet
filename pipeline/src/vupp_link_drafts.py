"""Черновики связей «программа каталога ↔ код приёма statistika.vupp.lv»
(programme_vupp_link) для ЛУ и РТУ.

Портал называет программу кодом приёма вуза, каталог — своим адресом.
Ошибка связи показала бы на карточке чужие цифры конкурса, поэтому скрипт
пишет только черновики (verified_at пустой); наружу связь выходит после
подтверждения владельцем. Разведка и правила —
docs/checks/VUPP-RECON-2026-10-18.md.

Как находится код:

- ЛУ — на странице программы lu.lv есть ссылка на каталог курсов с кодом
  приёма (`tx_lustudycatalogue_pi1[program]=207B7`). Страница читается
  заново, код не хранится в каталоге: так сборщик ЛУ не меняется.
- РТУ — код программы стоит в её адресе (`…/atvert/MBS?department=31000`),
  у портала он внутри кода приёма: «RMBS0», «LMCE0», «NGCS0». Первая буква
  — вариант набора (Рига, Лиепая, Резекне, Морская академия, заочная
  форма), последняя цифра — тоже, поэтому сверяется середина кода и город
  строки портала с городом программы.

Кандидаты берутся из уже собранной статистики (vupp_admission_stat —
сначала vupp_stats.py --apply). Код, который нашёлся у двух программ
каталога сразу, в черновики не идёт, а попадает в отчёт.

Запуск:
  python src/vupp_link_drafts.py --selftest
  python src/vupp_link_drafts.py            # отчёт, в базу ничего не пишется
  python src/vupp_link_drafts.py --apply    # записать черновики
"""

from __future__ import annotations

import re
import sys
import time
import unicodedata
import urllib.request
from collections import defaultdict

# ссылка на каталог курсов ЛУ; в разметке скобки бывают закодированы
_LU_CODE = re.compile(r"tx_lustudycatalogue_pi1(?:%5B|\[)program(?:%5D|\])=([A-Za-z0-9]{2,12})")
_RTU_CODE = re.compile(r"/atvert/([A-Z0-9]{2,6})\?")
LU_PAUSE_SECONDS = 2.0
# уровни, которые набираются через портал (pamatstudijas)
LEVELS = ["bachelor", "college"]


def plain(text: str) -> str:
    """«Rēzekne» -> «rezekne»: город портала в виде города каталога."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()


def lu_codes(html: str) -> set[str]:
    return set(_LU_CODE.findall(html))


def rtu_code(source_url: str | None) -> str | None:
    match = _RTU_CODE.search(source_url or "")
    return match.group(1) if match else None


def rtu_candidates(code: str, city: str | None, portal: dict[str, set[str]]) -> list[str]:
    """Коды портала РТУ с той же серединой и тем же городом.
    portal: код приёма -> города его строк (в виде каталога)."""
    return sorted(
        portal_code
        for portal_code, cities in portal.items()
        if len(portal_code) == len(code) + 2 and portal_code[1:-1] == code and portal_code[-1].isdigit() and city in cities
    )


def drafts_without_conflicts(drafts: list[dict]) -> tuple[list[dict], dict[str, list[str]]]:
    """Код, который достался двум программам каталога, не связывается ни с
    одной: какая из них настоящая, решает человек."""
    owners: dict[tuple[str, str], set[str]] = defaultdict(set)
    for draft in drafts:
        owners[(draft["university_slug"], draft["programme_code"])].add(draft["programme_slug"])
    conflicts = {code: sorted(slugs) for (_, code), slugs in owners.items() if len(slugs) > 1}
    return [d for d in drafts if d["programme_code"] not in conflicts], conflicts


def _selftest() -> None:
    assert plain("Rēzekne") == "rezekne" and plain("Liepāja") == "liepaja" and plain("Rīga") == "riga"
    page = (
        '<a href="https://www.lu.lv/studijas/?tx_lustudycatalogue_pi1%5Baction%5D=detail&amp;'
        'tx_lustudycatalogue_pi1%5Bprogram%5D=207B7&amp;cHash=ae35">Additional</a>'
        '<a href="/x?tx_lustudycatalogue_pi1[program]=22523JapS">x</a>'
    )
    assert lu_codes(page) == {"207B7", "22523JapS"}, lu_codes(page)
    assert lu_codes("<p>bez saites</p>") == set()

    assert rtu_code("https://www.rtu.lv/lv/studijas/visas-studiju-programmas/atvert/MBS?department=31000&type=A") == "MBS"
    assert rtu_code("https://www.rtu.lv/en/studies/all-study-programmes/open/civil-engineering?id=188") is None
    portal = {
        "RMCE0": {"riga"}, "LMCE0": {"liepaja"}, "EMCE0": {"rezekne"},
        "LGCS0": {"liepaja"}, "NGCS0": {"liepaja"},
        "RMCEX": {"riga"},  # в конце не цифра — не вариант этой программы
        "RMCEE0": {"riga"},  # не та длина
    }
    assert rtu_candidates("MCE", "liepaja", portal) == ["LMCE0"]
    assert rtu_candidates("MCE", "riga", portal) == ["RMCE0"]
    assert rtu_candidates("GCS", "liepaja", portal) == ["LGCS0", "NGCS0"], "очная и заочная форма — оба кода"
    assert rtu_candidates("GCS", "riga", portal) == []

    drafts = [
        {"programme_slug": "a", "university_slug": "lu", "programme_code": "207B7"},
        {"programme_slug": "b", "university_slug": "lu", "programme_code": "207B7"},
        {"programme_slug": "c", "university_slug": "lu", "programme_code": "207B9"},
    ]
    kept, conflicts = drafts_without_conflicts(drafts)
    assert [d["programme_slug"] for d in kept] == ["c"] and conflicts == {"207B7": ["a", "b"]}
    print("selftest: OK")


def _fetch(url: str, agent: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": agent})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "replace")


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")
    import urllib.robotparser

    from dotenv import load_dotenv

    import polite
    from db import fetch_all, get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()
    agent = polite.user_agent()

    # Строки портала: код -> названия и города (по вузу)
    stats = fetch_all(
        lambda: client.table("vupp_admission_stat")
        .select("id, university_slug, programme_code, programme_name, city")
        .in_("university_slug", ["lu", "rtu"])
        .order("id")
    )
    if not stats:
        raise SystemExit("в vupp_admission_stat нет строк ЛУ и РТУ — сначала vupp_stats.py --apply")
    portal_cities: dict[str, dict[str, set[str]]] = {"lu": defaultdict(set), "rtu": defaultdict(set)}
    portal_names: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in stats:
        portal_cities[row["university_slug"]][row["programme_code"]].add(plain(row["city"]))
        portal_names[(row["university_slug"], row["programme_code"])].add(row["programme_name"])

    universities = {
        row["slug"]: row["id"]
        for row in execute(client.table("university").select("id, slug").in_("slug", ["lu", "rtu"])).data
    }
    drafts: list[dict] = []
    without_code: list[str] = []

    robots = urllib.robotparser.RobotFileParser("https://www.lu.lv/robots.txt")
    robots.read()
    lu_programmes = fetch_all(
        lambda: client.table("programme")
        .select("id, slug, name_lv, name_en, source_url")
        .eq("university_id", universities["lu"])
        .in_("degree_level", LEVELS)
        .order("id")
    )
    print(f"ЛУ: программ бакалавра и колледжа — {len(lu_programmes)}, читаю страницы lu.lv…")
    for programme in lu_programmes:
        url = programme["source_url"] or ""
        if not url.startswith("https://www.lu.lv/") or not robots.can_fetch(agent, url):
            without_code.append(f"lu {programme['slug']}: адрес не на lu.lv или закрыт robots.txt")
            continue
        time.sleep(LU_PAUSE_SECONDS)
        codes = lu_codes(_fetch(url, agent))
        on_portal = sorted(code for code in codes if code in portal_cities["lu"])
        if not on_portal:
            without_code.append(f"lu {programme['slug']}: на странице {sorted(codes) or 'кода нет'}, в статистике портала нет")
        for code in on_portal:
            drafts.append(_draft(programme, "lu", code, "code_from_page", url))

    rtu_programmes = fetch_all(
        lambda: client.table("programme")
        .select("id, slug, name_lv, name_en, city, source_url")
        .eq("university_id", universities["rtu"])
        .in_("degree_level", LEVELS)
        .order("id")
    )
    for programme in rtu_programmes:
        code = rtu_code(programme["source_url"])
        candidates = rtu_candidates(code, programme["city"], portal_cities["rtu"]) if code else []
        if not candidates:
            reason = "кода в адресе нет" if not code else f"{code} в городе {programme['city']} на портале нет"
            without_code.append(f"rtu {programme['slug']}: {reason}")
        for candidate in candidates:
            drafts.append(_draft(programme, "rtu", candidate, "code_from_slug", programme["source_url"]))

    drafts, conflicts = drafts_without_conflicts(drafts)
    linked_codes = {(d["university_slug"], d["programme_code"]) for d in drafts}

    print(f"\nчерновиков связей: {len(drafts)} (ЛУ {sum(d['university_slug'] == 'lu' for d in drafts)}, РТУ {sum(d['university_slug'] == 'rtu' for d in drafts)})")
    print("\nсвязи, где название портала не совпадает с названием каталога (проверить глазами):")
    for draft in drafts:
        names = portal_names[(draft["university_slug"], draft["programme_code"])]
        if draft["catalog_name"].casefold() not in {name.casefold() for name in names}:
            print(f"  {draft['university_slug']} {draft['programme_slug']} «{draft['catalog_name']}» ↔ {draft['programme_code']} {sorted(names)}")
    if conflicts:
        print("\nкод у нескольких программ каталога — не связан:")
        for code, slugs in conflicts.items():
            print(f"  {code}: {slugs}")
    print(f"\nпрограммы без кода на портале: {len(without_code)}")
    for line in without_code:
        print(f"  {line}")
    unused = sorted(
        (slug, code) for slug in ("lu", "rtu") for code in portal_cities[slug] if (slug, code) not in linked_codes
    )
    print(f"\nкоды портала без программы каталога: {len(unused)}")
    for slug, code in unused:
        print(f"  {slug} {code} {sorted(portal_names[(slug, code)])}")

    if "--apply" not in args:
        print("\nотчёт — в базу ничего не записано; запишет --apply")
        return
    records = [
        {key: draft[key] for key in ("programme_id", "university_slug", "programme_code", "method", "source_url")}
        for draft in drafts
    ]
    # ignore_duplicates: уже записанная связь (и её подтверждение) не трогается
    for start in range(0, len(records), 500):
        execute(
            client.table("programme_vupp_link").upsert(
                records[start : start + 500], on_conflict="programme_id,university_slug,programme_code", ignore_duplicates=True
            )
        )
    print(f"\nзаписано черновиков: {len(records)} (подтверждённые не тронуты)")


def _draft(programme: dict, university: str, code: str, method: str, source_url: str | None) -> dict:
    return {
        "programme_id": programme["id"],
        "programme_slug": programme["slug"],
        "catalog_name": programme["name_lv"] or programme["name_en"] or "",
        "university_slug": university,
        "programme_code": code,
        "method": method,
        "source_url": source_url,
    }


if __name__ == "__main__":
    main()
