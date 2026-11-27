"""Эстония, TalTech: условия приёма следующего учебного года из решения сената
(docs/PLAN-ESTONIA.md, журнал 2026-11-27).

Правило в ee_admission.rule разобрано со страницы последнего конкурса SAIS —
это приём прошлого лета. Условия следующего года TalTech утверждает осенью
решением сената («I ja II kõrgharidusastme üliõpilaste 2027/2028. õa
vastuvõtutingimused», 24.11.2026 № 40), а конкурсы SAIS появляются весной.
Решение владельца 2026-11-27: показывать условия следующего года уже сейчас,
рядом с прошлым приёмом. Здесь читаются приложения решения — Excel-файлы со
страницы решения на oigusaktid.taltech.ee — и пишется ee_next_rule:
  - приложение 1 (бакалавриат, интегрированное и прикладное высшее) — пороги
    госэкзаменов и места, правило «thresholds»;
  - приложение 2 (магистратура, с 2026-11-27) — требования к образованию,
    испытания и порог по шкале 0–10 свободным текстом по-эстонски; они
    записываются как есть, правилом «text», без перевода и разбора смысла.

Разбор приложения 1 строгий, как у ee_rules.taltech_rule: правило записывается, только
если у программы одни госэкзамены (математика, эстонский, английский), а
каждая строка с порогами узнана. Тест, собеседование, средняя оценка, две
формы обучения — правила нет, и сайт его не показывает.

Программа привязывается к каталогу по эстонскому названию и уровню.
Двойники (версии одного учебного плана, src/lib/ee-variants.ts) получают
одно правило: в решении у названия одна строка.

Excel читается своими тридцатью строками (zipfile + xml): openpyxl ради
одного файла в год не нужен.

Раз в год, когда сенат утвердит условия следующего года (в 2025 году —
21.10, в 2026 — 24.11): проверить, что адрес страницы решения не сменился
(DECISION_URL), и запустить с --apply. В расписание не ставится.

Таблица — миграция 20261127130000_ee_next_rule.sql.

Запуск:
  python src/ee_load_taltech_conditions.py --selftest
  python src/ee_load_taltech_conditions.py            # разобрать и показать, без записи
  python src/ee_load_taltech_conditions.py --apply
"""

from __future__ import annotations

import io
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from urllib.parse import urljoin

DECISION_URL = "https://oigusaktid.taltech.ee/i-ja-ii-korgharidusastme-uliopilaste-oppeaasta-vastuvotutingimused/"
LEVELS = {"B": "bachelor", "I": "integrated", "R": "college"}

# ---------------------------------------------------------------- Excel

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _column(reference: str) -> str:
    return re.sub(r"\d+", "", reference)


def xlsx_rows(data: bytes) -> list[dict[str, str]]:
    """Первый лист Excel-файла: строка -> {буква столбца: текст}. Пустые
    ячейки пропускаются, пустые строки тоже."""
    archive = zipfile.ZipFile(io.BytesIO(data))
    shared: list[str] = []
    if "xl/sharedStrings.xml" in archive.namelist():
        for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).iter(f"{_NS}si"):
            shared.append("".join(node.text or "" for node in item.iter(f"{_NS}t")))
    sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    rows: list[dict[str, str]] = []
    for row in sheet.iter(f"{_NS}row"):
        cells: dict[str, str] = {}
        for cell in row.iter(f"{_NS}c"):
            kind = cell.get("t")
            if kind == "inlineStr":
                text = "".join(node.text or "" for node in cell.iter(f"{_NS}t"))
            else:
                value = cell.find(f"{_NS}v")
                if value is None or value.text is None:
                    continue
                text = shared[int(value.text)] if kind == "s" else value.text
            text = " ".join(text.split())
            if text:
                cells[_column(cell.get("r", ""))] = text
        if cells:
            rows.append(cells)
    return rows


# ---------------------------------------------------------------- разбор

_START = re.compile(r"^\d+\.\d+\s+(.+)$")


def blocks_of(rows: list[dict[str, str]]) -> list[dict]:
    """Строки приложения -> программы: название (как в столбце B), уровень,
    условия (D) и пороги (E). Программа начинается строкой с номером «1.1» в
    столбце B, продолжается строками без него; сноски («* …») её закрывают."""
    blocks: list[dict] = []
    current: dict | None = None
    for cells in rows:
        if cells.get("A", "").startswith("*"):
            current = None
            continue
        start = _START.match(cells.get("B", ""))
        if start:
            current = {"title": start.group(1), "level": cells.get("C", ""), "conditions": [], "results": []}
            blocks.append(current)
        if current is None:
            continue
        if "D" in cells:
            current["conditions"].append(cells["D"])
        if "E" in cells:
            current["results"].append(cells["E"])
    return blocks


_SET = (
    # «/» между эстонским и эстонским как вторым; у Toidu- ja biotehnoloogia
    # 2027/28 вместо него «ja» — смысл тот же.
    r"matemaatika vähemalt (\d+) punkti,? (?:ja )?eesti keel vähemalt (\d+)(?: punkti)?(?: ?/ ?| ja )"
    r"eesti keel teise keelena (?:vähemalt )?(\d+) punkti(?:,? ja inglise keel vähemalt (B2|C1) tasemel)?\."
)
_APPLY = re.compile(r"^Kandideerimiseks nõut(?:ud|av) (?:lävend|tulemus): " + _SET + "$")
_GUARANTEE = re.compile(r"^Õppekoha tagab tulemus: " + _SET + "$")
_PLACES = re.compile(r"^Piirarv: (\d+)$")
# Условия, при которых правило — только пороги госэкзаменов.
_EXAMS = {
    "1) laia matemaatika riigieksam",
    "2) eesti keele riigieksam",
    "3) inglise keele riigieksam või tasemetest",
}


def _threshold_set(match: re.Match) -> dict:
    result = {"math": int(match.group(1)), "estonian": int(match.group(2)), "estonian_second": int(match.group(3))}
    if match.group(4):
        result["english"] = match.group(4)
    return result


def rule_of(block: dict) -> dict | None:
    """Правило в форме ee_admission.rule у TalTech; None — не узнано."""
    if any(condition not in _EXAMS for condition in block["conditions"]):
        return None
    apply = guarantee = places = None
    for line in block["results"]:
        if (match := _APPLY.match(line)) and apply is None:
            apply = _threshold_set(match)
        elif (match := _GUARANTEE.match(line)) and guarantee is None:
            guarantee = _threshold_set(match)
        elif (match := _PLACES.match(line)) and places is None:
            places = int(match.group(1))
        else:
            return None
    if guarantee is None:
        return None
    # Есть порог для подачи — между ним и гарантирующим места делит рейтинг,
    # и число мест обязано быть. Нет — приём только по порогу, без мест.
    ranking = apply is not None
    if ranking != (places is not None):
        return None
    english = "english" in guarantee or (apply is not None and "english" in apply)
    if english != any(condition.startswith("3)") for condition in block["conditions"]):
        return None
    return {"model": "thresholds", "apply": apply, "guarantee": guarantee, "places": places, "ranking": ranking, "wide_math": True}


def name_of(title: str) -> tuple[str, bool]:
    """«2.6 Keskkonna- energia- ja keemiatehnoloogia (EACB)» без номера ->
    (название без кода и пометок, новый ли учебный план — «***»)."""
    new_curriculum = "***" in title
    name = title.replace("*", "")
    name = re.split(r"\s*\(|\s+[A-Z]{4}\)", name)[0]
    return name.strip(" ,"), new_curriculum


def normalized(name: str) -> str:
    """Для сравнения с каталогом: регистр, запятые и пробелы не важны
    («Keskkonna-, energia-» в каталоге, «Keskkonna- energia-» в решении)."""
    return " ".join(name.casefold().replace(",", " ").split())


_DECIDED = re.compile(r"senati (\d{1,2})\.(\d{1,2})\.(\d{4}) otsusega nr (\d+)")
_YEAR = re.compile(r"(\d{4})/(\d{4})\.\s*õa vastuvõtutingimused")


def decision_of(page: str) -> dict:
    """Со страницы решения: учебный год, дата и номер решения, ссылка на
    приложение 1. Чего-то нет — ValueError: страница поменялась, читать
    приложение вслепую нельзя."""
    text = " ".join(re.sub(r"<[^>]+>", " ", page).split())
    decided = _DECIDED.search(text)
    year = _YEAR.search(text)
    links = re.findall(r'href="([^"]+_Lisa_1\.xlsx)"', page)
    masters = re.findall(r'href="([^"]+[_-][Ll]isa_?2\.xlsx)"', page)
    if not decided or not year or len(set(links)) != 1 or len(set(masters)) != 1:
        raise ValueError("страница решения не узнана: нет даты решения, учебного года или единственных ссылок на приложения 1 и 2")
    day, month, year_of_decision, number = decided.groups()
    academic_year = f"{year.group(1)}/{year.group(2)}"
    return {
        "academic_year": academic_year,
        "decided_on": date(int(year_of_decision), int(month), int(day)).isoformat(),
        "source_title": f"I ja II kõrgharidusastme üliõpilaste {academic_year}. õa vastuvõtutingimused (senati otsus nr {number})",
        "annex_url": urljoin(DECISION_URL, links[0]),
        "masters_url": urljoin(DECISION_URL, masters[0]),
    }


# ---------------------------------------------------------------- магистратура

# Опечатка в названии в решении 24.11.2026 № 40 — каталогу нужно правильное.
NAME_FIXES = {"tehnisintellekt äris": "tehisintellekt äris"}


def master_blocks_of(rows: list[dict[str, str]]) -> list[dict]:
    """Строки приложения 2 -> программы: название (B), форма обучения (C),
    требования к образованию (D), испытания (E), порог (F). Строка без
    номера в B со «Väliskandidaadil: …» в E — условия для иностранцев."""
    blocks: list[dict] = []
    current: dict | None = None
    for cells in rows:
        if cells.get("A", "").startswith("*"):
            current = None
            continue
        start = _START.match(cells.get("B", ""))
        if start:
            current = {
                "title": start.group(1),
                "form": cells.get("C"),
                "education": cells.get("D"),
                "tests": cells.get("E"),
                "threshold": cells.get("F"),
                "foreign_tests": None,
                "foreign_threshold": None,
            }
            blocks.append(current)
        elif current is not None and cells.get("E", "").startswith("Väliskandidaadil:"):
            current["foreign_tests"] = cells["E"].removeprefix("Väliskandidaadil:").strip()
            current["foreign_threshold"] = cells.get("F")
    return blocks


def _clean(text: str | None) -> str | None:
    """Без сносок «***»: что они значат, правило хранит отдельно."""
    if text is None:
        return None
    text = re.sub(r"\s*\*+", "", text)
    return " ".join(text.split()).strip(" ,") or None


def text_rule_of(block: dict) -> dict | None:
    """Правило «text»: условия как в решении. None — нет требований,
    испытаний или порога (строка неполная — показывать нечего)."""
    education, tests, threshold = _clean(block["education"]), _clean(block["tests"]), _clean(block["threshold"])
    if not education or not tests or not threshold or block["form"] not in {"P", "S", "P/S"}:
        return None
    raw = " ".join(filter(None, [block["tests"], block["foreign_tests"]]))
    return {
        "model": "text",
        "study_form": block["form"],
        "education": education,
        "tests": tests,
        "threshold": threshold,
        "foreign_tests": _clean(block["foreign_tests"]),
        "foreign_threshold": _clean(block["foreign_threshold"]),
        # сноска «***» (ровно три звезды): иностранцу нужен GRE, минимумы — в
        # сноске решения; «****» — новый учебный план, это не GRE
        "gre": bool(re.search(r"(?<!\*)\*{3}(?!\*)", raw)) or "GRE" in raw,
    }


def master_names_of(title: str) -> tuple[list[str], bool]:
    """«1.7 Cybersecurity IVCM (Küberturve)» без номера -> (все названия
    программы — английское и эстонское в скобках, без кода; новый ли план —
    «****»)."""
    new_curriculum = "****" in title
    names = []
    # «(NAEM), Tartu» — место учёбы после кода, не название
    title = re.sub(r",\s*Tartu\s*$", "", title.replace("*", "").strip())
    for part in re.split(r"[()]", title):
        part = re.sub(r"\s+[A-Z]{4}$", "", part.strip(" ,")).strip()
        if part and not re.fullmatch(r"[A-Z]{4}", part):
            names.append(NAME_FIXES.get(normalized(part), part))
    return names, new_curriculum


# ---------------------------------------------------------------- самотест


def _xlsx(rows: list[list[str]]) -> bytes:
    """Маленький Excel для самотеста: все ячейки — общие строки."""
    shared: list[str] = []
    sheet_rows = []
    for number, row in enumerate(rows, start=1):
        cells = []
        for column, text in zip("ABCDEF", row):
            if text:
                shared.append(text)
                cells.append(f'<c r="{column}{number}" t="s"><v>{len(shared) - 1}</v></c>')
        sheet_rows.append(f'<row r="{number}">{"".join(cells)}</row>')
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    strings = "".join(f"<si><t>{text}</t></si>" for text in shared)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", f"<sst {ns}>{strings}</sst>")
        archive.writestr("xl/worksheets/sheet1.xml", f'<worksheet {ns}><sheetData>{"".join(sheet_rows)}</sheetData></worksheet>')
    return buffer.getvalue()


def _selftest() -> None:
    # строки — как в приложении 1 решения 24.11.2026 № 40
    data = _xlsx([
        ["", "", "", "", "Lisa 1"],
        ["Teadus-kond", "Õppekava (eriala)", "õppe-tase", "Konkursitingimused*", "Kandiderimiseks /õppekoha saamiseks nõutav tulemus"],
        ["1. Infotehnoloogia teaduduskond", "1.1 Informaatika ja tehisintellekt (IAIB)", "B", "1) laia matemaatika riigieksam",
         "Kandideerimiseks nõutud lävend: matemaatika vähemalt 65 punkti ja eesti keel vähemalt 55 / eesti keel teise keelena vähemalt 65 punkti."],
        ["", "", "", "2) eesti keele riigieksam",
         "Õppekoha tagab tulemus: matemaatika vähemalt 75 punkti ja eesti keel vähemalt 60 / eesti keel teise keelena vähemalt 70 punkti."],
        ["", "", "", "", "Piirarv: 150"],
        ["", "1.2 IT süsteemide inseneeria (IAAB), päeva- või sessioonõpe***", "B", "Päevaõppes:", "Päevaõppes:"],
        ["", "2.6 Keskkonna- energia- ja keemiatehnoloogia (EACB)", "B", "1) laia matemaatika riigieksam",
         "Kandideerimiseks nõutud lävend: matemaatika vähemalt 45 punkti ja eesti keel vähemalt 45 punkti / eesti keel teise keelena vähemalt 55 punkti."],
        ["", "", "", "2) eesti keele riigieksam",
         "Õppekoha tagab tulemus: matemaatika vähemalt 50 punkti ja eesti keel vähemalt 50 ja eesti keel teise keelena 60 punkti."],
        ["", "", "", "", "Piirarv: 60"],
        ["", "2.4 Hoonete sisekliima ja veetehnika (EAKI)", "I", "1) laia matemaatika riigieksam",
         "Kandideerimiseks nõutud lävend: matemaatika vähemalt 45 punkti, eesti keel vähemalt 45 punkti / eesti keel teise keelena vähemalt 55 punkti ja vestlus vähemalt 5 punkti."],
        ["", "4.2 Rakenduslik majandusteadus (TAAB)", "B", "1) laia matemaatika riigieksam",
         "Õppekoha tagab tulemus: matemaatika vähemalt 70 punkti, eesti keel vähemalt 55 / eesti keel teise keelena vähemalt 75 punkti ja inglise keel vähemalt B2 tasemel."],
        ["", "", "", "2) eesti keele riigieksam", ""],
        ["", "", "", "3) inglise keele riigieksam või tasemetest", ""],
        ["", "7.4 Ringmajandus ja kestlik tootmine (RDRR), päevaõpe***", "R", "1) lõputunnistuse keskmine hinne VÕI laia matemaatika riigieksam",
         "Õppekoha tagab tulemus: keskmine hinne vähemalt 3,80 VÕI matemaatika vähemalt 50 punkti."],
        ["* laia matemaatika riigieksamit asendab vajadusel …", "", "", "", ""],
    ])
    rows = xlsx_rows(data)
    assert rows[0] == {"E": "Lisa 1"}, rows[0]
    blocks = blocks_of(rows)
    assert [b["title"] for b in blocks] == [
        "Informaatika ja tehisintellekt (IAIB)",
        "IT süsteemide inseneeria (IAAB), päeva- või sessioonõpe***",
        "Keskkonna- energia- ja keemiatehnoloogia (EACB)",
        "Hoonete sisekliima ja veetehnika (EAKI)",
        "Rakenduslik majandusteadus (TAAB)",
        "Ringmajandus ja kestlik tootmine (RDRR), päevaõpe***",
    ], [b["title"] for b in blocks]
    iaib, iaab, eacb, eaki, taab, rdrr = (rule_of(b) for b in blocks)
    assert iaib == {
        "model": "thresholds",
        "apply": {"math": 65, "estonian": 55, "estonian_second": 65},
        "guarantee": {"math": 75, "estonian": 60, "estonian_second": 70},
        "places": 150, "ranking": True, "wide_math": True,
    }, iaib
    assert iaab is None, "две формы обучения — не разбираем"
    assert eacb and eacb["guarantee"] == {"math": 50, "estonian": 50, "estonian_second": 60} and eacb["places"] == 60
    assert eaki is None, "собеседование — не разбираем"
    assert taab == {
        "model": "thresholds", "apply": None,
        "guarantee": {"math": 70, "estonian": 55, "estonian_second": 75, "english": "B2"},
        "places": None, "ranking": False, "wide_math": True,
    }, taab
    assert rdrr is None, "средняя оценка — не разбираем"

    assert name_of("Keskkonna- energia- ja keemiatehnoloogia (EACB)") == ("Keskkonna- energia- ja keemiatehnoloogia", False)
    assert name_of("Logistika ja liikuvus EALB)") == ("Logistika ja liikuvus", False)
    assert name_of("Ringmajandus ja kestlik tootmine (RDRR), päevaõpe***") == ("Ringmajandus ja kestlik tootmine", True)
    assert normalized("Keskkonna-, energia- ja keemiatehnoloogia") == normalized("Keskkonna- energia- ja keemiatehnoloogia")

    page = (
        '<h1>I ja II kõrgharidusastme üliõpilaste 2027/2028. õa vastuvõtutingimused</h1>'
        "<p>Kinnitatud Tallinna Tehnikaülikooli senati 24.11.2026 otsusega nr 40</p>"
        '<a href="https://oigusaktid.taltech.ee/wp-content/uploads/2026/11/TT_x_Lisa_1.xlsx">Lisa 1</a>'
        '<a href="https://oigusaktid.taltech.ee/wp-content/uploads/2026/11/TT_x_Lisa_1.xlsx">Lisa 1</a>'
        '<a href="https://oigusaktid.taltech.ee/wp-content/uploads/2026/11/TT_x_Lisa_1_ja_2_VV.xlsx">Lisa 1 ja 2</a>'
        '<a href="https://oigusaktid.taltech.ee/wp-content/uploads/2026/11/x_lisa2.xlsx">Lisa 2</a>'
    )
    decision = decision_of(page)
    assert decision["academic_year"] == "2027/2028" and decision["decided_on"] == "2026-11-24", decision
    assert decision["annex_url"].endswith("/TT_x_Lisa_1.xlsx")
    assert "nr 40" in decision["source_title"]
    assert decision["masters_url"].endswith("/x_lisa2.xlsx")
    try:
        decision_of("<p>Lehte ei leitud</p>")
        raise AssertionError("неузнанная страница должна остановить загрузку")
    except ValueError:
        pass

    # приложение 2 — строки как в решении 24.11.2026 № 40
    masters = master_blocks_of(xlsx_rows(_xlsx([
        ["Teaduskond / täpsustus", "Õppekava", "S/P*", "Hariduse nõuded", "Konkursitingimused**", "Õppekoha saamise lävend"],
        ["", "1.7 Cybersecurity IVCM (Küberturve)", "P", "kõrgharidus info- ja kommunikatsioonitehnoloogia erialal",
         "motivatsioonikiri, CV + vestlus, test ***, sh mõlemad katse osad vähemalt 5 punkti", "5+5"],
        ["", "2.7 Technology of Wood, Plastics and Textiles (KVEM) (Puidu-, plasti- ja tekstiilitehnoloogia)", "P",
         "kõrgharidus lähedasel erialal", "CV ja vestlus", "5"],
        ["", "", "", "", "Väliskandidaadil: CV ja vestlus***", "5"],
        ["", "2.12 Tööstusökoloogia (NAEM), Tartu", "S", "kõrgharidus", "test", "5"],
        ["", "4.12 Tehnisintellekt äris (MAIM)", "S", "kõrgharidus", "CV, projektiplaan", "kandideerimislävend 5, piirarv 45 *****"],
        ["", "7.3 Energia- ja tööstussüsteemid (RAEM)****", "S", "kõrgharidus loodus- või tehnikateadustes", "CV ja vestlus", "5"],
        ["", "5.2 Maritime Digital Solutions (VAMM)", "P", "kõrgharidus", "motivatsioonikiri + vestlus", ""],
        ["* õppevormi täpsustus", "", "", "", "", ""],
    ])))
    assert len(masters) == 6, [m["title"] for m in masters]
    cyber, wood, tartu, ai, energy, maritime = masters
    assert text_rule_of(cyber) == {
        "model": "text", "study_form": "P",
        "education": "kõrgharidus info- ja kommunikatsioonitehnoloogia erialal",
        "tests": "motivatsioonikiri, CV + vestlus, test, sh mõlemad katse osad vähemalt 5 punkti",
        "threshold": "5+5", "foreign_tests": None, "foreign_threshold": None, "gre": True,
    }, text_rule_of(cyber)
    wood_rule = text_rule_of(wood)
    assert wood_rule and wood_rule["foreign_tests"] == "CV ja vestlus" and wood_rule["foreign_threshold"] == "5" and wood_rule["gre"], wood_rule
    assert text_rule_of(tartu)["gre"] is False
    assert text_rule_of(ai)["threshold"] == "kandideerimislävend 5, piirarv 45", text_rule_of(ai)
    assert text_rule_of(energy)["gre"] is False, "«****» — новый план, а не GRE"
    assert text_rule_of(maritime) is None, "нет порога — показывать нечего"
    assert master_names_of(cyber["title"]) == (["Cybersecurity", "Küberturve"], False), master_names_of(cyber["title"])
    assert master_names_of(wood["title"])[0] == ["Technology of Wood, Plastics and Textiles", "Puidu-, plasti- ja tekstiilitehnoloogia"]
    assert master_names_of(tartu["title"])[0] == ["Tööstusökoloogia"], master_names_of(tartu["title"])
    assert master_names_of(ai["title"])[0] == ["tehisintellekt äris"]
    assert master_names_of(energy["title"]) == (["Energia- ja tööstussüsteemid"], True)
    print("ee_load_taltech_conditions selftest: ok")


# ---------------------------------------------------------------- запуск


def main() -> None:
    args = sys.argv[1:]
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in args:
        _selftest()
        return
    from dotenv import load_dotenv

    import polite
    from db import fetch_all, get_service_client
    from db_retry import execute

    load_dotenv()
    decision = decision_of(polite.fetch_text(DECISION_URL))
    with polite.open_url(decision["annex_url"]) as response:
        blocks = blocks_of(xlsx_rows(response.read()))
    with polite.open_url(decision["masters_url"]) as response:
        masters = master_blocks_of(xlsx_rows(response.read()))
    print(
        f"решение: {decision['source_title']}, {decision['decided_on']}; "
        f"программ в приложении 1: {len(blocks)}, в приложении 2: {len(masters)}"
    )

    client = get_service_client()
    university = execute(client.table("university").select("id").eq("slug", "taltech")).data[0]["id"]
    programmes = fetch_all(
        lambda: client.table("programme")
        .select("id, name_et, degree_level, language_of_instruction")
        .eq("university_id", university)
        .order("id")
    )
    # Приложение 1: эстонские названия — у программ на эстонском; английские
    # программы названы по-английски и с тестами, их правило не разбирается.
    # Приложение 2: у английских магистратур эстонское название стоит в
    # скобках, поэтому язык обучения любой.
    by_name: dict[tuple[str, str], list[str]] = {}
    masters_by_name: dict[str, list[str]] = {}
    for programme in programmes:
        if not programme["name_et"]:
            continue
        if programme["degree_level"] == "master":
            masters_by_name.setdefault(normalized(programme["name_et"]), []).append(programme["id"])
        elif programme["language_of_instruction"] == "et":
            by_name.setdefault((normalized(programme["name_et"]), programme["degree_level"]), []).append(programme["id"])

    now = datetime.now(timezone.utc).isoformat()
    rows: dict[str, dict] = {}

    def add(ids: list[str], rule: dict, new_curriculum: bool) -> None:
        for programme_id in ids:
            if programme_id in rows:
                # две строки решения на одну программу — не угадываем, какая верна
                print(f"    ! программа {programme_id} уже получила правило из другой строки — эта пропущена")
                continue
            rows[programme_id] = {
                "programme_id": programme_id,
                "academic_year": decision["academic_year"],
                "rule": rule,
                "new_curriculum": new_curriculum,
                "source_url": DECISION_URL,
                "source_title": decision["source_title"],
                "decided_on": decision["decided_on"],
                "extracted_at": now,
            }

    print("приложение 1:")
    for block in blocks:
        name, new_curriculum = name_of(block["title"])
        level = LEVELS.get(block["level"])
        rule = rule_of(block)
        ids = by_name.get((normalized(name), level or ""), [])
        status = "правило" if rule else "не разобрано"
        print(f"  {name} [{block['level']}]: {status}; в каталоге: {len(ids)}" + (" (новый учебный план)" if new_curriculum else ""))
        if rule is not None:
            add(ids, rule, new_curriculum)
    print("приложение 2:")
    for block in masters:
        names, new_curriculum = master_names_of(block["title"])
        rule = text_rule_of(block)
        ids = sorted({programme_id for name in names for programme_id in masters_by_name.get(normalized(name), [])})
        status = "условия" if rule else "строка неполная"
        print(f"  {' / '.join(names)}: {status}; в каталоге: {len(ids)}" + (" (новый учебный план)" if new_curriculum else ""))
        if rule is not None:
            add(ids, rule, new_curriculum)
    print(f"правил к записи: {len(rows)} (программ каталога)")

    if "--apply" not in args:
        print("\nзаписи не было (добавьте --apply)")
        print(polite.report_and_reset())
        return
    if rows:
        execute(client.table("ee_next_rule").upsert(list(rows.values()), on_conflict="programme_id,academic_year"))
    # Правила этого года у программ TalTech, которых в решении больше нет
    # или которые теперь не разбираются, — удалить.
    keep = set(rows)
    stale = [p["id"] for p in programmes if p["id"] not in keep]
    for start in range(0, len(stale), 200):
        execute(
            client.table("ee_next_rule").delete().eq("academic_year", decision["academic_year"]).in_("programme_id", stale[start : start + 200])
        )
    print(f"записано: {len(rows)}")
    print(polite.report_and_reset())


if __name__ == "__main__":
    main()
