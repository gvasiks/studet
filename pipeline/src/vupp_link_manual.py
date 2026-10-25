"""Черновики связей «программа ↔ код приёма statistika.vupp.lv» по ручной
таблице — для программ, у которых в каталоге английское название (ЛУ, DU,
EKA, RNU), и для программ с подпрограммами на портале («Skolotājs (…)»).
Правила по коду и по латышскому названию — vupp_link_drafts.py и
vupp_link_by_name.py.

Таблица MANUAL называет не коды, а латышские названия на портале: у RNU код
меняется каждый год («1B2026»), у EKA он включает форму обучения
(«BVzP», «BVzNs»). Название же стабильно, и коды следующего года найдутся
сами — но новые черновики снова подтверждает владелец.

Чего в таблице нет намеренно (отчёт — docs/checks/VUPP-LINKS-REVIEW.md):
- английские потоки, если портал не помечает язык (LBTU, EKA, RNU, DU):
  не ясно, в одной ли строке портала латышский и английский набор;
- английская подпрограмма ЛУ «East-West Intercultural Studies» (22569):
  английской записи этой программы в каталоге нет;
- программы, которых на портале нет (ЛУ Medicine (en), Radiography).

Запуск:
  python src/vupp_link_manual.py --selftest
  python src/vupp_link_manual.py            # отчёт
  python src/vupp_link_manual.py --apply    # записать черновики
"""

from __future__ import annotations

import sys
from collections import defaultdict

from vupp_link_drafts import drafts_without_conflicts

_PRESCHOOL = ["Pirmsskolas skolotājs"] + [
    f"Pirmsskolas skolotājs ({city})" for city in ("Bauska", "Cēsis", "Jēkabpils", "Kuldīga", "Madona", "Tukums")
]
_PRIMARY = ["Sākumizglītības skolotājs"] + [
    f"Sākumizglītības skolotājs ({city})" for city in ("Bauska", "Cēsis", "Jēkabpils", "Kuldīga", "Madona", "Tukums")
]
_COACH = ["Sporta treneris"] + [f"Sporta treneris ({city})" for city in ("Cēsis", "Kuldīga", "Madona", "Tukums")]
_DU_TEACHER = [
    f"Skolotājs ({subject})"
    for subject in (
        "Matemātika", "angļu valoda un vācu valoda", "bioloģija un angļu valoda", "bioloģija un dabaszinātnes",
        "datorika un angļu valoda", "datorika un dabaszinātnes", "datorika un dizains un tehnoloģijas",
        "datorika un matemātika", "dizains un tehnoloģijas un angļu valoda", "dizains un tehnoloģijas un dabaszinātnes",
        "dizains un tehnoloģijas un datorika", "dizains un tehnoloģijas un matemātika", "fizika un bioloģija",
        "fizika un dabaszinātnes", "fizika un datorika", "fizika un matemātika", "latviešu valoda un literatūra",
        "mūzika", "sociālās zinības un vēsture", "veselības un fiziskās aktivitātes joma", "ģeogrāfija un bioloģija",
        "ģeogrāfija un dabaszinātnes", "ķīmija un bioloģija", "ķīmija un dabaszinātnes",
    )
]
_DU_MUSIC = [
    f"Mūzika ({kind})"
    for kind in ("akordeonists", "pianists", "pūšaminstrumentu mūziķis", "sitaminstrumentu mūziķis", "vijolnieks", "vokālists", "ģitārists")
]
_DU_LANGUAGES = [
    f"Valodu un kultūras studijas ({branch}), programma paredz arī vācu, zviedru, franču, spāņu, krievu, ķīniešu, "
    "latviešu valodas kā otrās valodas apguvi"
    for branch in ("anglistikas studijas", "latvistikas studijas", "rusistikas studijas")
]
_DU_CIVIL = [
    "Civilā drošība un aizsardzība (speciālists organizāciju vispārējā un kiberdrošībā)",
    "Civilā drošība un aizsardzība (speciālists penitenciārajā darbā)",
    "Civilā drošība un aizsardzība (speciālists policijas darbā)",
]

# (вуз, адрес программы в каталоге) -> латышские названия на портале.
# Названия сравниваются без учёта регистра (у DU в разные годы
# «Speciālists…» и «speciālists…»).
MANUAL: dict[tuple[str, str], list[str]] = {
    ("lu", "art-1"): ["Māksla"],
    # латышская подпрограмма «Asian Studies» с четырьмя модулями (четвёртая
    # партия, решение владельца 2026-10-25); 2024 — «apakšprogramma», код 22523
    ("lu", "asian-and-intercultural-studies"): [
        f"Āzijas studijas, {kind} {module}"
        for kind in ("modulis", "apakšprogramma")
        for module in ("Japānas studijas", "Korejas studijas", "Tuvo Austrumu studijas", "Ķīnas studijas")
    ],
    ("lu", "communication-science"): ["Komunikācijas zinātne"],
    ("lu", "computer-science"): ["Datorzinātnes"],
    ("lu", "computer-science-en"): ["Datorzinātnes (angļu valodā)"],
    ("lu", "cultural-and-social-anthropology-en"): ["Kultūras un sociālā antropoloģija (angļu val.)"],
    # на портале без пометки языка, но это англистика; правило по коду его
    # отложило — решает владелец
    ("lu", "english-european-languages-and-business-studies"): ["Anglistikas, Eiropas valodu un biznesa studijas"],
    ("lu", "environmental-science"): ["Vides zinātne"],
    ("lu", "geography"): ["Ģeogrāfija"],
    ("lu", "geoinformatics"): ["Ģeoinformātika"],
    ("lu", "geology"): ["Ģeoloģija"],
    ("lu", "history-and-archeology"): ["Vēsture un arheoloģija"],
    ("lu", "information-management"): ["Informācijas pārvaldība"],
    ("lu", "labour-protection-college"): ["Darba aizsardzība"],
    ("lu", "occupational-health-and-safety-at-work"): ["Arodveselība un drošība darbā"],
    ("lu", "optometry-lv"): ["Optometrija"],
    ("lu", "optometry-en"): ["Optometrija (angļu val.)"],
    ("lu", "philology-lv"): [
        "Filoloģija, apakšprogramma Franču filoloģija (latviešu un franču valodā)",
        "Filoloģija, apakšprogramma Klasiskā filoloģija",
        "Filoloģija, apakšprogramma Krievu filoloģija (latviešu un krievu valodā)",
        "Filoloģija, apakšprogramma Somugru studijas",
        "Filoloģija, apakšprogramma Vācu filoloģija (latviešu un vācu valodā)",
    ],
    ("lu", "philosophy"): ["Filozofija"],
    ("lu", "political-science"): ["Politikas zinātne"],
    ("lu", "preschool-teacher-college"): _PRESCHOOL,
    ("lu", "primary-education-teacher"): _PRIMARY,
    ("lu", "professional-bachelor-study-programme-teacher"): [
        "Angļu valodas skolotājs",
        "Dabaszinātņu skolotājs (bioloģijas vai fizikas, vai ģeogrāfijas, vai ķīmijas skolotājs)",
        "Datorikas skolotājs",
        "Dizaina un tehnoloģiju skolotājs",
        "Latviešu valodas un literatūras skolotājs",
        "Matemātikas skolotājs",
        "Sociālo zinību un vēstures skolotājs",
        "Sporta un veselības mācības skolotājs",
        "Vizuālās mākslas un kultūras skolotājs",
        "Vācu valodas skolotājs",
    ],
    ("lu", "programming-and-computer-network-administration-college"): ["Programmēšana un datortīklu administrēšana"],
    ("lu", "psychology-1"): ["Psiholoģija"],
    ("lu", "research-and-protection-of-cultural-and-environmental-heritage"): ["Kultūrvides mantojuma izpēte un aizsardzība"],
    ("lu", "social-work-in-riga-and-ul-branches"): [
        f"Sociālais darbs ({city})" for city in ("Bauska", "Cēsis", "Jēkabpils", "Kuldīga")
    ],
    ("lu", "sociology"): ["Socioloģija"],
    ("lu", "sports-coach-college"): _COACH,
    ("lu", "sports-technology-and-public-health"): ["Sports, tehnoloģijas un sabiedrības veselība"],
    ("lu", "theology-and-religious-studies"): ["Teoloģija un reliģijpētniecība"],
    # на странице lu.lv код 20221, на портале 20220 — название то же
    ("lu", "translate-to-anglu-pirmstiesas-izmeklesana"): ["Pirmstiesas izmeklēšana"],
    ("du", "psychology"): ["Psiholoģija"],
    # английская страница DU ведёт на латышскую с этим названием (четвёртая партия)
    ("du", "eastern-european-cultural-and-business-relations"): ["Austrumeiropas kultūras sakari un integrācijas procesi"],
    ("du", "history"): ["Vēsture"],
    ("du", "science-of-law"): ["Tiesību zinātne"],
    ("du", "strategic-risks-and-crisis-management"): ["Stratēģiskie riski un krīžu vadība"],
    ("du", "biology"): ["Bioloģija"],
    ("du", "chemistry"): ["Ķīmija (atjaunojamo resursu ķīmija vai praktiskā bioanalītika)"],
    ("du", "environmental-science-lv"): ["Vides zinātne"],
    ("du", "language-and-culture-studies"): _DU_LANGUAGES,
    ("du", "niid-19888"): ["Dizains (grafikas dizains)", "Dizains (grafikas dizainers)"],
    ("du", "niid-25729-lv"): ["Biznesa un finanšu procesi (finansists vai ekonomists)"],
    ("du", "niid-86"): ["Informācijas tehnoloģijas (programmēšanas inženieris)"],
    ("du", "niid-7050"): _DU_CIVIL,
    ("du", "niid-26827-lv"): _DU_MUSIC,
    ("du", "niid-94"): _DU_TEACHER,
    ("eka", "management-lv"): ["Vadības zinības"],
    ("eka", "culture-management"): ["Kultūras vadība"],
    ("eka", "business-economics-lv"): ["Biznesa ekonomika"],
    ("eka", "information-technologies-programming-lv"): ["Informācijas tehnoloģijas (Programmēšanas inženieris)"],
    ("eka", "international-trade-and-logistics"): ["Starptautiskie tirdzniecības darījumi un loģistika"],
    ("eka", "law"): ["Tiesību zinātne"],
    ("eka", "interior-design"): ["Interjera dizains"],
    ("eka", "accounting-and-finance-management"): ["Grāmatvedība un finanšu vadība"],
    ("eka", "marketing-lv"): ["Mārketings"],
    ("eka", "computer-game-design"): ["Datorspēļu dizains"],
    # РТУ: код из адреса программы совпадает (DCP, HCF), правило по коду
    # отложило связь только из-за языка — в каталоге программа английская,
    # портал язык не помечает (четвёртая партия, решение владельца 2026-10-25)
    # с 2026-10-25 программа в каталоге — запись английского реестра
    # (ENGLISH_REGISTRY_TWINS в sources/rtu_catalog.py)
    ("rtu", "finance-management-information-systems-173"): [
        "Finanšu pārvaldības informācijas sistēmas (kopīga studiju programma ar LU BA)",
        "Finanšu pārvaldības informācijas sistēmas (kopīga studiju programma ar BA)",
    ],
    ("rtu", "hcf-33000"): ["Tehniskā tulkošana un tekstveide"],
    ("rnu", "business-administration-bachelor"): ["Uzņēmējdarbības vadība"],
    # 2024 — «Tūrisma uzņēmējdarbības vadība», дальше — нынешнее название
    ("rnu", "business-administration-in-tourism-bachelor"): ["Uzņēmējdarbības vadība tūrismā", "Tūrisma uzņēmējdarbības vadība"],
    ("rnu", "information-systems-bachelor"): ["Informācijas sistēmas"],
    ("rnu", "psychology-bachelor"): ["Psiholoģija"],
    ("rnu", "tourism-service-organisation-college"): ["Tūrisma pakalpojumu organizēšana"],
}


def codes_for(names: list[str], portal: dict[str, set[str]]) -> list[str]:
    """Коды портала одного вуза, у которых есть название из списка.
    portal: код -> названия этого кода во все годы."""
    wanted = {name.casefold() for name in names}
    return sorted(code for code, code_names in portal.items() if wanted & {name.casefold() for name in code_names})


def missing_names(names: list[str], portal: dict[str, set[str]]) -> list[str]:
    """Названия из таблицы, которых на портале нет — опечатка в таблице."""
    present = {name.casefold() for code_names in portal.values() for name in code_names}
    return [name for name in names if name.casefold() not in present]


def _selftest() -> None:
    portal = {
        "D1261CIVK": {"Civilā drošība un aizsardzība (speciālists organizāciju vispārējā un kiberdrošībā)"},
        "D1261DROSS": {"Civilā drošība un aizsardzība (Speciālists organizāciju vispārējā un kiberdrošībā)"},
        "1B2026": {"Uzņēmējdarbības vadība"},
        "2B2026": {"Uzņēmējdarbības vadība tūrismā"},
    }
    assert codes_for(_DU_CIVIL[:1], portal) == ["D1261CIVK", "D1261DROSS"], "регистр не важен"
    assert codes_for(["Uzņēmējdarbības vadība"], portal) == ["1B2026"], "только точное название, не начало"
    assert missing_names(["Uzņēmējdarbības vadība", "Opečatka"], portal) == ["Opečatka"]
    assert len(_DU_TEACHER) == 24 and len(_DU_MUSIC) == 7
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
    universities = sorted({university for university, _ in MANUAL})

    stats = fetch_all(
        lambda: client.table("vupp_admission_stat")
        .select("id, university_slug, programme_code, programme_name, source_url, admission_year")
        .in_("university_slug", universities)
        .order("id")
    )
    portal: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    source: dict[tuple[str, str], tuple[int, str]] = {}
    for row in stats:
        key = (row["university_slug"], row["programme_code"])
        portal[row["university_slug"]][row["programme_code"]].add(row["programme_name"])
        # источник — страница самого свежего года
        if row["admission_year"] > source.get(key, (0, ""))[0]:
            source[key] = (row["admission_year"], row["source_url"])

    university_ids = {
        row["slug"]: row["id"] for row in execute(client.table("university").select("id, slug").in_("slug", universities)).data
    }
    catalog: dict[tuple[str, str], dict] = {}
    for slug in universities:
        for programme in fetch_all(
            lambda: client.table("programme").select("id, slug").eq("university_id", university_ids[slug]).order("id")
        ):
            catalog[(slug, programme["slug"])] = programme

    drafts: list[dict] = []
    problems: list[str] = []
    for (university, programme_slug), names in MANUAL.items():
        programme = catalog.get((university, programme_slug))
        if programme is None:
            problems.append(f"{university} {programme_slug}: программы нет в каталоге")
            continue
        for name in missing_names(names, portal[university]):
            problems.append(f"{university} {programme_slug}: на портале нет названия «{name}»")
        for code in codes_for(names, portal[university]):
            drafts.append(
                {
                    "programme_id": programme["id"],
                    "programme_slug": programme_slug,
                    "university_slug": university,
                    "programme_code": code,
                    "method": "manual",
                    "source_url": source[(university, code)][1],
                }
            )

    drafts, conflicts = drafts_without_conflicts(drafts)
    by_university: dict[str, int] = defaultdict(int)
    programmes: dict[str, set[str]] = defaultdict(set)
    for draft in drafts:
        by_university[draft["university_slug"]] += 1
        programmes[draft["university_slug"]].add(draft["programme_slug"])
    print(f"черновиков по таблице: {len(drafts)} {dict(by_university)}")
    print(f"программ: {sum(len(slugs) for slugs in programmes.values())} { {slug: len(s) for slug, s in programmes.items()} }")
    if problems:
        print("\nпроблемы таблицы — исправить до записи:")
        for line in problems:
            print(f"  {line}")
    if conflicts:
        print("\nкод у нескольких программ каталога — не связан:")
        for code, slugs in conflicts.items():
            print(f"  {code}: {slugs}")

    if "--apply" not in args:
        print("\nотчёт — в базу ничего не записано; запишет --apply")
        return
    if problems:
        raise SystemExit("в таблице есть проблемы — ничего не записано")
    records = [
        {key: draft[key] for key in ("programme_id", "university_slug", "programme_code", "method", "source_url")}
        for draft in drafts
    ]
    for start in range(0, len(records), 500):
        execute(
            client.table("programme_vupp_link").upsert(
                records[start : start + 500], on_conflict="programme_id,university_slug,programme_code", ignore_duplicates=True
            )
        )
    print(f"\nзаписано черновиков: {len(records)} (подтверждённые не тронуты)")


if __name__ == "__main__":
    main()
