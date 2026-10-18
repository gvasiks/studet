"""Подтверждение связей «программа ↔ код приёма statistika.vupp.lv» ПО
ПРАВИЛУ, не по строке. Читайте сначала docs/checks/VUPP-LINKS-REVIEW.md —
этот скрипт исполняет описанное там решение владельца, а не принимает его.

  python src/confirm_vupp_links_by_rule.py            # только отчёт
  python src/confirm_vupp_links_by_rule.py --apply    # подтвердить

Подтверждает все неподтверждённые черновики programme_vupp_link, которые
записал vupp_link_drafts.py по коду (code_from_page — ЛУ, code_from_slug —
РТУ). Связь не входит в перечень полей правила 6 (формула, дедлайн,
стоимость, бюджетные места, язык, через кого подача): ошибка здесь — не те
прошлогодние цифры рядом с программой, а не поданные не туда документы.
Поэтому подтверждение разовое и по правилу, после просмотра списка.

Новые черновики (следующий год, сопоставление по названию) этим решением
не покрыты: перед следующим запуском с --apply спросите владельца и
допишите дату в VERIFIED_BY.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

METHODS = ["code_from_page", "code_from_slug"]

# Решение владельца 2026-10-18: «Подтвердить все 127» — ЛУ 35, РТУ 92,
# список — docs/checks/VUPP-LINKS-REVIEW.md.
VERIFIED_BY = (
    "Gvasiks (подтверждение по правилу, решение владельца 2026-10-18 для 127 связей ЛУ и РТУ по коду приёма; "
    "правила и список — docs/checks/VUPP-LINKS-REVIEW.md)"
)
EXPECTED = 127


def main(apply: bool) -> None:
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
        .in_("method", METHODS)
        .order("id")
    )
    by_university: dict[str, int] = {}
    for draft in drafts:
        by_university[draft["university_slug"]] = by_university.get(draft["university_slug"], 0) + 1
    print(f"неподтверждённых черновиков по коду: {len(drafts)} {by_university}")
    if len(drafts) != EXPECTED:
        # решение принято про 127 конкретных связей; другое число — значит,
        # черновики менялись после просмотра, и решение их не покрывает
        raise SystemExit(f"ожидалось {EXPECTED} — черновики изменились после решения владельца; ничего не подтверждено")
    if not apply:
        print("отчёт — ничего не подтверждено; подтвердит --apply")
        return
    now = datetime.now(timezone.utc).isoformat()
    ids = [draft["id"] for draft in drafts]
    for start in range(0, len(ids), 200):
        execute(
            client.table("programme_vupp_link")
            .update({"verified_at": now, "verified_by": VERIFIED_BY})
            .in_("id", ids[start : start + 200])
        )
    print(f"подтверждено: {len(ids)}")


if __name__ == "__main__":
    main("--apply" in sys.argv[1:])
