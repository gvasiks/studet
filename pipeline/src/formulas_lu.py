"""Конкурсные формулы ЛУ из утверждённого документа (не со страницы сайта).

Источник: "Uzņemšanas prasības un kritēriji pamatstudiju programmās
2026./2027. akadēmiskajā gadā", 2. sadaļа (LU rīkojums Nr. 1-4/506,
27.11.2025, с поправками до 03.07.2026) — копия в
docs/source-documents/lu/uzn-prasibas-pamat-2026-27.pdf.

Раньше формулы ЛУ переписывались в seed_formulas.py руками (26 штук, с
документа 2025/26). Здесь их достаёт парсер: документ регулярный — на
каждую программу блок "2.Ф.П. Название – тип …:" с пунктами-маркерами и
формулой вида "CE латвийского kopvērtējums procentos (1,5 x 100 = 150) + …".

Правило проекта (5 и 6): извлекает и объясняет автоматика, источником факта
она не является, подтверждает человек. Поэтому парсер:
- НИЧЕГО не додумывает. Что модель формул выразить не может или что в
  документе не определено, идёт в отчёт с причиной и в базу не попадает;
- проверяет арифметику: у каждого слагаемого "(k x m = p)" должно быть
  k*m == p, а сумма p по формуле — 1000 (документ прямо говорит: "aprēķināšana
  tiek veikta 1000 punktu skalā", п. 1.10). Формула, где это не сходится,
  считается неразобранной;
- кладёт в базу дословный текст блока программы (source_excerpt), чтобы
  человек, подтверждающий формулу, сверял разобранное с оригиналом, а не с
  пересказом.

Что берётся: формула 1-го варианта вучаса uzņemšanā (CE) — вариант
'ce', по которому считает калькулятор. Не берутся пока: формула 2-го
варианта (годовые оценки аттестата — для тех, у кого нет CE), формула
ранней приёмки (iestājpārbaudījums ЛУ, до CE) и условия ("īpaši nosacījumi",
преимущества, доп. баллы) — последние идут дословно в source_excerpt.

Что модель НЕ выражает и потому не берётся:
- альтернативы между экзаменами: "CE fizikā vai CE ķīmijā, vai CE bioloģijā
  (6 x 100)". В документе не сказано, как считать, если сданы несколько
  (лучший? любой?). Выбрать самим = сочинить правило; вопрос к приёмной
  комиссии ЛУ. Исключение — "angļu / franču / vācu": так уже принято для
  всех формул ЛУ (subject='english', п. 1.4 документа называет три языка
  равноправными).
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
PDF_PATH = REPO_ROOT / "docs/source-documents/lu/uzn-prasibas-pamat-2026-27.pdf"
SCALE = 1000  # п. 1.10: конкурсный балл — по шкале 1000

# Название блока в документе (до " – ") -> слаги программ в нашем каталоге.
# Имена стабильны из года в год, номера блоков (2.1.7 …) — нет.
LU_SLUGS: dict[str, list[str]] = {
    "Biznesa vadība": ["business-administration-lv"],
    "Biznesa vadība (angļu valodā)": ["business-administration-en"],
    "E-biznesa vadība": ["e-business-management"],
    "Ekonomika": ["economics"],
    "Finanšu menedžments": ["financial-management"],
    "Grāmatvedība, analīze un audits": ["accounting-analysis-and-audit"],
    "Industriālā inženierija un vadība": ["industrial-engineering-and-management-lv"],
    "Industriālā inženierija un vadība (angļu valodā)": ["industrial-engineering-and-management-en"],
    "Informācijas pārvaldība": ["information-management"],
    "Komunikācijas zinātne": ["communication-science"],
    "Kultūras un sociālā antropoloģija": ["cultural-and-social-anthropology"],
    "Kultūras un sociālā antropoloģija (angļu valodā)": ["cultural-and-social-anthropology-en"],
    "Politikas zinātne": ["political-science"],
    "Sociālais darbs": ["social-work-in-riga-and-ul-branches"],
    "Socioloģija": ["sociology"],
    "Starptautiskā ekonomika un komercdiplomātija": ["international-economics-and-commercial-diplomacy-lv"],
    "Starptautiskā ekonomika un komercdiplomātija (angļu valodā)": ["international-economics-and-commercial-diplomacy-en"],
    "Datorzinātnes": ["computer-science"],
    "Datorzinātnes (angļu valodā)": ["computer-science-en"],
    "Fizika": ["physics"],
    "Ģeogrāfija": ["geography"],
    "Ģeoinformātika": ["geoinformatics"],
    "Ģeoloģija": ["geology"],
    "Kultūrvides mantojuma izpēte un aizsardzība": ["research-and-protection-of-cultural-and-environmental-heritage"],
    "Matemātika": ["mathematics"],
    "Matemātiķis statistiķis": ["mathematician-statistician"],
    "Optometrija": ["optometry-lv"],
    "Optometrija (angļu valodā)": ["optometry-en"],
    "Programmēšana un datortīklu administrēšana": ["programming-and-computer-network-administration-college"],
    "Vides zinātne": ["environmental-science"],
    "Anglistikas, Eiropas valodu un biznesa studijas": ["english-european-languages-and-business-studies"],
    "Āzijas un starpkultūru studijas": ["asian-and-intercultural-studies"],
    "Filoloģija": ["philology-lv"],
    "Filozofija": ["philosophy"],
    "Latvistika": ["latvian-studies"],
    "Teoloģija un reliģijpētniecība": ["theology-and-religious-studies"],
    "Vēsture un arheoloģija": ["history-and-archeology"],
    "Māksla": ["art-1"],
    "Pirmsskolas skolotājs": ["preschool-teacher-college"],
    "Psiholoģija": ["psychology-1"],
    "Sākumizglītības skolotājs": ["primary-education-teacher"],
    "Sporta treneris": ["sports-coach-college"],
    "Sports, tehnoloģijas un sabiedrības veselība": ["sports-technology-and-public-health"],
    "Skolotājs": ["professional-bachelor-study-programme-teacher"],
    "Pirmstiesas izmeklēšana": ["translate-to-anglu-pirmstiesas-izmeklesana"],
    "Tiesību zinātne": ["law-1"],
    "Biznesa procesu vadība": ["business-process-management-lv"],
    "Biznesa procesu vadība (angļu valodā)": ["business-process-management-en"],
    "Finanses": ["finance-lv"],
    "Finanšu pārvaldības informācijas sistēmas (kopīga ar RTU) (angļu valodā)": ["finance-management-information-systems-en"],
    "Grāmatvedība un finanses": ["accountancy-and-finance-lv-college"],
    "Starptautiskās finanses (angļu)": ["international-finance-en"],
    "Arodveselība un drošība darbā": ["occupational-health-and-safety-at-work"],
    "Ārstniecība": ["medicine-lv"],
    "Ārstniecība (angļu valodā)": ["medicine-en"],
    "Bioloģija un biomedicīna": ["biology"],
    "Biotehnoloģija un bioinženierija (angļu valodā)": ["biotechnology-and-bioengineering"],
    "Darba aizsardzība": ["labour-protection-college"],
    "Farmācija": ["pharmacy"],
    "Ķīmija": ["chemistry"],
    "Māszinības": ["nursing-lv"],
    "Zobārstniecība": ["dentistry-lv"],
    "Zobārstniecība (angļu valodā)": ["dentistry-en"],
    "Radiogrāfija": ["radiography"],
}

# Предмет в тексте формулы -> ключ предмета (те же, что в словарях локалей)
CE_SUBJECTS = {
    "latviešu valodā": "latvian",
    "matemātikā": "mathematics",
    "angļu valodā": "english",
    "fizikā": "physics",
    "ķīmijā": "chemistry",
    "bioloģijā": "biology",
    "vēsturē": "history",
    "sociālajās zinātnēs": "socialstudies",
    "latviešu literatūrā": "literature",
    "ģeogrāfijā": "geography",
    "vācu valodā": "german",
    "franču valodā": "french",
    "krievu valodā": "russian",
}
LANGUAGE_SLOT = {"angļu valodā", "franču valodā", "vācu valodā", "krievu valodā"}

# Испытание в тексте -> метка (formula_term.subject у entrance_exam); подписи
# лежат в словарях: calculator.termKinds.entrance_exam_<метка>
ENTRANCE_LABELS = (
    ("praktiskais pārbaudījums vizuālajā mākslā", "art_test"),
    ("intervija", "interview"),
)


@dataclass
class ParsedFormula:
    terms: list[ParsedTerm] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)  # почему формулу нельзя брать в базу
    scope: str = ""  # "pilna laika studijās" и т.п.; пусто — на все формы обучения

    @property
    def ok(self) -> bool:
        return bool(self.terms) and not self.problems


@dataclass
class ParsedProgramme:
    block: str
    doc_name: str
    header: str
    excerpt: str
    slugs: list[str]
    deleted: bool
    ce_formula: ParsedFormula | None  # 1. variants vasaras uzņemšanā
    note: str | None  # почему формулы нет (два варианта 1.a/1.b, нет блока 1. varianta)
    has_early_admission: bool


def load_text(pdf_path: Path = PDF_PATH) -> str:
    reader = pypdf.PdfReader(str(pdf_path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _number(text: str) -> float:
    return float(text.replace(",", ".").replace(" ", ""))


# Числовая часть слагаемого "(k x m = p)", иногда в двойных скобках и с
# разорванными переносом цифрами: "(1 ,5 x 100 = 1 50)". Пробелы внутри чисел
# убираются, а правильность склейки страхует проверка k*m == p.
NUMBERS_RE = re.compile(r"\(\s*\(?\s*([0-9][0-9 ]*(?:[.,] ?[0-9 ]+)?)\s*x\s*([0-9][0-9 ]*)\s*=\s*([0-9][0-9 ]*)\s*\)")


def split_terms(formula_text: str) -> list[str]:
    """Делит формулу по " + " на нулевой глубине скобок: внутри скобок
    ("(vai vidējā atzīme algebrā un ģeometrijā)") плюс слагаемых не разделяет."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in formula_text:
        if char == "(":
            depth += 1
        elif char == ")":
            # в документе бывает лишняя ")": "(1 x 100 = 100))" (Bioloģija un
            # biomedicīna) — глубину ниже нуля не опускаем
            depth = max(0, depth - 1)
        if char == "+" and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [re.sub(r"\s+", " ", part).strip(" ;.") for part in parts if part.strip(" ;.")]


CE_AVERAGE_PREFIX = "ce kopvērtējumu vidējais vērtējums"
# группа 1 — предмет(ы) CE, "kopvērtējums" не всегда есть в тексте перед "procentos"
CE_PROCENTOS_RE = re.compile(r"^ce (.+?) (?:kopvērtējums )?procentos")


def _normalize(description: str) -> str:
    """Нижний регистр, схлопнутые пробелы + починка разрывов слов, которые PDF
    местами вставляет: "c e kopvērtējumu v idējais", "i estāj…". Общая часть
    для formulas_lu.py и requirements_lu.py — оба разбирают один документ."""
    text = re.sub(r"\s+", " ", description).strip(" ;,.+(").lower()
    for broken, fixed in (("c e ", "ce "), ("v idējais", "vidējais"), ("i estāj", "iestāj")):
        text = text.replace(broken, fixed)
    return text


def _ce_phrase_parts(text: str) -> list[str] | None:
    """Части предмета(ов) из «CE <phrase> [kopvērtējums] procentos» —
    len==1 обычное слагаемое, len>=2 альтернатива «vai CE …». None — не
    такая структура (среднее по CE, испытание, оценка, нераспознанное)."""
    if text.startswith(CE_AVERAGE_PREFIX):
        return None
    match = CE_PROCENTOS_RE.match(text)
    if not match:
        return None
    return [p.strip() for p in re.split(r",?\s*vai\s+ce\s+", match.group(1))]


def _classify(description: str) -> tuple[str, str | None] | str:
    """(kind, subject) или строка с причиной, почему слагаемое не берётся."""
    text = _normalize(description)

    if text.startswith(CE_AVERAGE_PREFIX):
        return ("ce_average", None)

    parts = _ce_phrase_parts(text)
    if parts is not None:
        if len(parts) == 1:
            subject = CE_SUBJECTS.get(parts[0])
            return ("ce", subject) if subject else f"неизвестный предмет CE: «{parts[0]}»"
        # язык: любые ≥2 из {en, fr, de, ru} с английским — один слот "english"
        # (так уже принято для всех формул ЛУ; п. 1.4 документа называет языки
        # равноправными)
        if set(parts) <= LANGUAGE_SLOT and "angļu valodā" in parts:
            return ("ce", "english")
        phrase = " vai CE ".join(parts)
        return f"альтернатива между экзаменами (сколько брать, если сданы несколько, документ не говорит): «{phrase}»"

    for marker, label in ENTRANCE_LABELS:
        if marker in text:
            return ("entrance_exam", label)
    if "iestājpārbaudījums" in text:
        return ("entrance_exam", None)

    if text.startswith("vidējās izglītības dokumenta gada"):
        match = re.match(r"^vidējās izglītības dokumenta gada atzīme (\w+ ?\w*?)$", text)
        if match and match.group(1) in CE_SUBJECTS:
            return ("certificate", CE_SUBJECTS[match.group(1)])
        return f"оценка аттестата в формуле 1-го варианта: «{text[:80]}»"

    return f"нераспознанное слагаемое: «{text[:90]}»"


def parse_formula(text: str) -> ParsedFormula:
    """Формула вида "слагаемое (k x m = p) + слагаемое (k x m = p) + …"."""
    result = ParsedFormula()
    total_all = 0.0
    total_required = 0.0

    for piece in split_terms(text):
        numbers = NUMBERS_RE.search(piece)
        if not numbers:
            result.problems.append(f"в слагаемом нет (k x m = p): «{piece[:70]}»")
            continue
        coefficient, scale, points = (_number(numbers.group(i)) for i in (1, 2, 3))
        if abs(coefficient * scale - points) > 0.01:
            result.problems.append(f"арифметика не сходится: {coefficient:g} x {scale:g} != {points:g}")
        # "ja nav CE …, tad 0" / "netiek kārtots, tad 0": слагаемое необязательно
        optional = "tad 0" in piece
        total_all += points
        if not optional:
            total_required += points

        classified = _classify(piece[: numbers.start()])
        if isinstance(classified, str):
            result.problems.append(classified)
        else:
            kind, subject = classified
            result.terms.append(ParsedTerm(kind, subject, coefficient, optional))

    # Сумма по шкале 1000: либо со всеми слагаемыми (необязательное вступительное
    # испытание добирает до 1000), либо без необязательных (необязательное CE
    # "ja nav CE …, tad 0" даёт сверху +100: максимум тогда 1100, п. 1.10 этого
    # не оговаривает — человек сверяет по excerpt).
    if abs(total_all - SCALE) > 0.01 and abs(total_required - SCALE) > 0.01:
        result.problems.append(f"сумма максимальных баллов {total_all:g} (без необязательных {total_required:g}), а должна быть {SCALE}")
    if result.terms and not any(t.kind == "ce" for t in result.terms):
        result.problems.append("в формуле нет ни одного CE")
    return result


V1_HEAD = re.compile(r"^vērtējuma aprēķināšanas formulas (1(?:\.[ab])?)\.? variants vasaras uzņemšanā([^:]*):\s*(.*)$", re.S)


def _find_v1_texts(block_text: str) -> tuple[list[str], str | None]:
    """Сырые тексты формулы 1-го варианта (CE) для очной формы — один на
    обычный блок, несколько на блок с подпрограммами. Общая часть для
    formulas_lu.py (нужны веса) и requirements_lu.py (нужны только
    предметы — подпрограммы с разными весами, но одинаковым набором
    предметов для требований не проблема, поэтому решение "брать или нет"
    здесь не принимается, только сбор текстов).

    Берём только чистый "1. variants". Не берём:
    - "1.a"/"1.b": два варианта с разными весами, а как выбирается между ними,
      общая часть документа не говорит;
    - "nepilna laika" (заочное): в каталоге программа одна, калькулятор её
      страницы считает по очной форме; заочная остаётся только в excerpt."""
    found: list[tuple[str, str, str]] = []  # (метка варианта, форма обучения, текст формулы)
    for bullet in re.split(r"\n\s*•", block_text)[1:]:
        flat = re.sub(r"\s+", " ", bullet).strip()
        match = V1_HEAD.match(flat)
        if match:
            found.append((match.group(1), match.group(2).strip(), match.group(3)))

    if not found:
        return [], "в блоке нет формулы 1-го варианта (CE)"
    if any(label != "1" for label, _, _ in found):
        return [], "варианты 1.a/1.b: как выбирается между ними, документ не говорит — вопрос приёмной комиссии"

    full = [item for item in found if "nepilna" not in item[1]]
    if not full:
        return [], "в блоке нет формулы 1-го варианта для очной формы"
    return [item[2] for item in full], None


def _pick_v1_formula(block_text: str) -> tuple[ParsedFormula | None, str | None]:
    """Формула 1-го варианта (CE) с весами — для записи в formula/formula_term.
    Требует РОВНО один текст (см. _find_v1_texts); подпрограммы с разными
    весами сюда не годятся — программа в каталоге одна, а показать чужой
    набор весов — соврать (для требований этого ограничения нет,
    см. requirements_lu.py)."""
    texts, note = _find_v1_texts(block_text)
    if note:
        return None, note
    parsed = [parse_formula(text) for text in texts]
    signatures = {tuple((t.kind, t.subject, t.coefficient, t.optional) for t in f.terms) for f in parsed}
    if len(signatures) > 1:
        return None, f"{len(texts)} формул 1-го варианта (подпрограммы) с разными весами — в каталоге программа одна"
    return parsed[0], None


def parse_document(text: str) -> list[ParsedProgramme]:
    start = text.find("2. Uzņemšanas prasības un kritēriji īsā cikla")
    if start == -1:
        raise ValueError("не нашёл раздел 2 документа")
    body = text[start:]
    heads = list(re.finditer(r"\n(2\.\d+\.\d+\.)\s+", body))

    programmes: list[ParsedProgramme] = []
    for index, head in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(body)
        block_text = body[head.start() : end]
        excerpt = re.sub(r"[ \t]+", " ", block_text).strip()

        header_end = block_text.find("•")
        header = re.sub(r"\s+", " ", block_text[: header_end if header_end != -1 else 200]).strip()
        header = re.sub(r"^2\.\d+\.\d+\.\s*", "", header)
        deleted = "Svītrots" in header
        doc_name = re.split(r"\s+[–-]\s+", header, maxsplit=1)[0].strip().replace("  ", " ")

        ce_formula, note = _pick_v1_formula(block_text)
        flat_block = re.sub(r"\s+", " ", block_text)

        programmes.append(
            ParsedProgramme(
                block=head.group(1).rstrip("."),
                doc_name=doc_name,
                header=header,
                excerpt=excerpt,
                slugs=LU_SLUGS.get(doc_name, []),
                deleted=deleted,
                ce_formula=ce_formula,
                note=note,
                has_early_admission="formula agrajā uzņemšanā" in flat_block,
            )
        )
    return programmes


def report(programmes: list[ParsedProgramme]) -> None:
    ok = [p for p in programmes if p.ce_formula and p.ce_formula.ok and p.slugs and not p.deleted]
    print(f"блоков в документе: {len(programmes)}; пригодных к записи: {len(ok)}")
    for p in programmes:
        if p.deleted:
            print(f"  [{p.block}] удалён документом: {p.header[:80]}")
        elif not p.slugs:
            print(f"  [{p.block}] НЕТ СООТВЕТСТВИЯ в каталоге: «{p.doc_name}»")
        elif p.ce_formula is None:
            print(f"  [{p.block}] «{p.doc_name}»: {p.note}")
        elif not p.ce_formula.ok:
            print(f"  [{p.block}] «{p.doc_name}»: не берётся — " + "; ".join(p.ce_formula.problems))


# --- запись в базу ---------------------------------------------------------

SOURCE_URL = (
    "https://www.lu.lv/fileadmin/user_upload/LU.LV/www.lu.lv/"
    "Gribu_studet/Uznemsanas_dokumenti/uzn_prasibas_pamat_26_27.pdf"
)
SOURCE_DOC = (
    "Uzņemšanas prasības un kritēriji pamatstudiju programmās 2026./2027. "
    "akadēmiskajā gadā, 2. sadaļa (LU rīkojums Nr. 1-4/506, 27.11.2025., "
    "ar grozījumiem līdz 03.07.2026.)"
)
VALID_FROM = date(2025, 11, 27)  # дата rīkojums; так же принято для формул Вентспилса и РТУ
COPY_PATH = "docs/source-documents/lu/uzn-prasibas-pamat-2026-27.pdf"


def seed(programmes: list[ParsedProgramme], apply: bool) -> None:
    """Черновики формул ЛУ в базу (см. formula_drafts.py). Без --apply —
    только показывает, что было бы записано."""
    ready = [p for p in programmes if p.ce_formula and p.ce_formula.ok and p.slugs and not p.deleted]
    drafts = [Draft(p.block, p.slugs, p.ce_formula.terms, p.excerpt) for p in ready]  # type: ignore[union-attr]

    protocol = None
    if apply:
        from seed_formulas import source_protocol

        protocol = source_protocol(
            number="1-4/506 (grozījumi: 1-4/22, 1-4/105, 1-4/167, 1-4/195, 1-4/250)",
            doc_date=date(2026, 7, 3),
            copy_path=COPY_PATH,
            fetched_on=date(2026, 9, 20),
        )
    meta = DocumentMeta("lu", SOURCE_URL, SOURCE_DOC, VALID_FROM, protocol or {})
    write_drafts(meta, drafts, apply)


# --- самотест: живые куски документа ------------------------------------

def selftest() -> None:
    def terms(text: str) -> list[tuple]:
        result = parse_formula(text)
        assert result.ok, result.problems
        return [(t.kind, t.subject, t.coefficient, t.optional) for t in result.terms]

    # обычная формула, язык — альтернатива из трёх
    assert terms(
        "CE latviešu valodā kopvērtējums procentos (1,5 x 100 = 150) + CE angļu valodā vai CE franču valodā, "
        "vai CE vācu valodā kopvērtējums procentos (1 x 100 = 100) + CE matemātikā kopvērtējums procentos "
        "(6,5 x 100 = 650) + CE kopvērtējumu vidējais vērtējums procentos, kuru aprēķina no personas "
        "nokārtotajiem CE visos mācību priekšmetos (1 x 100 = 100);"
    ) == [
        ("ce", "latvian", 1.5, False),
        ("ce", "english", 1.0, False),
        ("ce", "mathematics", 6.5, False),
        ("ce_average", None, 1.0, False),
    ]

    # необязательное CE: максимум 1100, без него ровно 1000
    optional = terms(
        "CE latviešu valodā kopvērtējums procentos (3,5 x 100 = 350) + CE matemātikā kopvērtējums procentos "
        "(3,5 x 100 = 350) + CE angļu valodā kopvērtējums procentos (2 x 100 = 200) + CE kopvērtējumu vidējais "
        "vērtējums procentos, kuru aprēķina no personas nokārtotajiem CE visos mācību priekšmetos (1 x 100 = 100) "
        "+ CE sociālajās zinātnēs procentos ((1 x 100 = 100), ja nav CE sociālajās zinātnēs, tad 0);"
    )
    assert optional[-1] == ("ce", "socialstudies", 1.0, True)

    # опечатка документа: лишняя ")" не должна склеивать слагаемые
    assert len(
        terms(
            "CE latviešu valodā kopvērtējums procentos (1,5 x 100 = 150) + CE angļu valodā kopvērtējums procentos "
            "(1 x 100 = 100)) + CE matemātikā kopvērtējums procentos (2,5 x 100 = 250) + CE bioloģijā "
            "kopvērtējums procentos (4 x 100 = 400) + CE kopvērtējumu vidējais vērtējums procentos, kuru aprēķina "
            "no personas nokārtotajiem CE visos mācību priekšmetos (1 x 100 = 100);"
        )
    ) == 5

    # цифры, разорванные переносом страницы: "(1 ,5 x 100 = 1 50)"
    broken = parse_formula(
        "CE latviešu valodā kopvērtējums procentos (1 ,5 x 100 = 1 50) + CE matemātikā kopvērtējums procentos "
        "(8,5 x 100 = 850);"
    )
    assert broken.ok, broken.problems

    # арифметика и сумма проверяются: 1000 не набирается — формула не берётся
    assert not parse_formula("CE matemātikā kopvērtējums procentos (2 x 100 = 200);").ok
    assert not parse_formula("CE matemātikā kopvērtējums procentos (2 x 100 = 300);").ok

    # альтернатива между предметами не берётся молча
    alternative = parse_formula(
        "CE fizikā vai CE ķīmijā, vai CE bioloģijā kopvērtējums procentos (10 x 100 = 1000);"
    )
    assert not alternative.ok and "альтернатива" in alternative.problems[0]
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        parsed = parse_document(load_text())
        report(parsed)
        seed(parsed, apply="--apply" in sys.argv)
