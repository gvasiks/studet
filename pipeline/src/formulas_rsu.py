"""Конкурсные формулы RSU из утверждённого документа (не со страницы сайта).

Источник: "Uzņemšanas noteikumi īsā cikla, pirmā cikla un otrā cikla studiju
programmās 2026./2027. akadēmiskajam gadam" (RSU iekšējais normatīvais akts
1-PB-9/36/2025 от 01.12.2025, консолидированная редакция с поправками
1-PB-9/14/2026 и 1-PB-9/29/2026) — копия в
docs/source-documents/rsu/uznemsanas-noteikumi-pamatstudijas-2026-27-rev1.pdf.

Документ регулярный: на каждую программу своё приложение (Pielikums Nr. N), в
нём строка "10. Konkursa vērtēšanas kritēriji" со списком "N% no kopējā
vērtējuma veido CE vērtējums <предмет>". Итог — 100 баллов (п. 25), поэтому
коэффициент слагаемого = N/100: CE 0–100% × уровень × N/100.

Как и в formulas_lu.py, ничего не додумываем: что модель не выражает, идёт в
отчёт с причиной и в базу не попадает.
- "CE ķīmijā vai bioloģijā", "gala atzīme bioloģijā vai dabaszinībās" —
  альтернативы, как считать при нескольких, документ не говорит;
- "iestājpārbaudījums fiziskajā sagatavotībā", "Sports" — шкала вне
  документа (таблица Nr. 29 / "перенос в 100 баллов").
- OSPPP (objektīvi strukturētais profesionālās piemērotības pārbaudījums):
  п. 24 прямо говорит, что оценивается по 10-балльной шкале, поэтому
  вход 0–10 и коэффициент N% × 100 / 10 (50% -> 5,0).
- "svešvaloda" (любой из иностранных) — слот 'english', как у остальных вузов;
  у "Starptautiskais bizness un jaunuzņēmumu darbība" прямо "angļu valodā".
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pypdf

from formula_drafts import Draft, DocumentMeta, ParsedTerm, write_drafts

REPO_ROOT = Path(__file__).resolve().parents[2]
COPY_PATH = "docs/source-documents/rsu/uznemsanas-noteikumi-pamatstudijas-2026-27-rev1.pdf"
PDF_PATH = REPO_ROOT / COPY_PATH
SOURCE_URL = (
    "https://www.rsu.lv/sites/default/files/imce/Dokumenti/noteikumi/"
    "uznemsanas_noteikumi_pamatstudijas_2026_2027_rev1.pdf"
)
SOURCE_DOC = (
    "Uzņemšanas noteikumi īsā cikla, pirmā cikla un otrā cikla studiju programmās "
    "2026./2027. akadēmiskajam gadam (RSU 1-PB-9/36/2025, 01.12.2025., ar grozījumiem "
    "1-PB-9/14/2026 un 1-PB-9/29/2026)"
)
VALID_FROM = date(2025, 12, 1)  # дата акта

# Номер приложения -> слаги программ каталога. Названия в каталоге английские,
# соответствие ручное. Филиал (Liepāja) — та же программа по тем же правилам:
# приложение места реализации не различает.
RSU_SLUGS: dict[str, list[str]] = {
    "1": ["medical-massage-liepaja-branch"],
    "2": ["physician-assistant-liepaja-branch"],
    "3": ["sports-coach", "sports-coach-liepaja-branch"],
    "4": ["dental-hygiene"],
    "5": ["audio-speech-therapy"],
    "6": ["occupational-therapy-lv"],
    "7": ["pharmacy-lv-0"],
    "8": ["physiotherapy-0-lv"],
    "9": ["nursing-lv", "nursing-liepaja-branch-0"],
    "10": ["medicine", "medicine-lv"],
    "11": ["orthotics-and-prosthetics"],
    "12": ["public-health-0"],
    "13": ["social-work-0"],
    "14": ["nutrition"],
    "15": ["midwifery"],
    "16": ["dentistry", "dentistry-lv"],
    "17": ["multimedia-communication"],
    "19": ["psychology-0"],
    "20": ["public-relations"],
    "21": ["international-business-and-sustainable-economy"],
    "22": ["international-business-and-start-up-entrepreneurship"],
    "23": ["international-marketing-and-advertising"],
    "24": ["international-relations-european-studies"],
    "25": ["law"],
    "26": ["journalism"],
    "27": ["sports-science-ba"],
    "28A": ["health-physical-activity-and-security"],
}
# Без формулы по конкурсу: 18 (Policijas darbs — по направлению служб),
# 28B (по списку Jaunsardzes centrs) — в документе конкурса баллов нет.

CE_SUBJECTS = {
    "matemātikā": "mathematics",
    "latviešu valodā": "latvian",
    "bioloģijā": "biology",
    "ķīmijā": "chemistry",
    "fizikā": "physics",
}
OSPPP_RAW_MAX = 10  # п. 24: OSPPP оценивается по 10-балльной шкале


@dataclass
class ParsedFormula:
    terms: list[ParsedTerm] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.terms) and not self.problems


@dataclass
class ParsedAppendix:
    number: str
    name: str
    excerpt: str
    slugs: list[str]
    formula: ParsedFormula | None
    note: str | None
    # сырой текст критериев (до разбора весов) — для requirements_rsu.py:
    # тот же документ, вопрос беднее ("какие CE нужны", не веса)
    criteria_text: str | None = None


def load_text(pdf_path: Path = PDF_PATH) -> str:
    reader = pypdf.PdfReader(str(pdf_path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _classify(percent: float, description: str) -> tuple[str, str | None, float] | str:
    """(kind, subject, coefficient) или строка с причиной, почему слагаемое не берётся."""
    text = re.sub(r"\s+", " ", description).strip(" ,.;").lower()
    # PDF местами рвёт слова: "tes- tēšanas", "vērtēj ums"
    text = re.sub(r"-\s+", "", text)
    text = text.replace("vērtēj ums", "vērtējums")

    if text.startswith("iestājpārbaudījums osppp") or text == "osppp":
        return ("entrance_exam", "osppp", round(percent / OSPPP_RAW_MAX, 6))

    text = re.sub(r"^(?:ce )?(?:veido |ietekmē )?", "", text)
    text = re.sub(r"^ce ", "", text)

    # "CE vērtējums matemātikā" / "CE ķīmijā vai bioloģijā"
    match = re.match(r"^(?:vērtējums )?(.+?)(?:\s+vai starptautiskas testēšanas institūcijas pārbaudījuma vērtējums (.+))?$", text)
    if not match:
        return f"нераспознанное слагаемое: «{text[:90]}»"
    subject_phrase = match.group(1).strip()
    if match.group(2):  # язык: "svešvalodā vai ... svešvalodā"
        if subject_phrase == "svešvalodā":
            return ("ce", "english", percent / 100)
        if subject_phrase == "angļu valodā":
            return ("ce", "english", percent / 100)
        return f"неизвестный язык: «{subject_phrase}»"
    if " vai " in subject_phrase:
        return f"альтернатива (как считать, если сданы несколько, документ не говорит): «{subject_phrase}»"
    if subject_phrase in CE_SUBJECTS:
        return ("ce", CE_SUBJECTS[subject_phrase], percent / 100)
    return f"не выражается моделью: «{subject_phrase[:80]}»"


BULLET_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%\s+no kopējā vērtējuma\s+(.+?)(?=\s*•|\s*$)", re.S)
# один маркер "• N% no kopējā vērtējuma [CE] [veido|ietekmē] <тело>" — общий
# для parse_criteria (нужны веса) и requirements_rsu.py (нужны только предметы)
BULLET_LINE_RE = re.compile(r"\s*(\d+(?:[.,]\d+)?)\s*%\s+no kopējā vērtējuma\s+(?:CE\s+)?(?:veido|ietekmē)?\s*(.+)$")


def parse_criteria(criteria: str) -> ParsedFormula:
    result = ParsedFormula()
    flat = re.sub(r"\s+", " ", criteria)
    # "100% OSPPP no kopējā vērtējuma" — единственное слагаемое без "•"
    single = re.search(r"(\d+)%\s+(OSPPP)\s+no kopējā vērtējuma", flat)
    total = 0.0
    if single:
        pct = float(single.group(1))
        result.terms.append(ParsedTerm("entrance_exam", "osppp", round(pct / OSPPP_RAW_MAX, 6)))
        total += pct
    else:
        for bullet in re.split(r"•", flat)[1:]:
            match = BULLET_LINE_RE.match(bullet.strip(" ,.;"))
            if not match:
                result.problems.append(f"строка без «N% no kopējā vērtējuma»: «{bullet.strip()[:70]}»")
                continue
            pct = float(match.group(1).replace(",", "."))
            total += pct
            body = match.group(2)
            # "veido gala atzīme …" / "veido fiziskās sagatavotības iestājpārbaudījuma …" — не CE
            if not re.match(r"(?:CE\s+)?vērtējums|CE\s", "CE " + body) and "CE" not in bullet:
                result.problems.append(f"слагаемое не из CE, шкала вне документа: «{body[:80]}»")
                continue
            classified = _classify(pct, body)
            if isinstance(classified, str):
                result.problems.append(classified)
            else:
                kind, subject, coefficient = classified
                result.terms.append(ParsedTerm(kind, subject, coefficient))
    if abs(total - 100) > 0.01:
        result.problems.append(f"сумма процентов {total:g}, а должна быть 100 (п. 25)")
    return result


def parse_document(text: str) -> list[ParsedAppendix]:
    body = text[text.find("Pielikums Nr. 1 – Ārstnieciskā masāža") :]
    body = body[body.find("Rektors") :]  # после списка приложений
    parts = re.split(r"Pielikums Nr\.\s*(\d+\s?[AB]?)\s+(?=1\.\s+Studiju|1\.\s*\n)", body)
    appendices: list[ParsedAppendix] = []
    for k in range(1, len(parts), 2):
        number = re.sub(r"\s+", "", parts[k])
        txt = parts[k + 1]
        name = re.sub(r"\s+", " ", txt[:220]).split("2. Studiju")[0]
        name = re.sub(r"^1\.\s*Studiju programma\s*\d+\.\s*", "", name).strip()
        excerpt = re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", txt)).strip()

        row = re.search(r"Konkursa vērtēšanas\s+kritē-?\s*riji:?\s+(Studiju programm.*)", txt, re.S)
        formula: ParsedFormula | None = None
        note: str | None = None
        criteria_text: str | None = None
        if number not in RSU_SLUGS:
            note = "нет конкурса по баллам (приём по направлению/списку) или нет в каталоге"
        elif not row:
            note = "в приложении нет строки «Konkursa vērtēšanas kritēriji»"
        else:
            crit = re.split(r"Vienād[au] |Papildu punkti|Papildus punkti|Piezīme\.|\* Studiju programmas nosaukums", row.group(1))[0]
            formula = parse_criteria(crit)
            criteria_text = crit
            # "Uzņemšanas rezultāta kopvērtējums nevar būt zemāks par N punktiem" — только в excerpt
        appendices.append(
            ParsedAppendix(number, name, excerpt, RSU_SLUGS.get(number, []), formula, note, criteria_text)
        )
    return appendices


def report(items: list[ParsedAppendix]) -> None:
    ok = [a for a in items if a.formula and a.formula.ok]
    print(f"приложений в документе: {len(items)}; пригодных к записи: {len(ok)}")
    for a in items:
        if a.formula is None:
            print(f"  [{a.number}] {a.name[:60]}: {a.note}")
        elif not a.formula.ok:
            print(f"  [{a.number}] {a.name[:60]}: не берётся — " + "; ".join(a.formula.problems))


def seed(items: list[ParsedAppendix], apply: bool) -> None:
    ready = [a for a in items if a.formula and a.formula.ok]
    drafts = [Draft(f"Nr. {a.number}", a.slugs, a.formula.terms, a.excerpt) for a in ready]  # type: ignore[union-attr]
    protocol = {}
    if apply:
        from seed_formulas import source_protocol

        protocol = source_protocol(
            number="1-PB-9/36/2025 (grozījumi: 1-PB-9/14/2026, 1-PB-9/29/2026)",
            doc_date=date(2026, 5, 14),
            copy_path=COPY_PATH,
            fetched_on=date(2026, 9, 20),
        )
    write_drafts(DocumentMeta("rsu", SOURCE_URL, SOURCE_DOC, VALID_FROM, protocol), drafts, apply)


def selftest() -> None:
    def terms(text: str) -> list[tuple]:
        result = parse_criteria(text)
        assert result.ok, result.problems
        return [(t.kind, t.subject, t.coefficient) for t in result.terms]

    assert terms(
        "Studiju programmas X reflektantus imatrikulē saskaņā ar uzņemšanas rezultātu kopvērtējumu, kurā: "
        "• 10% no kopējā vērtējuma veido CE vērtējums matemātikā, "
        "• 45% no kopējā vērtējuma veido CE vērtējums latviešu valodā, "
        "• 45% no kopējā vērtējuma veido CE vērtējums svešvalodā vai starptautiskas tes- tēšanas institūcijas "
        "pārbaudījuma vērtējums svešvalodā."
    ) == [("ce", "mathematics", 0.1), ("ce", "latvian", 0.45), ("ce", "english", 0.45)]

    # OSPPP: 10-балльная шкала, 50% -> коэффициент 5
    osppp = terms(
        "Studiju programmas Y reflektantus imatrikulē saskaņā ar uzņemšanas rezultātu kopvērtējumu, ko veido: "
        "• 50% no kopējā vērtējuma ietekmē iestājpārbaudījums OSPPP, "
        "• 15% no kopējā vērtējuma ietekmē CE vērtējums matemātikā, "
        "• 20% no kopējā vērtējuma ietekmē CE vērtējums latviešu valodā, "
        "• 15% no kopējā vērtējuma ietekmē CE vērtējums svešvalodā vai starptautiskas testēšanas institūcijas "
        "pārbaudījuma vērtējums svešvalodā."
    )
    assert osppp[0] == ("entrance_exam", "osppp", 5.0), osppp

    # альтернатива не берётся молча
    alt = parse_criteria(
        "Studiju programmas Z reflektantus imatrikulē saskaņā ar kopvērtējumu, kurā: "
        "• 85% no kopējā vērtējuma veido CE vērtējums ķīmijā vai bioloģijā, "
        "• 15% no kopējā vērtējuma veido CE vērtējums matemātikā."
    )
    assert not alt.ok and "альтернатива" in alt.problems[0]

    # сумма не 100
    assert not parse_criteria("• 10% no kopējā vērtējuma veido CE vērtējums matemātikā.").ok
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        parsed = parse_document(load_text())
        report(parsed)
        seed(parsed, apply="--apply" in sys.argv)
