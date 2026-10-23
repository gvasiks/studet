"""Подтверждение типов отбора (university_admission_type) по решению
владельца. Скрипт не принимает решение, а исполняет записанное ниже: для
каждого вуза из списка в базе должен лежать черновик именно того типа, что
видел владелец, со ссылкой на источник (правило 5). Иначе вуз пропускается.

  python src/confirm_admission_types.py            # только проверка
  python src/confirm_admission_types.py --apply    # подтвердить
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

# Решение владельца 2026-10-23: «Подтверждаю требования и типы» — 12 вузов с
# типом «конкурс по баллам» по их правилам приёма (REQUIREMENTS-REVIEW.md).
# Turība (черновик «вступительные испытания») в решение не входит: тип
# записан по странице для иностранцев, ждём ответа вуза
# (ADMISSION-COMMITTEE-QUESTIONS.md).
DECISION = {
    "selection_type": "competitive_score",
    "universities": [
        "lu", "rtu", "venta", "rsu", "du", "lbtu",
        "juridiska-koledza", "psmk", "rnu", "bsa", "via", "riseba",
    ],
    "verified_by": (
        "Gvasiks (решение владельца 2026-10-23: тип отбора «конкурс по баллам» по правилам приёма 2026/27 — "
        "ссылка в source_url; docs/checks/REQUIREMENTS-REVIEW.md)"
    ),
}


def main(apply: bool) -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()
    now = datetime.now(timezone.utc).isoformat()
    confirmed = 0
    for slug in DECISION["universities"]:
        university_id = execute(client.table("university").select("id").eq("slug", slug)).data[0]["id"]
        rows = execute(
            client.table("university_admission_type")
            .select("selection_type, source_url, verified_at")
            .eq("university_id", university_id)
        ).data
        if not rows:
            print(f"{slug}: черновика нет — пропуск")
            continue
        row = rows[0]
        if row["verified_at"]:
            print(f"{slug}: уже подтверждён")
            continue
        if row["selection_type"] != DECISION["selection_type"] or not row["source_url"]:
            print(f"{slug}: в базе «{row['selection_type']}», источник {row['source_url']!r} — не то, что видел владелец; пропуск")
            continue
        print(f"{slug}: {row['selection_type']} — {row['source_url']}")
        if apply:
            execute(
                client.table("university_admission_type")
                .update({"verified_at": now, "verified_by": DECISION["verified_by"]})
                .eq("university_id", university_id)
            )
            confirmed += 1
    print(f"подтверждено: {confirmed}" if apply else "проверка — ничего не подтверждено; подтвердит --apply")


if __name__ == "__main__":
    main("--apply" in sys.argv[1:])
