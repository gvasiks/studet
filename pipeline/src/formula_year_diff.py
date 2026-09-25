"""Дифф формулы год-к-году (план 2026-09-21, разбор бизнес-процессов,
предложение №6). Компаньон к годовому циклу сверки (пункт 08): П6/П8
закрывают формулу прошлого года (`valid_to`) и создают новую при повторном
разборе, но ничего до сих пор не сравнивало ЧИСЛА старой и новой формулы
для одной и той же программы. Резкий скачок коэффициента (опечатка при
разборе нового документа, а не реальное изменение правил вуза) можно было
заметить только вручную, построчно, при подтверждении — то есть в декабре,
в момент максимальной спешки, когда как раз меньше всего внимания на такие
детали.

Это не подтверждение и не проверка на правильность (человек по-прежнему
решает через Supabase Studio, правило 6 CLAUDE.md) — только сигнал
"посмотри сюда внимательнее" перед тем, как подтверждать.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

# Отношение новый/старый коэффициент за этой чертой — подозрительно
# независимо от масштаба вуза (у LU сумма 1000, у RSU — 100, но скачок
# "было 0.2, стало 2.0" одинаково подозрителен в обеих шкалах).
SUSPICIOUS_RATIO = 3.0


@dataclass
class TermDiff:
    kind: str
    subject: str | None
    old_coefficient: float | None  # None — слагаемого не было в старой формуле
    new_coefficient: float | None  # None — слагаемое пропало в новой формуле
    suspicious: bool


@dataclass
class ProgrammeDiff:
    programme_id: str
    programme_name: str
    old_valid_from: str
    new_valid_from: str
    term_diffs: list[TermDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(d.old_coefficient != d.new_coefficient for d in self.term_diffs)

    @property
    def has_suspicious(self) -> bool:
        return any(d.suspicious for d in self.term_diffs)


def _key(term: dict) -> tuple[str, str | None]:
    return (term["kind"], term["subject"])


def diff_terms(old_terms: list[dict], new_terms: list[dict]) -> list[TermDiff]:
    """Чистая функция — сравнение по (kind, subject), без обращения к базе.
    Слагаемое, которого нет в одной из формул, — тоже диф (old/new=None),
    не только изменившийся коэффициент: пропавшее или появившееся
    слагаемое так же стоит человеческого внимания, как и изменившийся вес."""
    old_by_key = {_key(t): t["coefficient"] for t in old_terms}
    new_by_key = {_key(t): t["coefficient"] for t in new_terms}

    diffs = []
    for key in sorted(set(old_by_key) | set(new_by_key), key=lambda k: (k[0], k[1] or "")):
        old_c = old_by_key.get(key)
        new_c = new_by_key.get(key)
        suspicious = False
        if old_c is not None and new_c is not None and old_c > 0 and new_c > 0:
            ratio = new_c / old_c
            suspicious = ratio >= SUSPICIOUS_RATIO or ratio <= 1 / SUSPICIOUS_RATIO
        elif (old_c is None) != (new_c is None):
            suspicious = True  # слагаемое появилось или пропало целиком
        diffs.append(TermDiff(kind=key[0], subject=key[1], old_coefficient=old_c, new_coefficient=new_c, suspicious=suspicious))
    return diffs


def compute_programme_diffs(formula_rows: list[dict], terms_by_formula: dict[str, list[dict]]) -> list[ProgrammeDiff]:
    """formula_rows — строки formula (variant='ce'), отсортированные заранее
    по (programme_id, valid_from). Сравнивает только ДВЕ САМЫЕ СВЕЖИЕ строки
    на программу — более старая история (третий год подряд) пока не нужна:
    именно переход "было в прошлом году -> стало в этом" интересует
    годовой цикл."""
    by_programme: dict[str, list[dict]] = {}
    for row in formula_rows:
        by_programme.setdefault(row["programme_id"], []).append(row)

    diffs = []
    for programme_id, rows in by_programme.items():
        if len(rows) < 2:
            continue
        rows_sorted = sorted(rows, key=lambda r: r["valid_from"])
        old_row, new_row = rows_sorted[-2], rows_sorted[-1]
        term_diffs = diff_terms(
            terms_by_formula.get(old_row["id"], []),
            terms_by_formula.get(new_row["id"], []),
        )
        diffs.append(
            ProgrammeDiff(
                programme_id=programme_id,
                programme_name=new_row.get("programme_name", programme_id),
                old_valid_from=old_row["valid_from"],
                new_valid_from=new_row["valid_from"],
                term_diffs=term_diffs,
            )
        )
    return diffs


def format_report(diffs: list[ProgrammeDiff]) -> str:
    lines = []
    changed = [d for d in diffs if d.has_changes]
    suspicious = [d for d in diffs if d.has_suspicious]
    lines.append(f"программ с формулой в двух годах: {len(diffs)}; с изменениями: {len(changed)}; подозрительных: {len(suspicious)}")
    for d in changed:
        lines.append(f"\n{d.programme_name} ({d.old_valid_from} -> {d.new_valid_from}):")
        for t in d.term_diffs:
            if t.old_coefficient == t.new_coefficient:
                continue
            mark = " !!! ПОДОЗРИТЕЛЬНО" if t.suspicious else ""
            subject = t.subject or t.kind
            lines.append(f"  {subject}: {t.old_coefficient} -> {t.new_coefficient}{mark}")
    return "\n".join(lines)


def main() -> None:
    from dotenv import load_dotenv

    from db import get_service_client

    load_dotenv()
    client = get_service_client()

    rows = (
        client.table("formula")
        .select("id, programme_id, valid_from, programme!inner(name_lv, name_en)")
        .eq("variant", "ce")
        .order("valid_from")
        .execute()
        .data
    )
    for row in rows:
        programme = row.pop("programme")
        row["programme_name"] = programme.get("name_en") or programme.get("name_lv") or row["programme_id"]

    ids = [row["id"] for row in rows]
    terms = client.table("formula_term").select("formula_id, kind, subject, coefficient").in_("formula_id", ids).execute().data if ids else []
    terms_by_formula: dict[str, list[dict]] = {}
    for term in terms:
        terms_by_formula.setdefault(term["formula_id"], []).append(term)

    diffs = compute_programme_diffs(rows, terms_by_formula)
    print(format_report(diffs))


def selftest() -> None:
    # обычное, не подозрительное изменение (0.2 -> 0.25, в пределах порога)
    old_terms = [{"kind": "ce", "subject": "latvian", "coefficient": 0.2}, {"kind": "ce", "subject": "mathematics", "coefficient": 0.5}]
    new_terms = [{"kind": "ce", "subject": "latvian", "coefficient": 0.25}, {"kind": "ce", "subject": "mathematics", "coefficient": 0.5}]
    diffs = diff_terms(old_terms, new_terms)
    latvian = next(d for d in diffs if d.subject == "latvian")
    assert not latvian.suspicious, latvian
    math = next(d for d in diffs if d.subject == "mathematics")
    assert math.old_coefficient == math.new_coefficient

    # подозрительный скачок (0.2 -> 2.0, ×10)
    jump_terms = [{"kind": "ce", "subject": "latvian", "coefficient": 2.0}, {"kind": "ce", "subject": "mathematics", "coefficient": 0.5}]
    diffs2 = diff_terms(old_terms, jump_terms)
    latvian2 = next(d for d in diffs2 if d.subject == "latvian")
    assert latvian2.suspicious, latvian2

    # слагаемое пропало целиком — тоже подозрительно
    dropped_terms = [{"kind": "ce", "subject": "mathematics", "coefficient": 0.5}]
    diffs3 = diff_terms(old_terms, dropped_terms)
    latvian3 = next(d for d in diffs3 if d.subject == "latvian")
    assert latvian3.new_coefficient is None and latvian3.suspicious

    # живой баг (2026-09-25): sorted() падал на смешанных None/строка в
    # subject у одного и того же kind ("entrance_exam"/None против
    # "entrance_exam"/"osppp") — до фикса TypeError на реальных данных
    mixed_subject_old = [{"kind": "entrance_exam", "subject": None, "coefficient": 1.0}]
    mixed_subject_new = [{"kind": "entrance_exam", "subject": "osppp", "coefficient": 1.0}]
    diff_terms(mixed_subject_old, mixed_subject_new)  # не должно упасть

    # compute_programme_diffs: только 2 последние строки на программу учитываются
    rows = [
        {"id": "f1", "programme_id": "p1", "valid_from": "2024-01-01", "programme_name": "X"},
        {"id": "f2", "programme_id": "p1", "valid_from": "2025-01-01", "programme_name": "X"},
        {"id": "f3", "programme_id": "p1", "valid_from": "2026-01-01", "programme_name": "X"},
        {"id": "f4", "programme_id": "p2", "valid_from": "2026-01-01", "programme_name": "Y"},  # одна строка — не сравнивается
    ]
    terms_by_formula = {
        "f1": [{"kind": "ce", "subject": "latvian", "coefficient": 999}],  # старая история, не должна попасть в дифф
        "f2": old_terms,
        "f3": new_terms,
    }
    diffs4 = compute_programme_diffs(rows, terms_by_formula)
    assert len(diffs4) == 1, diffs4  # p2 пропущена — только 1 строка
    assert diffs4[0].old_valid_from == "2025-01-01" and diffs4[0].new_valid_from == "2026-01-01"

    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
