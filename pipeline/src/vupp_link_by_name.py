"""Черновики связей «программа ↔ код приёма statistika.vupp.lv» по
латышскому названию — для вузов, у которых кода приёма в каталоге нет
(Ventspils, ViA, LBTU, часть DU). ЛУ и РТУ связаны по коду —
vupp_link_drafts.py.

Связь предлагается, только если сходится всё сразу:
- название на портале без пометки языка («(angļu valodā)», «(ENG)», «(LV)»)
  совпадает с латышским названием программы в каталоге (без учёта
  регистра);
- пометка языка не спорит с языком программы: английская пометка —
  только английской программе, без пометки или «(LV)» — латышской;
- вид на портале подходит уровню: бакалавру — «Bakalaura…» и «Pirmā
  cikla profesionālā», колледжу — «Īsā cikla profesionālā»;
- город строки портала совпадает с городом программы.

Чего правило не делает: не сравнивает название без уточнения в скобках
(«Skolotājs (Matemātika)» у DU — не «Skolotājs»; у такой программы на
портале десятки подпрограмм, их связь решает человек) и не переводит
английские названия каталога (EKA, RNU, часть DU и ЛУ). Такие программы
попадают в отчёт.

Как и у vupp_link_drafts.py: пишутся только черновики (verified_at пустой),
код у двух программ сразу не связывается ни с одной.

Запуск:
  python src/vupp_link_by_name.py --selftest
  python src/vupp_link_by_name.py            # отчёт
  python src/vupp_link_by_name.py --apply    # записать черновики
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict

from vupp_link_drafts import LEVELS, drafts_without_conflicts, plain

# Вузы с правилом по коду — здесь не трогаются.
CODE_RULE_UNIVERSITIES = {"lu", "rtu"}

# Пометка языка в конце названия на портале.
_LANGUAGE_MARK = re.compile(r"\s*\((angļu valodā|angļu val\.|ENG|LV|latviešu valodā)\)$")
_ENGLISH_MARKS = {"angļu valodā", "angļu val.", "ENG"}

# Вид программы на портале -> уровень каталога.
KIND_LEVEL = {
    "Bakalaura akadēmiskā": "bachelor",
    "Bakalaura profesionālā": "bachelor",
    "Pirmā cikla profesionālā": "bachelor",
    "Īsā cikla profesionālā": "college",
}


def split_language(name: str) -> tuple[str, str | None]:
    """«Datorzinātnes (angļu valodā)» -> («Datorzinātnes», «en»);
    без пометки — язык None."""
    match = _LANGUAGE_MARK.search(name)
    if match is None:
        return name, None
    return name[: match.start()], "en" if match.group(1) in _ENGLISH_MARKS else "lv"


def language_fits(mark: str | None, language: str | None) -> bool:
    if mark == "en":
        return language == "en"
    return language == "lv"


def name_candidates(programme: dict, portal: dict[str, dict]) -> list[str]:
    """Коды портала одного вуза, подходящие программе каталога.
    portal: код -> {"names": set, "kinds": set, "cities": set}."""
    name = (programme.get("name_lv") or "").strip().casefold()
    if not name:
        return []
    found = []
    for code, info in portal.items():
        if plain_city(programme.get("city")) not in info["cities"]:
            continue
        if programme["degree_level"] not in {KIND_LEVEL.get(kind) for kind in info["kinds"]}:
            continue
        for portal_name in info["names"]:
            base, mark = split_language(portal_name)
            if base.strip().casefold() == name and language_fits(mark, programme.get("language_of_instruction")):
                found.append(code)
                break
    return sorted(found)


def plain_city(city: str | None) -> str | None:
    return plain(city) if city else None


def _selftest() -> None:
    assert split_language("Datorzinātnes (angļu valodā)") == ("Datorzinātnes", "en")
    assert split_language("Jaunuzņēmumu vadība (ENG)") == ("Jaunuzņēmumu vadība", "en")
    assert split_language("Starpkultūru komunikācija (LV)") == ("Starpkultūru komunikācija", "lv")
    assert split_language("Skolotājs (Matemātika)") == ("Skolotājs (Matemātika)", None)

    portal = {
        "V0601": {"names": {"Datorzinātnes"}, "kinds": {"Bakalaura akadēmiskā"}, "cities": {"ventspils"}},
        "V0608": {"names": {"Datorzinātnes (ENG)", "Datorzinātnes (angļu valodā)"}, "kinds": {"Bakalaura akadēmiskā"}, "cities": {"ventspils"}},
        "10146": {"names": {"Ilgtspējīgu ēku būvniecība"}, "kinds": {"Īsā cikla profesionālā"}, "cities": {"valmiera"}},
        "10152": {"names": {"Ilgtspējīgu ēku būvniecība"}, "kinds": {"Bakalaura profesionālā"}, "cities": {"valmiera"}},
        "D139TMATE": {"names": {"Skolotājs (Matemātika)"}, "kinds": {"Bakalaura profesionālā"}, "cities": {"daugavpils"}},
    }

    def programme(name: str, language: str, level: str = "bachelor", city: str = "ventspils") -> dict:
        return {"name_lv": name, "language_of_instruction": language, "degree_level": level, "city": city}

    assert name_candidates(programme("Datorzinātnes", "lv"), portal) == ["V0601"]
    assert name_candidates(programme("Datorzinātnes", "en"), portal) == ["V0608"]
    assert name_candidates(programme("Datorzinātnes", "lv", city="riga"), portal) == [], "другой город"
    assert name_candidates(programme("Ilgtspējīgu ēku būvniecība", "lv", city="valmiera"), portal) == ["10152"], "бакалавр — не колледж"
    assert name_candidates(programme("Ilgtspējīgu ēku būvniecība", "lv", "college", "valmiera"), portal) == ["10146"]
    assert name_candidates(programme("Skolotājs", "lv", city="daugavpils"), portal) == [], "подпрограммы не угадываются"
    assert name_candidates({**programme("Datorzinātnes", "lv"), "name_lv": None}, portal) == []
    assert name_candidates(programme("Datorzinātnes", None), portal) == [], "язык неизвестен — без связи"  # type: ignore[arg-type]
    print("selftest: OK")


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    from db import fetch_all, get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()

    stats = fetch_all(
        lambda: client.table("vupp_admission_stat")
        .select("id, university_slug, programme_code, programme_name, programme_kind, city, source_url, admission_year")
        .not_.is_("university_slug", "null")
        .order("id")
    )
    portal: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in stats:
        if row["university_slug"] in CODE_RULE_UNIVERSITIES:
            continue
        info = portal[row["university_slug"]].setdefault(
            row["programme_code"], {"names": set(), "kinds": set(), "cities": set(), "source_url": row["source_url"], "year": 0}
        )
        info["names"].add(row["programme_name"])
        info["kinds"].add(row["programme_kind"])
        info["cities"].add(plain(row["city"]))
        # источник — страница самого свежего года
        if row["admission_year"] > info["year"]:
            info["year"], info["source_url"] = row["admission_year"], row["source_url"]

    universities = {
        row["slug"]: row["id"]
        for row in execute(client.table("university").select("id, slug").in_("slug", sorted(portal))).data
    }
    drafts: list[dict] = []
    unmatched: list[str] = []
    for slug in sorted(portal):
        programmes = fetch_all(
            lambda: client.table("programme")
            .select("id, slug, name_lv, name_en, degree_level, city, language_of_instruction")
            .eq("university_id", universities[slug])
            .in_("degree_level", LEVELS)
            .order("id")
        )
        for programme in programmes:
            codes = name_candidates(programme, portal[slug])
            if not codes:
                unmatched.append(
                    f"{slug} {programme['slug']} ({programme['language_of_instruction']}, {programme['degree_level']}): "
                    f"{programme['name_lv'] or programme['name_en']}"
                )
            for code in codes:
                drafts.append(
                    {
                        "programme_id": programme["id"],
                        "programme_slug": programme["slug"],
                        "catalog_name": programme["name_lv"],
                        "university_slug": slug,
                        "programme_code": code,
                        "method": "name",
                        "source_url": portal[slug][code]["source_url"],
                    }
                )

    drafts, conflicts = drafts_without_conflicts(drafts)
    linked = {(d["university_slug"], d["programme_code"]) for d in drafts}
    by_university: dict[str, int] = defaultdict(int)
    for draft in drafts:
        by_university[draft["university_slug"]] += 1

    print(f"черновиков по названию: {len(drafts)} {dict(by_university)}")
    for draft in drafts:
        names = sorted(portal[draft["university_slug"]][draft["programme_code"]]["names"])
        print(f"  {draft['university_slug']} {draft['programme_slug']} «{draft['catalog_name']}» ↔ {draft['programme_code']} {names}")
    if conflicts:
        print("\nкод у нескольких программ каталога — не связан:")
        for code, slugs in conflicts.items():
            print(f"  {code}: {slugs}")
    print(f"\nпрограммы без пары: {len(unmatched)}")
    for line in unmatched:
        print(f"  {line}")
    unused = sorted((slug, code) for slug in portal for code in portal[slug] if (slug, code) not in linked)
    print(f"\nкоды портала без программы каталога: {len(unused)}")
    for slug, code in unused:
        print(f"  {slug} {code} {sorted(portal[slug][code]['names'])}")

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


if __name__ == "__main__":
    main()
