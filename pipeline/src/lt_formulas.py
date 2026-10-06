"""Литва: состав конкурсного балла по каждой формуле общего приёма.

Источник — открытый файл официального калькулятора LAMA BPO
(competitions.js, таблица `formulas`). Одна формула — до четырёх
составляющих; у каждой вес и предмет или список предметов на выбор. Номер
формулы стоит у каждой записи общего приёма (поле `p` в programs_lt.js).

Здесь только разбор текста в данные; в базу этот модуль не пишет. Запись
появится отдельным шагом, вместе с миграцией (фаза 3 литовского плана).

Что текст составляющей значит (проверено по документам 2026 года, см.
docs/checks/LT-PHASE3-SCORE-RULES.md):
- «A arba B, arba C» — один предмет из списка, какой выгоднее поступающему;
- «A / B / C»       — то же, длинный список для третьей составляющей;
- «A ir B»          — среднее двух предметов (медицина и одонтология);
- «stojamasis egzaminas», «sporto pasiekimai», «kompetencijų įvertinimas» —
  не школьный предмет, а вступительный экзамен, спортивные достижения или
  оценка профессиональной квалификации.

Любой незнакомый текст — ошибка, а не «пропустим»: так изменение файла на
следующий год не пройдёт молча.

Запуск:
  python src/lt_formulas.py --selftest   # разбор на встроенных примерах, без сети
  python src/lt_formulas.py              # прочитать файл с сайта и напечатать сводку
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass

from sources.lt_lamabpo import parse_array

COMPETITIONS_URL = "https://lamabpo.lt/wp-content/plugins/simple-score-calculator/competitions.js"

# Название в файле -> ключ предмета. Ключи английские, как у латвийских
# предметов; подписи для посетителя — в словарях сайта.
SUBJECTS = {
    "lietuvių kalba ir literatūra": "lithuanian",
    "matematika": "mathematics",
    "istorija": "history",
    "biologija": "biology",
    "chemija": "chemistry",
    "fizika": "physics",
    "geografija": "geography",
    "informatika (informacinės technologijos)": "informatics",
    "užsienio kalba": "foreign_language",
    "antroji užsienio kalba": "second_foreign_language",
    "mažumos gimtoji kalba": "minority_language",
    "ekonomika ir verslumas": "economics",
    "filosofija": "philosophy",
    "inžinerinės technologijos": "engineering",
    # не школьные предметы
    "stojamasis egzaminas": "entrance_exam",
    "sporto pasiekimai": "sport_achievements",
    "kompetencijų įvertinimas": "competence_assessment",
}

# Длинные названия раньше коротких: «antroji užsienio kalba» содержит
# «užsienio kalba», а «ekonomika ir verslumas» — слово «ir».
_NAMES = sorted(SUBJECTS, key=len, reverse=True)


@dataclass(frozen=True)
class Component:
    position: int  # 1–4
    weight: float
    mode: str  # 'one_of' — один предмет из списка; 'average' — среднее всех перечисленных
    subjects: tuple[str, ...]


def parse_component_text(text: str) -> tuple[str, tuple[str, ...]]:
    """«chemija arba matematika, arba fizika» -> ('one_of', ('chemistry', 'mathematics', 'physics'))."""
    rest = text.strip()
    found: list[tuple[int, str]] = []
    for name in _NAMES:
        while True:
            at = rest.find(name)
            if at < 0:
                break
            found.append((at, SUBJECTS[name]))
            rest = rest[:at] + "\x00" * len(name) + rest[at + len(name):]
    glue = re.sub(r"\x00+", "@", rest)
    separators = [part.strip() for part in glue.split("@")]
    # между предметами допустимы только известные связки
    unknown = [part for part in separators if part not in ("", "arba", ", arba", ",", "/", "ir")]
    if unknown or not found:
        raise ValueError(f"незнакомый текст составляющей: «{text}» (не разобрано: {unknown})")
    average = "ir" in separators
    if average and any(part in ("arba", ", arba", "/") for part in separators):
        raise ValueError(f"в составляющей смешаны «ir» и «arba»: «{text}»")
    subjects = tuple(key for _, key in sorted(found))
    if len(set(subjects)) != len(subjects):
        raise ValueError(f"предмет назван дважды: «{text}»")
    return ("average" if average else "one_of"), subjects


def parse_formulas(js_text: str) -> dict[str, list[Component]]:
    """Номер формулы -> её составляющие по порядку. Пустые строки файла
    (у программ искусств три из четырёх составляющих пусты) пропускаются."""
    result: dict[str, list[Component]] = {}
    for row in parse_array(js_text, "formulas"):
        if not row.get("p"):
            continue
        mode, subjects = parse_component_text(row["p"])
        weight = float("0" + row["k"]) if row["k"].startswith(".") else float(row["k"])
        result.setdefault(row["i"], []).append(Component(int(row["n"]), weight, mode, subjects))
    for number, components in result.items():
        components.sort(key=lambda component: component.position)
        total = round(sum(component.weight for component in components), 6)
        if total != 1.0:
            raise ValueError(f"формула {number}: веса дают {total}, а не 1")
        positions = [component.position for component in components]
        if len(set(positions)) != len(positions):
            raise ValueError(f"формула {number}: повтор номера составляющей {positions}")
    return result


def _selftest() -> None:
    assert parse_component_text("matematika") == ("one_of", ("mathematics",))
    assert parse_component_text("lietuvių kalba ir literatūra") == ("one_of", ("lithuanian",)), "«ir» внутри названия — не среднее"
    assert parse_component_text("chemija ir matematika") == ("average", ("chemistry", "mathematics"))
    assert parse_component_text("chemija, arba matematika arba fizika") == ("one_of", ("chemistry", "mathematics", "physics"))
    mode, subjects = parse_component_text(
        "istorija arba informatika (informacinės technologijos), arba geografija, arba užsienio kalba, arba ekonomika ir verslumas"
    )
    assert mode == "one_of" and subjects == ("history", "informatics", "geography", "foreign_language", "economics"), subjects
    mode, subjects = parse_component_text(
        "biologija / chemija / antroji užsienio kalba / mažumos gimtoji kalba / ekonomika ir verslumas / kompetencijų įvertinimas"
    )
    assert subjects == ("biology", "chemistry", "second_foreign_language", "minority_language", "economics", "competence_assessment"), subjects
    for bad in ("muzika", "matematika arba muzika", "matematika, ir fizika arba chemija", ""):
        try:
            parse_component_text(bad)
        except ValueError:
            continue
        raise AssertionError(f"незнакомый текст должен быть ошибкой: {bad!r}")

    js = (
        "const competitions = [{i:'1',p:'x',g:'y'}];\n"
        "const formulas = [{i:'46',p:'matematika',k:'.4',n:'1'},"
        "{i:'46',p:'istorija arba geografija',k:'.2',n:'2'},"
        "{i:'46',p:'biologija / chemija',k:'.2',n:'3'},"
        "{i:'46',p:'lietuvių kalba ir literatūra',k:'.2',n:'4'},"
        "{i:'5',p:'stojamasis egzaminas',k:'1',n:'1'},{i:'5',p:'',k:'',n:'2'},{i:'5',p:'',k:'',n:'3'},{i:'5',p:'',k:'',n:'4'}];\n"
        "const exams = [];"
    )
    formulas = parse_formulas(js)
    assert sorted(formulas) == ["46", "5"], sorted(formulas)
    assert [c.weight for c in formulas["46"]] == [0.4, 0.2, 0.2, 0.2]
    assert formulas["46"][1] == Component(2, 0.2, "one_of", ("history", "geography"))
    assert formulas["5"] == [Component(1, 1.0, "one_of", ("entrance_exam",))]
    try:
        parse_formulas("const formulas = [{i:'9',p:'matematika',k:'.4',n:'1'}];")
    except ValueError:
        pass
    else:
        raise AssertionError("веса не дают 1 — должно быть ошибкой")
    print("selftest: OK")


def _report(formulas: dict[str, list[Component]]) -> None:
    from collections import Counter

    print(f"формул: {len(formulas)}")
    print("наборы весов:", Counter(tuple(c.weight for c in components) for components in formulas.values()).most_common())
    print("первая составляющая:", Counter(components[0].subjects for components in formulas.values()).most_common())
    print("среднее двух предметов:", [(n, c.position, c.subjects) for n, cs in formulas.items() for c in cs if c.mode == "average"])
    for number in sorted(formulas, key=int)[:4]:
        print(f"  формула {number}:")
        for component in formulas[number]:
            print(f"    {component.position}. вес {component.weight} · {component.mode} · {', '.join(component.subjects)}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        from dotenv import load_dotenv
        from playwright.sync_api import sync_playwright

        import polite

        load_dotenv()
        polite.install()
        sys.stdout.reconfigure(encoding="utf-8")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            text = page.goto(COMPETITIONS_URL, timeout=45000).text()
            browser.close()
        _report(parse_formulas(text))
