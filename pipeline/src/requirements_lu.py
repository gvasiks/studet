"""Требования к экзаменам ЛУ — отдельно от формулы (план 2026-09-21,
неделя 4/5, пункт 02). Тот же документ, что и formulas_lu.py
(`docs/source-documents/lu/uzn-prasibas-pamat-2026-27.pdf`), но другой,
более бедный вопрос: не "с каким весом считать баллы", а "какие экзамены
вообще нужны". Это позволяет разобрать БОЛЬШЕ блоков, чем formulas_lu.py:

- "CE fizikā vai CE ķīmijā, vai CE bioloģijā" как ФОРМУЛА не разбирается
  (неясно, брать лучший из трёх или суммировать), а как ТРЕБОВАНИЕ —
  однозначно: нужен хотя бы один из трёх. Записывается одной
  альтернативной группой (formula_drafts.RequirementGroup ниже).
- подпрограммы с разными весами (Filoloģija, Skolotājs) для формулы не
  годятся (программа в каталоге одна, веса разные), а для требований —
  годятся, ЕСЛИ им нужен один и тот же набор предметов: тогда неважно,
  какая подпрограмма конкретно, предметы одни и те же.

Не разбирается по-прежнему:
- "1.a"/"1.b" (Fizika, Ķīmija): физика в 1.a — необязательна ("ja nav CE
  fizikā, tad 0"), в 1.b — обязательна. Это разное ТРЕБОВАНИЕ, не просто
  разный вес, выбрать самим — соврать;
- подпрограммы, где предметы всё же различаются (не только веса);
- удалённые документом блоки (те же 2.2.3).

Как и formulas_lu.py: ничего не додумывает, дословный текст блока — в
source_excerpt, протокол источника обязателен для подтверждения.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from formula_drafts import DocumentMeta, RequirementDraft, write_requirement_drafts
from formulas_lu import (
    CE_SUBJECTS,
    LANGUAGE_SLOT,
    NUMBERS_RE,
    _ce_phrase_parts,
    _find_v1_texts,
    _normalize,
    load_text,
    parse_document,
    split_terms,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COPY_PATH = "docs/source-documents/lu/uzn-prasibas-pamat-2026-27.pdf"
SOURCE_URL = (
    "https://www.lu.lv/fileadmin/user_upload/LU.LV/www.lu.lv/"
    "Gribu_studet/Uznemsanas_dokumenti/uzn_prasibas_pamat_26_27.pdf"
)
SOURCE_DOC = (
    "Uzņemšanas prasības un kritēriji pamatstudiju programmās 2026./2027. "
    "akadēmiskajā gadā, 2. sadaļa (LU rīkojums Nr. 1-4/506, 27.11.2025., "
    "ar grozījumiem līdz 03.07.2026.)"
)
VALID_FROM = date(2025, 11, 27)


@dataclass
class ParsedRequirement:
    block: str
    doc_name: str
    excerpt: str
    slugs: list[str]
    # список альтернативных групп: каждая группа — список кодов предметов,
    # "нужен хотя бы один из них" (группа из одного предмета — обязателен сам)
    groups: list[list[str]] = field(default_factory=list)
    note: str | None = None


def _classify_for_requirement(description: str) -> list[str] | None:
    """Список кодов предметов (альтернативная группа) для CE-слагаемого,
    None — если слагаемое не про конкретный CE-предмет (среднее по всем CE,
    вступительное испытание, оценка аттестата — их не требуем как экзамен),
    не распознана структура «CE ... procentos», или предмет не распознан
    (лучше пропустить программу, чем ошибиться). Разбор фразы — общий с
    formulas_lu.py (_ce_phrase_parts): здесь та же грамматика, только
    политика мягче — альтернатива между РАЗНЫМИ предметами (не только
    языковой слот) не отбрасывается, а становится группой."""
    parts = _ce_phrase_parts(_normalize(description))
    if parts is None:
        return None
    if set(parts) <= LANGUAGE_SLOT and "angļu valodā" in parts:
        return ["english"]
    codes = [CE_SUBJECTS.get(p) for p in parts]
    if any(code is None for code in codes):
        return None  # неизвестный предмет — не рискуем
    return codes


def _groups_from_text(formula_text: str) -> list[list[str]]:
    groups: list[list[str]] = []
    for piece in split_terms(formula_text):
        numbers = NUMBERS_RE.search(piece)
        if not numbers:
            continue
        codes = _classify_for_requirement(piece[: numbers.start()])
        if codes:
            groups.append(codes)
    return groups


def extract_requirements(block_text: str) -> tuple[list[list[str]] | None, str | None]:
    texts, note = _find_v1_texts(block_text)
    if note:
        return None, note

    variants = [_groups_from_text(text) for text in texts]
    # подпрограммы (несколько текстов): требования годятся, только если
    # набор предметов одинаковый — веса могут отличаться, это требований
    # не касается
    signatures = {frozenset(frozenset(g) for g in variant) for variant in variants}
    if len(signatures) > 1:
        return None, f"{len(texts)} формул (подпрограммы) требуют разных предметов — в каталоге программа одна"
    if not variants[0]:
        return None, "в формуле нет ни одного распознанного CE-предмета"
    return variants[0], None


def parse_all(text: str) -> list[ParsedRequirement]:
    programmes = parse_document(text)
    out = []
    for p in programmes:
        if p.deleted or not p.slugs:
            continue
        groups, note = extract_requirements(p.excerpt)
        out.append(ParsedRequirement(block=p.block, doc_name=p.doc_name, excerpt=p.excerpt, slugs=p.slugs, groups=groups or [], note=note))
    return out


def report(items: list[ParsedRequirement]) -> None:
    ok = [item for item in items if item.note is None]
    print(f"программ с распознанными требованиями: {len(ok)} из {len(items)} (с соответствием слагу в каталоге)")
    for item in items:
        if item.note:
            print(f"  [{item.block}] «{item.doc_name}»: {item.note}")


def seed(items: list[ParsedRequirement], apply: bool) -> None:
    ready = [item for item in items if item.note is None]
    drafts = [
        RequirementDraft(block=f"LU {item.block}", slugs=item.slugs, groups=item.groups, excerpt=item.excerpt)
        for item in ready
    ]
    protocol = {}
    if apply:
        from seed_formulas import source_protocol

        protocol = source_protocol(
            number="1-4/506 (grozījumi: 1-4/22, 1-4/105, 1-4/167, 1-4/195, 1-4/250)",
            doc_date=date(2026, 7, 3),
            copy_path=COPY_PATH,
            fetched_on=date(2026, 9, 20),
        )
    write_requirement_drafts(DocumentMeta("lu", SOURCE_URL, SOURCE_DOC, VALID_FROM, protocol), drafts, apply)


def selftest() -> None:
    # LU "Ārstniecība" (2.7.2): альтернатива физика/химия/биология —
    # формула не разбирается (formulas_lu.py), требование — разбирается
    block = (
        "2.7.2. Ārstniecība – otrā cikla profesionālās augstākās izglītības studiju programma pilna laika "
        "klātienes studijām: \n"
        "• studiju valoda: latviešu; \n"
        "• vērtējuma aprēķināšanas formulas 1. variants vasaras uzņemšanā : CE latviešu valodā "
        "kopvērtējums procentos (1 x 100 = 100) + CE angļu valodā vai CE franču valodā, vai CE vācu valodā "
        "kopvērtējums procentos (1 x 100 = 100) + CE matemātikā kopvērtējums procentos (1 x 100 = 100) + "
        "CE fizikā vai CE ķīmijā, vai CE bioloģijā kopvērtējums procentos (6 x 100 = 600) + CE kopvērtējumu "
        "vidējais vērtējums procentos, kuru aprēķina no personas nokārtotajiem CE visos mācību priekšmetos "
        "(1 x 100 = 100); \n"
        "• vērtējuma aprēķināšanas formulas 2. variants vasaras uzņemšanā : vidējās izglītības ...;"
    )
    groups, note = extract_requirements(block)
    assert note is None, note
    assert groups is not None
    assert ["latvian"] in groups
    assert ["english"] in groups
    assert ["mathematics"] in groups
    assert ["physics", "chemistry", "biology"] in groups
    assert len(groups) == 4, groups

    # 1.a/1.b — по-прежнему не берём
    fizika_block = (
        "2.2.4. Fizika – akadēmiskā bakalaura studiju programma pilna laika klātienes studijām: \n"
        "• vērtējuma aprēķināšanas formulas 1.a variants vasaras uzņemšanā : CE matemātikā kopvērtējums "
        "procentos (7,5 x 100 = 750);\n"
        "• vērtējuma aprēķināšanas formulas 1.b variants vasaras uzņemšanā : CE fizikā kopvērtējums "
        "procentos (8 x 100 = 800);"
    )
    groups2, note2 = extract_requirements(fizika_block)
    assert groups2 is None and note2 is not None

    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        parsed = parse_all(load_text())
        report(parsed)
        seed(parsed, apply="--apply" in sys.argv)
