"""Подтверждение требований к экзаменам ПО ПРАВИЛУ: «совпадают с
подтверждённой формулой той же программы». Читайте сначала
docs/checks/REQUIREMENTS-REVIEW.md — этот скрипт исполняет решение
владельца, а не принимает его.

  python src/confirm_requirements_by_rule.py --batch venta            # только отчёт
  python src/confirm_requirements_by_rule.py --batch venta --apply    # подтвердить

Партия — решение владельца про вузы и число программ (BATCHES ниже).

Правило. Требования и формула взяты из одного документа вуза, формулу
человек уже проверил по этому документу. Если обязательные экзамены
формулы (CE-слагаемые без «ja nav CE …, tad 0» и пороги) — ровно те же,
что в черновике требований, черновик подтверждается. Иностранный язык в
требованиях — группа «английский | немецкий»
(formula_drafts.FOREIGN_LANGUAGE_CHOICE), в формуле — слот 'english': для
сверки это одно и то же.

Черновики без подтверждённой формулы этим правилом не покрыты — их
подтверждает владелец после просмотра списка (отдельное решение).
"""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import datetime, timezone

from formula_drafts import FOREIGN_LANGUAGE_CHOICE

# expected — сколько программ совпадало, когда владелец принимал решение;
# другое число — черновики менялись, решение их не покрывает.
BATCHES = {
    # Решение владельца 2026-10-18: «62 по правилу» — ЛУ 45, RSU 17
    # (REQUIREMENTS-REVIEW.md, «Сверка с подтверждёнными формулами»).
    "lu-rsu": {
        "universities": ["lu", "rsu"],
        "expected": 62,
        "verified_by": (
            "Gvasiks (подтверждение по правилу, решение владельца 2026-10-18: требования совпадают с подтверждённой "
            "формулой той же программы; 62 программы ЛУ и RSU — docs/checks/REQUIREMENTS-REVIEW.md)"
        ),
    },
    # Решение владельца 2026-10-21: «Подтвердить 7» (раздел «Ventspils»).
    "venta": {
        "universities": ["venta"],
        "expected": 7,
        "verified_by": (
            "Gvasiks (подтверждение по правилу, решение владельца 2026-10-21: требования совпадают с подтверждённой "
            "формулой той же программы; 7 программ Ventspils — docs/checks/REQUIREMENTS-REVIEW.md, «Ventspils»)"
        ),
    },
    # Решение владельца 2026-10-21: «Подтверждаю … требования 77 программ без
    # формулы» — список просмотрен им (REQUIREMENTS-REVIEW.md, «Без формулы» и
    # «Ventspils»). Правило другое: не сверка с формулой, а просмотр списка;
    # берутся программы БЕЗ подтверждённой формулы.
    # Решение владельца 2026-10-21: «Подтвердить 101» — у РТУ требования одни
    # на все программы (раздел 3 правил приёма), с формулой и без
    # (REQUIREMENTS-REVIEW.md, «РТУ»).
    "rtu": {
        "universities": ["rtu"],
        "whole_university": True,
        "expected": 101,
        "verified_by": (
            "Gvasiks (решение владельца 2026-10-21: требования РТУ — одна фраза раздела 3 правил приёма "
            "«obligātajiem CE – matemātikā, latviešu valodā un svešvalodā» для всех 101 программы; "
            "docs/checks/REQUIREMENTS-REVIEW.md, «РТУ»)"
        ),
    },
    "reviewed-no-formula": {
        "universities": ["lu", "rsu", "du", "lbtu", "venta"],
        "without_formula": True,
        # у этих двух есть черновик формулы (неподтверждённый) — в просмотренный
        # список «без формулы» они не входили, решение их не покрывает
        "exclude": {("lu", "business-process-management-lv"), ("lu", "finance-lv")},
        "expected": 77,
        "verified_by": (
            "Gvasiks (решение владельца 2026-10-21 после просмотра списка 77 программ без подтверждённой формулы — "
            "ЛУ 13, RSU 13, DU 22, LBTU 27, Ventspils 2; docs/checks/REQUIREMENTS-REVIEW.md)"
        ),
    },
}


def requirement_signature(rows: list[dict]) -> frozenset[frozenset[str]]:
    """Набор групп «нужен один из»; языковая группа — как слот 'english'."""
    groups: dict[str, set[str]] = defaultdict(set)
    singles: list[frozenset[str]] = []
    for row in rows:
        if row["alternative_group"]:
            groups[row["alternative_group"]].add(row["subject"])
        else:
            singles.append(frozenset([row["subject"]]))
    result = set(singles) | {frozenset(group) for group in groups.values()}
    language = frozenset(FOREIGN_LANGUAGE_CHOICE)
    return frozenset(frozenset(["english"]) if group == language else group for group in result)


def formula_signature(terms: list[dict], gates: list[dict]) -> frozenset[frozenset[str]]:
    subjects = {t["subject"] for t in terms if t["kind"] == "ce" and t["subject"] and not t["optional"]}
    subjects |= {g["subject"] for g in gates}
    return frozenset(frozenset([subject]) for subject in subjects)


def _selftest() -> None:
    requirement = [
        {"subject": "latvian", "alternative_group": None},
        {"subject": "english", "alternative_group": "g1"},
        {"subject": "german", "alternative_group": "g1"},
        {"subject": "mathematics", "alternative_group": None},
    ]
    formula = [
        {"kind": "ce", "subject": "latvian", "optional": False},
        {"kind": "ce", "subject": "english", "optional": False},
        {"kind": "ce", "subject": "mathematics", "optional": False},
        {"kind": "ce_average", "subject": None, "optional": False},
        {"kind": "ce", "subject": "socialstudies", "optional": True},
    ]
    assert requirement_signature(requirement) == formula_signature(formula, [])
    # лишний обязательный предмет в требованиях — не совпадение
    assert requirement_signature(requirement + [{"subject": "history", "alternative_group": None}]) != formula_signature(formula, [])
    # порог формулы — тоже обязательный экзамен
    assert formula_signature(formula, [{"subject": "chemistry"}]) != requirement_signature(requirement)
    # группа «физика | химия | биология» с формулой из одного предмета не совпадает
    group = [{"subject": s, "alternative_group": "g2"} for s in ("physics", "chemistry", "biology")]
    assert requirement_signature(group) != formula_signature([{"kind": "ce", "subject": "chemistry", "optional": False}], [])
    print("selftest: OK")


def main(batch_name: str, apply: bool) -> None:
    batch = BATCHES[batch_name]
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    from db import fetch_all, get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()
    sets = fetch_all(
        lambda: client.table("programme_requirement_set")
        .select("id, programme_id, programme(slug, university(slug)), programme_requirement(subject, alternative_group)")
        .is_("verified_at", "null")
        .is_("disputed_at", "null")
        .order("id")
    )
    formulas = fetch_all(
        lambda: client.table("formula")
        .select("id, programme_id, formula_term(kind, subject, optional), formula_gate(subject)")
        .eq("variant", "ce")
        .is_("valid_to", "null")
        .not_.is_("verified_at", "null")
        .order("id")
    )
    by_programme = {formula["programme_id"]: formula for formula in formulas}

    matching: list[dict] = []
    differing: list[str] = []
    for requirement_set in sets:
        formula = by_programme.get(requirement_set["programme_id"])
        if requirement_set["programme"]["university"]["slug"] not in batch["universities"]:
            continue
        if batch.get("whole_university"):
            # одно правило на весь вуз: все его черновики, с формулой и без
            matching.append(requirement_set)
            continue
        if batch.get("without_formula"):
            # партия «просмотрено владельцем»: только программы без формулы
            key = (requirement_set["programme"]["university"]["slug"], requirement_set["programme"]["slug"])
            if formula is None and key not in batch.get("exclude", set()):
                matching.append(requirement_set)
            continue
        if formula is None:
            continue
        name = f"{requirement_set['programme']['university']['slug']} {requirement_set['programme']['slug']}"
        if requirement_signature(requirement_set["programme_requirement"]) == formula_signature(
            formula["formula_term"], formula["formula_gate"]
        ):
            matching.append(requirement_set)
        else:
            differing.append(name)

    by_university: dict[str, int] = defaultdict(int)
    for requirement_set in matching:
        by_university[requirement_set["programme"]["university"]["slug"]] += 1
    label = (
        "все программы вуза"
        if batch.get("whole_university")
        else "без подтверждённой формулы" if batch.get("without_formula") else "совпадают с подтверждённой формулой"
    )
    print(f"{label}: {len(matching)} {dict(by_university)}")
    for name in differing:
        print(f"  НЕ совпадает (не подтверждается): {name}")
    if len(matching) != batch["expected"]:
        raise SystemExit(f"ожидалось {batch['expected']} — черновики изменились после решения владельца; ничего не подтверждено")
    if not apply:
        print("отчёт — ничего не подтверждено; подтвердит --apply")
        return
    now = datetime.now(timezone.utc).isoformat()
    ids = [requirement_set["id"] for requirement_set in matching]
    for start in range(0, len(ids), 200):
        execute(
            client.table("programme_requirement_set")
            .update({"verified_at": now, "verified_by": batch["verified_by"]})
            .in_("id", ids[start : start + 200])
        )
    print(f"подтверждено: {len(ids)}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
    elif "--batch" not in args or args[args.index("--batch") + 1] not in BATCHES:
        raise SystemExit(f"укажите партию: --batch {' | '.join(BATCHES)}")
    else:
        main(args[args.index("--batch") + 1], "--apply" in args)
