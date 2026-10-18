"""Подтверждение связей «программа ↔ код приёма statistika.vupp.lv» ПО
ПРАВИЛУ, не по строке. Читайте сначала docs/checks/VUPP-LINKS-REVIEW.md —
этот скрипт исполняет описанное там решение владельца, а не принимает его.

  python src/confirm_vupp_links_by_rule.py --batch name            # только отчёт
  python src/confirm_vupp_links_by_rule.py --batch name --apply    # подтвердить

Партия — решение владельца о черновиках одного способа (BATCHES ниже):
code — по коду приёма (vupp_link_drafts.py: code_from_page — ЛУ,
code_from_slug — РТУ), name — по латышскому названию (vupp_link_by_name.py),
manual — по ручной таблице (vupp_link_manual.py).
Подтверждаются все неподтверждённые черновики партии.

Связь не входит в перечень полей правила 6 (формула, дедлайн, стоимость,
бюджетные места, язык, через кого подача): ошибка здесь — не те
прошлогодние цифры рядом с программой, а не поданные не туда документы.
Поэтому подтверждение разовое и по правилу, после просмотра списка.

Новые черновики (следующий год, ручная таблица соответствий) этими
решениями не покрыты: спросите владельца и добавьте в BATCHES новую
партию с датой его решения.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

# expected — сколько черновиков было в просмотренном владельцем списке.
# Другое число значит, что черновики менялись после решения, и оно их не
# покрывает: скрипт ничего не подтверждает.
BATCHES = {
    # Решение владельца 2026-10-18: «Подтвердить все 127» — ЛУ 35, РТУ 92.
    "code": {
        "methods": ["code_from_page", "code_from_slug"],
        "expected": 127,
        "verified_by": (
            "Gvasiks (подтверждение по правилу, решение владельца 2026-10-18 для 127 связей ЛУ и РТУ по коду приёма; "
            "правила и список — docs/checks/VUPP-LINKS-REVIEW.md)"
        ),
    },
    # Решение владельца 2026-10-18: «Подтвердить все 42» — Ventspils 9, ViA 7,
    # LBTU 20, DU 6 (раздел «Вторая партия»).
    "name": {
        "methods": ["name"],
        "expected": 42,
        "verified_by": (
            "Gvasiks (подтверждение по правилу, решение владельца 2026-10-18 для 42 связей Ventspils, ViA, LBTU и DU "
            "по латышскому названию; правила и список — docs/checks/VUPP-LINKS-REVIEW.md, «Вторая партия»)"
        ),
    },
    # Решение владельца 2026-10-18: «Все 60 программ» — 178 кодов ручной
    # таблицы (ЛУ 31, DU 14, EKA 10, RNU 5), включая два помеченных
    # «проверить» (раздел «Третья партия»).
    "manual": {
        "methods": ["manual"],
        "expected": 178,
        "verified_by": (
            "Gvasiks (подтверждение по правилу, решение владельца 2026-10-18 для 178 связей 60 программ ЛУ, DU, EKA и RNU "
            "по ручной таблице соответствий vupp_link_manual.py; список — docs/checks/VUPP-LINKS-REVIEW.md, «Третья партия»)"
        ),
    },
}


def main(batch_name: str, apply: bool) -> None:
    batch = BATCHES[batch_name]
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    from db import fetch_all, get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()
    drafts = fetch_all(
        lambda: client.table("programme_vupp_link")
        .select("id, university_slug, programme_code, method")
        .is_("verified_at", "null")
        .in_("method", batch["methods"])
        .order("id")
    )
    by_university: dict[str, int] = {}
    for draft in drafts:
        by_university[draft["university_slug"]] = by_university.get(draft["university_slug"], 0) + 1
    print(f"неподтверждённых черновиков партии {batch_name}: {len(drafts)} {by_university}")
    if len(drafts) != batch["expected"]:
        # решение принято про конкретный список; другое число — значит,
        # черновики менялись после просмотра, и решение их не покрывает
        raise SystemExit(f"ожидалось {batch['expected']} — черновики изменились после решения владельца; ничего не подтверждено")
    if not apply:
        print("отчёт — ничего не подтверждено; подтвердит --apply")
        return
    now = datetime.now(timezone.utc).isoformat()
    ids = [draft["id"] for draft in drafts]
    for start in range(0, len(ids), 200):
        execute(
            client.table("programme_vupp_link")
            .update({"verified_at": now, "verified_by": batch["verified_by"]})
            .in_("id", ids[start : start + 200])
        )
    print(f"подтверждено: {len(ids)}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--batch" not in args or args[args.index("--batch") + 1] not in BATCHES:
        raise SystemExit(f"укажите партию: --batch {' | '.join(BATCHES)}")
    main(args[args.index("--batch") + 1], "--apply" in args)
