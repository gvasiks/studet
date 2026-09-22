"""Требования к экзаменам RSU — отдельно от формулы (план 2026-09-21,
неделя 4/5, пункт 02, порция 1). Тот же документ и то же приложение на
программу, что и formulas_rsu.py, но вопрос беднее: не "с каким весом",
а "какой CE вообще нужен".

Разбирает БОЛЬШЕ приложений, чем formulas_rsu.py, потому что RSU-документ
кроме CE-альтернатив ("CE ķīmijā vai bioloģijā") использует и АТТЕСТАТНЫЕ
альтернативы ("gala atzīme bioloģijā vai dabaszinībās") — как ФОРМУЛА они
одинаково неразборчивы (сколько брать, если сдано несколько, не сказано),
но как ТРЕБОВАНИЕ CE-альтернатива разбирается ("нужен один из"), а
аттестатная — НЕТ: это не централизованный экзамен, для него нет уровня
augstākais/optimālais/vispārīgais и анкета про него не спрашивает
(programme_requirement.subject — тот же код, что и у formula_term CE-
слагаемого, см. миграцию 20260922120000). Поэтому в отличие от LU, где всё
было CE, здесь классификатор для требований СТРОЖЕ formulas_rsu.py._classify
по источнику (берёт только явные "CE …"), хотя и мягче по альтернативам
внутри CE (не отбрасывает несколько разных предметов, а собирает группу).

OSPPP (вступительное испытание, шкала вне CE) и "iestājpārbaudījums" в
требования тоже не попадают — те же причины, что у аттестата.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date

from formula_drafts import DocumentMeta, RequirementDraft, write_requirement_drafts
from formulas_rsu import (
    BULLET_LINE_RE,
    CE_SUBJECTS,
    COPY_PATH,
    SOURCE_DOC,
    SOURCE_URL,
    VALID_FROM,
    load_text,
    parse_document,
)


@dataclass
class ParsedRequirement:
    number: str
    name: str
    excerpt: str
    slugs: list[str]
    groups: list[list[str]] = field(default_factory=list)
    note: str | None = None


def _classify_for_requirement(body: str) -> list[str] | None:
    """Список кодов предметов (альтернативная группа) для CE-слагаемого,
    None — если слагаемое не CE (OSPPP, iestājpārbaudījums, gala atzīme
    аттестата) или предмет не распознан."""
    text = re.sub(r"\s+", " ", body).strip(" ,.;").lower()
    text = re.sub(r"-\s+", "", text)
    text = text.replace("vērtēj ums", "vērtējums")

    if not text.startswith("ce "):
        return None
    text = text[len("ce ") :]

    match = re.match(
        r"^(?:vērtējums )?(.+?)(?:\s+vai starptautiskas testēšanas institūcijas pārbaudījuma vērtējums (.+))?$",
        text,
    )
    if not match:
        return None
    subject_phrase = match.group(1).strip()
    if match.group(2):
        return ["english"] if subject_phrase in ("svešvalodā", "angļu valodā") else None
    parts = [p.strip() for p in subject_phrase.split(" vai ")]
    codes = [CE_SUBJECTS.get(p) for p in parts]
    return None if any(code is None for code in codes) else codes


def _groups_from_criteria(criteria_text: str) -> list[list[str]]:
    groups: list[list[str]] = []
    flat = re.sub(r"\s+", " ", criteria_text)
    for bullet in re.split(r"•", flat)[1:]:
        match = BULLET_LINE_RE.match(bullet.strip(" ,.;"))
        if not match:
            continue
        codes = _classify_for_requirement(match.group(2))
        if codes:
            groups.append(codes)
    return groups


def extract_requirements(criteria_text: str) -> tuple[list[list[str]] | None, str | None]:
    groups = _groups_from_criteria(criteria_text)
    if not groups:
        return None, "в критериях нет ни одного распознанного CE-предмета"
    return groups, None


def parse_all(text: str) -> list[ParsedRequirement]:
    appendices = parse_document(text)
    out = []
    for a in appendices:
        if not a.slugs or not a.criteria_text:
            continue
        groups, note = extract_requirements(a.criteria_text)
        out.append(ParsedRequirement(a.number, a.name, a.excerpt, a.slugs, groups or [], note))
    return out


def report(items: list[ParsedRequirement]) -> None:
    ok = [item for item in items if item.note is None]
    print(f"приложений с распознанными требованиями: {len(ok)} из {len(items)} (с соответствием слагу в каталоге)")
    for item in items:
        if item.note:
            print(f"  [{item.number}] {item.name[:60]}: {item.note}")


def seed(items: list[ParsedRequirement], apply: bool) -> None:
    ready = [item for item in items if item.note is None]
    drafts = [
        RequirementDraft(block=f"Nr. {item.number}", slugs=item.slugs, groups=item.groups, excerpt=item.excerpt)
        for item in ready
    ]
    protocol = {}
    if apply:
        from seed_formulas import source_protocol

        protocol = source_protocol(
            number="1-PB-9/36/2025 (grozījumi: 1-PB-9/14/2026, 1-PB-9/29/2026)",
            doc_date=date(2026, 5, 14),
            copy_path=COPY_PATH,
            fetched_on=date(2026, 9, 20),
        )
    write_requirement_drafts(DocumentMeta("rsu", SOURCE_URL, SOURCE_DOC, VALID_FROM, protocol), drafts, apply)


def selftest() -> None:
    text = (
        "Studiju programmas X reflektantus imatrikulē saskaņā ar uzņemšanas rezultātu kopvērtējumu, kurā: "
        "• 10% no kopējā vērtējuma veido CE vērtējums matemātikā, "
        "• 45% no kopējā vērtējuma veido CE vērtējums latviešu valodā, "
        "• 45% no kopējā vērtējuma veido CE vērtējums svešvalodā vai starptautiskas tes- tēšanas institūcijas "
        "pārbaudījuma vērtējums svešvalodā."
    )
    groups, note = extract_requirements(text)
    assert note is None, note
    assert groups is not None
    assert ["mathematics"] in groups and ["latvian"] in groups and ["english"] in groups
    assert len(groups) == 3, groups

    # CE-альтернатива между двумя разными предметами: для требования — группа,
    # хотя для формулы (formulas_rsu.py) это неразборчивый случай
    alt = (
        "Studiju programmas Z reflektantus imatrikulē saskaņā ar kopvērtējumu, kurā: "
        "• 85% no kopējā vērtējuma veido CE vērtējums ķīmijā vai bioloģijā, "
        "• 15% no kopējā vērtējuma veido CE vērtējums matemātikā."
    )
    groups2, note2 = extract_requirements(alt)
    assert note2 is None
    assert ["chemistry", "biology"] in groups2
    assert ["mathematics"] in groups2

    # аттестатная альтернатива (не CE) — не выдумываем требование, просто
    # пропускаем это слагаемое, а не всё приложение целиком
    cert = (
        "Studiju programmas Y reflektantus imatrikulē saskaņā ar kopvērtējumu, kurā: "
        "• 85% no kopējā vērtējuma veido gala atzīme bioloģijā vai dabaszinībās, "
        "• 15% no kopējā vērtējuma veido CE vērtējums matemātikā."
    )
    groups3, note3 = extract_requirements(cert)
    assert note3 is None
    assert groups3 == [["mathematics"]], groups3

    # чистый OSPPP — CE-предметов нет вовсе, приложение не берётся
    osppp_only = "• 100% no kopējā vērtējuma ietekmē iestājpārbaudījums OSPPP."
    groups4, note4 = extract_requirements(osppp_only)
    assert groups4 is None and note4 is not None

    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        parsed = parse_all(load_text())
        report(parsed)
        seed(parsed, apply="--apply" in sys.argv)
