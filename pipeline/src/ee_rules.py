"""Эстония: правила конкурса из текста условий SAIS и страницы программы
вуза (docs/PLAN-ESTONIA.md, раздел 9).

Здесь только разбор текста — без сети и базы; читает и пишет
ee_load_rules.py. Разбираются два вуза, у каждого своя модель:

Тартуский университет (ut) — балл с весами. В SAIS список составляющих:

    Eesti keele või eesti keele teise keelena riigieksam 40%
    Matemaatika riigieksam 60%

бывают варианты через строку «VÕI» (засчитывается лучший) и «Üks eksam
valikust 25%» с пронумерованными экзаменами на выбор. Пороги — на странице
программы ut.ee: «Kandideerimiseks peab punktisumma olema vähemalt 66»,
«Vastuvõtu tagab 80-punktise lävendi ületamine»; там же надбавка за
широкую математику. Надбавка за медаль — на общей странице ut.ee о подсчёте
баллов.

    {"model": "weighted",
     "variants": [[{"exam": "estonian", "weight": 40}, {"exam": "math", "weight": 60}],
                  [{"other": "Programmeerimise sisseastumiseksam", "weight": 100}]],
     "apply_min": 66, "guarantee_min": 80,
     "wide_math_bonus": 16, "medal_bonus": 3,
     "requirements": {"english": "B2"}}

TalTech (taltech) — пороги, балла нет: минимумы по госэкзаменам «для
подачи» и «гарантирует место», отдельно для эстонского как второго языка,
и число мест. У части программ только второй порог: ниже него места нет
(ranking: false). Как считается рейтинг, TalTech не публикует.

    {"model": "thresholds",
     "apply": {"math": 35, "estonian": 35, "estonian_second": 45} | None,
     "guarantee": {"math": 50, "estonian": 50, "estonian_second": 60, "english": "B2"},
     "places": 60 | None, "ranking": true, "wide_math": true}

Правило: строка, которую разборщик не узнал, делает правило пустым (None).
Лучше не показать условия, чем показать неточные.
"""

from __future__ import annotations

import itertools
import re

# ---------------------------------------------------------------- общее


def lines_of(text: str) -> list[str]:
    """Строки текста без пустых, с одиночными пробелами."""
    result = []
    for line in (text or "").replace("\xa0", " ").splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            result.append(line)
    return result


# ---------------------------------------------------------------- Тартуский университет

_ESTONIAN = re.compile(r"eesti keele? või eesti keele? teise keelena riigieksam", re.IGNORECASE)
_MATH = re.compile(r"matemaatika riigieksam", re.IGNORECASE)
_COMPONENT = re.compile(r"^(.+?):?\s*(\d+)\s*%$")
_OPTION = re.compile(r"^\d+\s*[.)]\s*(.+?);?$")
_ENGLISH = re.compile(r"^Nõutav on inglise keele oskus vähemalt tasemel (B2|C1)\.?$", re.IGNORECASE)
_CHOICE = "üks eksam valikust"


def part_of(name: str) -> dict:
    """Название составляющей -> {"exam": ...} или {"other": название}."""
    name = name.strip().rstrip(";").strip()
    if _ESTONIAN.fullmatch(name):
        return {"exam": "estonian"}
    if _MATH.fullmatch(name):
        return {"exam": "math"}
    return {"other": name[:1].upper() + name[1:]}


def parse_ut_criteria(text: str) -> dict | None:
    """Составляющие балла и требования из текста SAIS; None — текст не узнан."""
    branches: list[list[tuple[int, list[dict]]]] = [[]]
    requirements: dict = {}
    choice: tuple[int, list[dict]] | None = None
    for line in lines_of(text):
        if line.upper() == "VÕI":
            branches.append([])
            choice = None
            continue
        if line.lower() == "riigieksamid":
            continue
        english = _ENGLISH.match(line)
        if english:
            requirements["english"] = english.group(1).upper()
            continue
        option = _OPTION.match(line)
        if option and choice is not None:
            choice[1].append(part_of(option.group(1)))
            continue
        component = _COMPONENT.match(line)
        if not component:
            return None
        name, weight = component.group(1).strip(), int(component.group(2))
        if name.lower().rstrip(":") == _CHOICE:
            choice = (weight, [])
            branches[-1].append(choice)
        else:
            choice = None
            # «Matemaatika riigieksam VÕI erialakatse 50%» — выбор внутри строки
            options = [part_of(piece) for piece in re.split(r"\s+VÕI\s+", name)]
            branches[-1].append((weight, options))

    variants: list[list[dict]] = []
    for branch in branches:
        if not branch or any(not options for _, options in branch):
            return None
        for combination in itertools.product(*[options for _, options in branch]):
            variant = [{**part, "weight": weight} for (weight, _), part in zip(branch, combination)]
            if sum(item["weight"] for item in variant) != 100:
                return None
            variants.append(variant)
    return {"variants": variants, "requirements": requirements}


_GUARANTEE = re.compile(r"Vastuvõtu tagab (\d+)[- ]punktise lävendi ületamine")
_APPLY = re.compile(r"Kandideerimiseks peab punktisumma olema vähemalt (\d+)")
_WIDE_MATH = re.compile(r"lisame laia matemaatika riigieksami tulemusele (\d+) punkti")
_MEDAL = re.compile(r"Lisapunktid medali ja kiitusega lõpetanule\s*(\d+) lisapunkti")


def single(values: list[str]) -> int | None:
    """Одно значение на странице — число; ни одного или несколько разных —
    None: на странице несколько форм обучения, и чьё это значение, не ясно."""
    distinct = set(values)
    return int(distinct.pop()) if len(distinct) == 1 else None


def parse_ut_page(text: str) -> dict:
    """Пороги и надбавка за широкую математику со страницы программы ut.ee
    (текст без разметки, в одну строку или в несколько — всё равно)."""
    flat = re.sub(r"\s+", " ", (text or "").replace("\xa0", " "))
    return {
        "apply_min": single(_APPLY.findall(flat)),
        "guarantee_min": single(_GUARANTEE.findall(flat)),
        "wide_math_bonus": single(_WIDE_MATH.findall(flat)),
    }


def parse_ut_medal(text: str) -> int | None:
    """Надбавка за медаль с общей страницы ut.ee «Punktisumma ja pingeread»."""
    flat = re.sub(r"\s+", " ", (text or "").replace("\xa0", " "))
    return single(_MEDAL.findall(flat))


def ut_rule(criteria: str, page: dict | None, medal_bonus: int | None) -> dict | None:
    """Правило Тартуского университета. page — результат parse_ut_page или
    None, если страница программы не прочитана: тогда порогов нет, а
    составляющие из SAIS остаются."""
    parsed = parse_ut_criteria(criteria)
    if parsed is None:
        return None
    page = page or {"apply_min": None, "guarantee_min": None, "wide_math_bonus": None}
    return {
        "model": "weighted",
        "variants": parsed["variants"],
        "apply_min": page["apply_min"],
        "guarantee_min": page["guarantee_min"],
        "wide_math_bonus": page["wide_math_bonus"],
        "medal_bonus": medal_bonus,
        "requirements": parsed["requirements"],
    }


# ---------------------------------------------------------------- TalTech

_SET = (
    r"\(laia\) matemaatika riigieksam vähemalt (\d+),? (?:ja )?eesti keele oma vähemalt (\d+) punkti "
    r"\(eesti keel teise keelena vähemalt (\d+) punkti\)(?:,? ja inglise keele tase vähemalt (B2|C1))?\.?"
)
_TT_APPLY = re.compile(r"^Kandideerimiseks nõutavad tulemused: " + _SET + r"$")
_TT_GUARANTEE = re.compile(r"^Õppekoha tagav(?:ad tulemused| lävend): " + _SET + r"$")
_TT_PLACES = re.compile(r"^Piirarv: (\d+)$")
_TT_ONLY_THRESHOLD = re.compile(r"^(Tegemist on )?ainult lävendipõhise vastuvõtuga", re.IGNORECASE)
_TT_EXPLANATIONS = [
    re.compile(
        r"^\(Kui õppekoha tagava tulemusega kandidaate on rohkem kui (\d+), saavad kõik õppekoha\. "
        r"Kui vähem, siis hakatakse pakkuma kohti pingerea alusel kandideerimiseks nõutava tulemuse "
        r"ületanud kandidaatidele\)$"
    ),
    re.compile(r"^Kõik selliste tulemustega kandidaadid saavad õppekoha, allapoole neid tulemusi kedagi ei võeta\.$"),
    # место учёбы — оно уже есть в условиях конкурса
    re.compile(r"^Õppetöö toimub [^.]+\.$"),
]


def threshold_set(match: re.Match) -> dict:
    result = {
        "math": int(match.group(1)),
        "estonian": int(match.group(2)),
        "estonian_second": int(match.group(3)),
    }
    if match.group(4):
        result["english"] = match.group(4)
    return result


def taltech_rule(criteria: str) -> dict | None:
    """Пороги TalTech; None — текст не узнан или в нём есть то, чего
    разборщик не понимает (тест, собеседование, средняя оценка)."""
    apply = guarantee = places = None
    only_threshold = False
    for line in lines_of(criteria):
        if _TT_ONLY_THRESHOLD.match(line):
            only_threshold = True
            continue
        if (match := _TT_APPLY.match(line)) and apply is None:
            apply = threshold_set(match)
        elif (match := _TT_GUARANTEE.match(line)) and guarantee is None:
            guarantee = threshold_set(match)
        elif (match := _TT_PLACES.match(line)) and places is None:
            places = int(match.group(1))
        elif any(pattern.match(line) for pattern in _TT_EXPLANATIONS):
            explained = _TT_EXPLANATIONS[0].match(line)
            # число мест в пояснении должно совпасть с «Piirarv»
            if explained and places is not None and int(explained.group(1)) != places:
                return None
        else:
            return None
    if guarantee is None:
        return None
    if only_threshold:
        if apply is not None or places is not None:
            return None
    elif apply is None or places is None:
        return None
    return {
        "model": "thresholds",
        "apply": apply,
        "guarantee": guarantee,
        "places": places,
        "ranking": not only_threshold,
        "wide_math": True,
    }


# ---------------------------------------------------------------- самотест


def _selftest() -> None:
    estonian, math = {"exam": "estonian"}, {"exam": "math"}

    informatics = ut_rule(
        "Riigieksamid\neesti keele või eesti keele teise keelena riigieksam 40%\nmatemaatika riigieksam 60%\nVÕI\n"
        "Programmeerimise sisseastumiseksam 100%",
        parse_ut_page(
            "lisame laia matemaatika riigieksami tulemusele 16 punkti, kuid … Vastuvõtu tagab 80-punktise\n"
            "lävendi ületamine. Ülejäänud … Kandideerimiseks peab punktisumma olema vähemalt 66."
        ),
        3,
    )
    assert informatics == {
        "model": "weighted",
        "variants": [
            [{**estonian, "weight": 40}, {**math, "weight": 60}],
            [{"other": "Programmeerimise sisseastumiseksam", "weight": 100}],
        ],
        "apply_min": 66,
        "guarantee_min": 80,
        "wide_math_bonus": 16,
        "medal_bonus": 3,
        "requirements": {},
    }, informatics

    # «Üks eksam valikust» — варианты по числу экзаменов на выбор
    psychology = parse_ut_criteria(
        "Eesti keele või eesti keele teise keelena riigieksam 25%\nÜks eksam valikust 25%\n"
        "1. matemaatika riigieksam;\n2. akadeemiline test\nErialakatse 50%"
    )
    assert psychology["variants"] == [
        [{**estonian, "weight": 25}, {**math, "weight": 25}, {"other": "Erialakatse", "weight": 50}],
        [{**estonian, "weight": 25}, {"other": "Akadeemiline test", "weight": 25}, {"other": "Erialakatse", "weight": 50}],
    ], psychology
    # двоеточие после «valikust», скобки в номерах, «eesti keel» без «e»
    philosophy = parse_ut_criteria(
        "Erialakatse 70%\nÜks eksam valikust: 30%\n1) matemaatika riigieksam;\n"
        "2) eesti keele või eesti keel teise keelena riigieksam"
    )
    assert [variant[1] for variant in philosophy["variants"]] == [{**math, "weight": 30}, {**estonian, "weight": 30}]
    # выбор внутри строки
    teaching = parse_ut_criteria("Eesti keele või eesti keele teise keelena riigieksam 50%\nMatemaatika riigieksam VÕI erialakatse 50%")
    assert [variant[1] for variant in teaching["variants"]] == [{**math, "weight": 50}, {"other": "Erialakatse", "weight": 50}]
    # требование английского — не составляющая балла
    business = parse_ut_criteria("Motivatsioonikiri 60%\nMatemaatika sisseastumiseksam 40%\nNõutav on inglise keele oskus vähemalt tasemel B2.")
    assert business["requirements"] == {"english": "B2"} and len(business["variants"]) == 1
    # доли не дают 100 или незнакомая строка — правила нет
    assert parse_ut_criteria("Matemaatika riigieksam 60%\nErialakatse 30%") is None
    assert parse_ut_criteria("Matemaatika riigieksam 60%\nEesti keele riigieksam 40%\nLisainfo kodulehel") is None
    assert parse_ut_criteria("") is None
    assert parse_ut_criteria("Erialakatse 100%\nVÕI") is None
    # страница программы не прочитана — составляющие остаются, порогов нет
    bare = ut_rule("Erialakatse 100%", None, 3)
    assert (bare["apply_min"], bare["guarantee_min"], bare["wide_math_bonus"]) == (None, None, None)
    # два разных порога на одной странице (две формы обучения) — не берём
    assert parse_ut_page("Vastuvõtu tagab 93-punktise lävendi ületamine. … Vastuvõtu tagab 85-punktise lävendi ületamine.")["guarantee_min"] is None
    assert parse_ut_medal("Lisapunktid medali ja kiitusega lõpetanule\n3 lisapunkti\nantakse") == 3
    assert parse_ut_medal("") is None

    logistics = taltech_rule(
        "Kandideerimiseks nõutavad tulemused: (laia) matemaatika riigieksam vähemalt 35 ja eesti keele oma vähemalt 35 "
        "punkti (eesti keel teise keelena vähemalt 45 punkti).\xa0\n"
        "Õppekoha tagavad tulemused: (laia) matemaatika riigieksam vähemalt 60 ja eesti keele oma vähemalt 50 punkti "
        "(eesti keel teise keelena vähemalt 60 punkti).\n"
        "Piirarv: 60\n(Kui õppekoha tagava tulemusega kandidaate on rohkem kui 60, saavad kõik õppekoha. Kui vähem, siis "
        "hakatakse pakkuma kohti pingerea alusel kandideerimiseks nõutava tulemuse ületanud kandidaatidele)"
    )
    assert logistics == {
        "model": "thresholds",
        "apply": {"math": 35, "estonian": 35, "estonian_second": 45},
        "guarantee": {"math": 60, "estonian": 50, "estonian_second": 60},
        "places": 60,
        "ranking": True,
        "wide_math": True,
    }, logistics
    # английский в порогах, запятая вместо «ja»
    public = taltech_rule(
        "Kandideerimiseks nõutavad tulemused: (laia) matemaatika riigieksam vähemalt 55, eesti keele oma vähemalt 55 "
        "punkti (eesti keel teise keelena vähemalt 75 punkti) ja inglise keele tase vähemalt B2.\n"
        "Õppekoha tagavad tulemused: (laia) matemaatika riigieksam vähemalt 60, eesti keele oma vähemalt 70 punkti "
        "(eesti keel teise keelena vähemalt 90 punkti) ja inglise keele tase vähemalt C1.\nPiirarv: 30"
    )
    assert public["apply"]["english"] == "B2" and public["guarantee"]["english"] == "C1"
    # только порог
    hardware = taltech_rule(
        "Tegemist on ainult lävendipõhise vastuvõtuga, pingerea alusel vastuvõttu ei toimu.\n"
        "Õppekoha tagavad tulemused: (laia) matemaatika riigieksam vähemalt 50 ja eesti keele oma vähemalt 50 punkti "
        "(eesti keel teise keelena vähemalt 60 punkti).\n"
        "Kõik selliste tulemustega kandidaadid saavad õppekoha, allapoole neid tulemusi kedagi ei võeta."
    )
    assert hardware["ranking"] is False and hardware["apply"] is None and hardware["places"] is None
    # число мест в пояснении не совпало — правила нет
    assert taltech_rule(
        "Kandideerimiseks nõutavad tulemused: (laia) matemaatika riigieksam vähemalt 35 ja eesti keele oma vähemalt 35 "
        "punkti (eesti keel teise keelena vähemalt 45 punkti).\n"
        "Õppekoha tagavad tulemused: (laia) matemaatika riigieksam vähemalt 60 ja eesti keele oma vähemalt 50 punkti "
        "(eesti keel teise keelena vähemalt 60 punkti).\nPiirarv: 60\n(Kui õppekoha tagava tulemusega kandidaate on "
        "rohkem kui 61, saavad kõik õppekoha. Kui vähem, siis hakatakse pakkuma kohti pingerea alusel "
        "kandideerimiseks nõutava tulemuse ületanud kandidaatidele)"
    ) is None
    # тест, собеседование, «Piirarv» с пояснением — правила нет
    assert taltech_rule("Ainult lävendipõhise vastuvõtuga kava. Õppekoha pakkumise saavad kandidaadid, kes sooritavad erialaste teadmiste testi vähemalt 70 punktile.") is None
    assert taltech_rule("Piirarv: 145, sh Tallinnas kuni 100") is None
    assert taltech_rule("") is None
    print("ee_rules selftest: ok")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    _selftest()
