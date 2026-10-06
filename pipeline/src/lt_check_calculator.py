"""Литва: случаи для сверки нашего расчёта балла с официальным калькулятором LAMA BPO.

Зачем. Литовские формулы не подтверждает человек (решение владельца
2026-10-05); взамен расчёт обязан совпасть с официальным калькулятором не
меньше чем на 30 наборах оценок, иначе не выпускается
(docs/PLAN-LITHUANIA-2027.md, раздел 4).

ПОЧЕМУ СВЕРКА РУЧНАЯ. Страница калькулятора считает балл на сервисе
bp.lamabpo.lt, а его robots.txt запрещает автоматическим клиентам всё
(«User-agent: * / Disallow: /», проверено 2026-10-06). Владелец отправку
разрешил, но запрет стоит на стороне LAMA BPO, и мы его соблюдаем: этот
скрипт сервису ничего не отправляет. Он только готовит 30 случаев с
выдуманными оценками; человек вводит их на странице официального
калькулятора и записывает ответ.

Что получается:
- docs/checks/lt-calculator-cases-<год>.json — случаи и поле official для
  ответа официального калькулятора (пока пусто — null);
- docs/checks/LT-CALCULATOR-CHECK-SHEET.md — лист для ввода с нашими
  ответами, его делает scripts/lt-check-sheet.mjs;
- тест src/lib/lt-score-official.test.ts сравнивает наш расчёт с каждым
  заполненным official — сверка остаётся в проекте и повторяется при каждом
  прогоне тестов.

Запуск:
  python src/lt_check_calculator.py --selftest
  python src/lt_check_calculator.py           # показать случаи
  python src/lt_check_calculator.py --save    # записать файл случаев (уже введённые ответы сохраняются)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from lt_formulas import COMPETITIONS_URL, Component, parse_formulas
from sources.lt_lamabpo import PROGRAMS_URL, parse_programs

CALCULATOR_PAGE = "https://lamabpo.lt/pirmosios-pakopos-ir-vientisosios-studijos/konkursinio-balo-skaiciuokle/"
ADMISSION_YEAR = 2026
OUTPUT = Path(__file__).resolve().parent.parent.parent / "docs" / "checks" / f"lt-calculator-cases-{ADMISSION_YEAR}.json"

# Наш ключ предмета -> как предмет назван на странице калькулятора. Два
# иностранных языка — английский и немецкий.
PAGE_NAMES = {
    "lithuanian": "Lietuvių kalba ir literatūra",
    "mathematics": "Matematika",
    "history": "Istorija",
    "biology": "Biologija",
    "chemistry": "Chemija",
    "physics": "Fizika",
    "geography": "Geografija",
    "informatics": "Informatika",
    "foreign_language": "Anglų kalba",
    "second_foreign_language": "Vokiečių kalba",
    "minority_language": "Mažumos gimtoji kalba",
    "economics": "Ekonomika ir verslumas",
    "philosophy": "Filosofija",
    "engineering": "Inžinerinės technologijos",
}
TWO_COURSE = {"lithuanian", "mathematics"}
NOT_SCHOOL_SUBJECTS = {"entrance_exam", "sport_achievements", "competence_assessment"}

# (номер формулы, чем случай отличается, оценки по составляющим 1–4, поправки)
# Поправки: course_b — предметы по общему курсу; drop — составляющие, для
# которых оценки нет; second_language — оценка второго иностранного языка;
# без поправок — «полный» набор по расширенному курсу.
CASES: list[dict] = [
    {"formula": "46", "note": "полный набор, расширенный курс", "scores": [68, 57, 71, 86]},
    {"formula": "46", "note": "математика по общему курсу (B)", "scores": [68, 57, 71, 86], "course_b": ["mathematics"]},
    {"formula": "46", "note": "литовский по общему курсу (B)", "scores": [68, 57, 71, 86], "course_b": ["lithuanian"]},
    {"formula": "46", "note": "нет первого предмета", "scores": [0, 57, 71, 86], "drop": [1]},
    {"formula": "46", "note": "два иностранных языка", "scores": [62, 79, 43, 94], "second_language": 91},
    {"formula": "46", "note": "все оценки 100", "scores": [100, 100, 100, 100]},
    {"formula": "46", "note": "все оценки 30 (нижняя граница)", "scores": [30, 30, 30, 30]},
    {"formula": "53", "note": "полный набор", "scores": [83, 47, 95, 61]},
    {"formula": "53", "note": "одна оценка в интервале 30–39", "scores": [83, 37, 95, 61]},
    {"formula": "25", "note": "полный набор", "scores": [55, 66, 77, 88]},
    {"formula": "8", "note": "математика B", "scores": [73, 49, 58, 64], "course_b": ["mathematics"]},
    {"formula": "49", "note": "полный набор", "scores": [91, 82, 73, 64]},
    {"formula": "52", "note": "полный набор", "scores": [76, 59, 84, 67]},
    {"formula": "52", "note": "нет второго предмета", "scores": [76, 0, 84, 67], "drop": [2]},
    {"formula": "3", "note": "литовский первым, один иностранный", "scores": [81, 63, 45, 72]},
    {"formula": "3", "note": "литовский первым, два иностранных", "scores": [81, 63, 45, 72], "second_language": 88},
    {"formula": "3", "note": "литовский первым, по общему курсу", "scores": [81, 63, 45, 72], "course_b": ["lithuanian"]},
    {"formula": "15", "note": "полный набор", "scores": [39, 51, 62, 74]},
    {"formula": "48", "note": "полный набор", "scores": [87, 93, 41, 56]},
    {"formula": "12", "note": "история первой", "scores": [69, 78, 87, 96]},
    {"formula": "47", "note": "полный набор", "scores": [44, 55, 66, 77]},
    {"formula": "4", "note": "полный набор", "scores": [92, 38, 65, 70]},
    {"formula": "10", "note": "литовский первым, история четвёртой", "scores": [58, 67, 76, 85]},
    {"formula": "21", "note": "полный набор", "scores": [97, 89, 54, 63]},
    {"formula": "43", "note": "нет третьего предмета", "scores": [75, 85, 0, 95], "drop": [3]},
    {"formula": "42", "note": "право: полный набор", "scores": [61, 72, 83, 94]},
    {"formula": "20", "note": "медицина: среднее химии и математики", "scores": [90, 80, 70, 50]},
    {"formula": "20", "note": "медицина: математика B в среднем", "scores": [90, 80, 70, 50], "course_b": ["mathematics"]},
    {"formula": "54", "note": "веса 0,4 · 0,1 · 0,3 · 0,2", "scores": [66, 99, 33, 77]},
    {"formula": "22", "note": "сельское хозяйство: веса 0,4 · 0,1 · 0,3 · 0,2", "scores": [52, 64, 78, 91]},
]


def exams_for(case: dict, components: list[Component]) -> dict[str, dict]:
    """Оценки по предметам для случая: в каждую составляющую — первый ещё не
    занятый предмет из её списка. У «среднего» — все перечисленные предметы:
    первый с оценкой составляющей, остальные на 20 ниже (чтобы среднее было
    видно в ответе)."""
    exams: dict[str, dict] = {}
    drop = set(case.get("drop", []))
    for component, score in zip(components, case["scores"]):
        if component.position in drop:
            continue
        if component.mode == "average":
            subjects = list(component.subjects)
        else:
            subjects = [next(s for s in component.subjects if s not in exams and s not in NOT_SCHOOL_SUBJECTS)]
        for index, subject in enumerate(subjects):
            if subject in exams:
                raise ValueError(f"случай «{case['note']}»: предмет {subject} нужен двум составляющим")
            exams[subject] = {"score": score - 20 * index}
    if "second_language" in case:
        exams["second_foreign_language"] = {"score": case["second_language"]}
    for subject in exams:
        if subject in TWO_COURSE:
            exams[subject]["course"] = "B" if subject in case.get("course_b", []) else "A"
    return exams


def prepare(entries: list[dict[str, str]], formulas: dict[str, list[Component]]) -> list[dict]:
    """Случаи с подобранной программой: для номера формулы берётся строка
    приёма с наименьшим номером — выбор воспроизводим."""
    by_formula: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        by_formula.setdefault(entry["p"], []).append(entry)
    prepared = []
    for number, case in enumerate(CASES, start=1):
        components = formulas[case["formula"]]
        entry = min(by_formula[case["formula"]], key=lambda e: int(e["e"]))
        exams = exams_for(case, components)
        prepared.append(
            {
                "id": number,
                "note": case["note"],
                "formula_number": case["formula"],
                "formula": [
                    {"position": c.position, "weight": c.weight, "mode": c.mode, "subjects": list(c.subjects)} for c in components
                ],
                "institution": entry["f"],
                "institution_name": entry["g"],
                "program_id": entry["e"],
                "program_name": entry["k"],
                "program_city": entry["m"],
                "program_form": " · ".join(part for part in (entry.get("o"), entry.get("n")) if part),
                "exams": {subject: {**exam, "page_name": PAGE_NAMES[subject]} for subject, exam in exams.items()},
                # ответ официального калькулятора; вписывает человек
                "official": None,
            }
        )
    return prepared


def keep_official(cases: list[dict], previous: list[dict]) -> list[dict]:
    """Перенести уже введённые ответы официального калькулятора в заново
    собранные случаи. Ответ переносится, только если случай не изменился:
    та же программа, та же формула и те же оценки."""

    def signature(case: dict) -> str:
        return json.dumps([case["program_id"], case["formula"], case["exams"]], sort_keys=True, ensure_ascii=False)

    known = {case["id"]: case for case in previous}
    for case in cases:
        before = known.get(case["id"])
        if before is not None and before.get("official") is not None and signature(before) == signature(case):
            case["official"] = before["official"]
    return cases


def _selftest() -> None:
    formula = [
        Component(1, 0.4, "one_of", ("mathematics",)),
        Component(2, 0.2, "one_of", ("history", "foreign_language")),
        Component(3, 0.2, "one_of", ("history", "biology", "foreign_language")),
        Component(4, 0.2, "one_of", ("lithuanian",)),
    ]
    exams = exams_for({"note": "x", "scores": [68, 57, 71, 86]}, formula)
    assert exams == {
        "mathematics": {"score": 68, "course": "A"}, "history": {"score": 57},
        "biology": {"score": 71}, "lithuanian": {"score": 86, "course": "A"},
    }, exams
    exams = exams_for({"note": "x", "scores": [68, 57, 71, 86], "course_b": ["mathematics"], "drop": [2], "second_language": 90}, formula)
    assert exams["mathematics"]["course"] == "B" and "biology" not in exams and exams["history"] == {"score": 71}, exams
    assert exams["second_foreign_language"] == {"score": 90}

    medicine = [Component(1, 0.4, "one_of", ("biology",)), Component(2, 0.2, "average", ("chemistry", "mathematics"))]
    exams = exams_for({"note": "x", "scores": [90, 80]}, medicine)
    assert exams == {"biology": {"score": 90}, "chemistry": {"score": 80}, "mathematics": {"score": 60, "course": "A"}}, exams

    assert len(CASES) == 30, len(CASES)
    for case in CASES:
        assert len(case["scores"]) == 4 and case["formula"].isdigit(), case
        for position in range(1, 5):
            score = case["scores"][position - 1]
            assert position in case.get("drop", []) or 30 <= score <= 100, case

    extra = {"g": "Vardas", "m": "Vilnius", "o": "Nuolatinė (NL)", "n": "Dieninė"}
    entries = [{"e": "9", "p": "46", "f": "VU", "k": "Ekonomika", **extra}, {"e": "5", "p": "46", "f": "KTU", "k": "Vadyba", **extra}]
    formulas = {case["formula"]: formula for case in CASES}
    entries += [{"e": str(100 + i), "p": number, "f": "X", "k": "y", **extra} for i, number in enumerate(sorted(formulas)) if number != "46"]
    prepared = prepare(entries, formulas)
    assert len(prepared) == 30 and prepared[0]["program_id"] == "5" and prepared[0]["institution"] == "KTU"
    assert prepared[0]["official"] is None and prepared[0]["program_form"] == "Nuolatinė (NL) · Dieninė"
    assert prepared[0]["exams"]["mathematics"] == {"score": 68, "course": "A", "page_name": "Matematika"}
    json.dumps(prepared)

    # уже введённый ответ не теряется, пока случай тот же; изменился случай — ответ сбрасывается
    old = [{**prepared[0], "official": 6.82}, {**prepared[1], "official": 5.5, "exams": {"mathematics": {"score": 1}}}]
    merged = keep_official(json.loads(json.dumps(prepared)), old)
    assert merged[0]["official"] == 6.82 and merged[1]["official"] is None and merged[2]["official"] is None
    print("selftest: OK")


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright

    import polite

    load_dotenv()
    polite.install()
    # Читаются только открытые файлы калькулятора на lamabpo.lt; сервису
    # расчёта (bp.lamabpo.lt) этот скрипт ничего не отправляет — см. шапку.
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        entries = parse_programs(page.goto(PROGRAMS_URL, timeout=45000).text())
        formulas = parse_formulas(page.goto(COMPETITIONS_URL, timeout=45000).text())
        browser.close()
    cases = prepare(entries, formulas)

    for case in cases:
        print(f"[{case['id']:2}] формула {case['formula_number']:>2} · {case['institution']} №{case['program_id']} {case['program_name'][:32]} · {case['note']}")
        print("     ", {s: (e["score"], e.get("course", "")) for s, e in case["exams"].items()})

    if "--save" not in args:
        print(f"\nслучаев: {len(cases)}. Файл не записан (добавьте --save).")
        return

    # Запись владельца о проведённой сверке (owner_check) делается руками и
    # при пересборке случаев не теряется.
    owner_check = None
    if OUTPUT.exists():
        previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
        cases = keep_official(cases, previous["cases"])
        owner_check = previous.get("owner_check")
    OUTPUT.write_text(
        json.dumps(
            {
                "admission_year": ADMISSION_YEAR,
                "calculator_page": CALCULATOR_PAGE,
                "prepared_at": datetime.now(timezone.utc).isoformat(),
                "note": "Оценки выдуманы; персональных данных нет. Поле official вписывает человек — см. pipeline/src/lt_check_calculator.py.",
                "owner_check": owner_check,
                "cases": cases,
            },
            ensure_ascii=False,
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    filled = sum(1 for case in cases if case["official"] is not None)
    print(f"сохранено: {OUTPUT} | ответов официального калькулятора вписано: {filled} из {len(cases)}")


if __name__ == "__main__":
    main()
