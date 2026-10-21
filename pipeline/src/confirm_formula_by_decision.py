"""Подтверждение конкретной формулы по решению владельца, данному в чате.

Формула — поле правила 6 CLAUDE.md: подтверждает только человек. Этот
скрипт не принимает решения, а исполняет записанное ниже решение владельца
и только если формула в базе — ровно та, что была ему показана (те же
слагаемые и коэффициенты). Иначе ничего не меняет.

  python src/confirm_formula_by_decision.py            # только проверка
  python src/confirm_formula_by_decision.py --apply    # подтвердить
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

# (вуз, программа, слагаемые как их видел владелец, подпись)
DECISIONS = [
    (
        "venta",
        "datorzinatnes-bakalaurs-en",
        # строка документа «Datorzinātnes (ENG un LV)»: та же формула, что у
        # латышского потока
        {("ce", "mathematics", 0.6, False), ("ce", "english", 0.2, False), ("ce", "latvian", 0.1, False), ("ce_average", None, 0.1, False)},
        "Gvasiks (решение владельца 2026-10-21 в чате: «Подтверждаю» формулу Datorzinātnes (en) — строка «Datorzinātnes "
        "(ENG un LV)» приложения 1 правил приёма VeA 2026/27; docs/checks/REQUIREMENTS-REVIEW.md, «Ventspils»)",
    ),
]


def main(apply: bool) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()
    for university, slug, expected, verified_by in DECISIONS:
        university_id = execute(client.table("university").select("id").eq("slug", university)).data[0]["id"]
        programme_id = execute(
            client.table("programme").select("id").eq("university_id", university_id).eq("slug", slug)
        ).data[0]["id"]
        formulas = execute(
            client.table("formula")
            .select("id, verified_at, formula_term(kind, subject, coefficient, optional)")
            .eq("programme_id", programme_id)
            .eq("variant", "ce")
            .is_("valid_to", "null")
        ).data
        if len(formulas) != 1:
            print(f"{university} {slug}: действующих формул {len(formulas)}, ожидалась одна — пропуск")
            continue
        formula = formulas[0]
        terms = {(t["kind"], t["subject"], float(t["coefficient"]), bool(t["optional"])) for t in formula["formula_term"]}
        if formula["verified_at"]:
            print(f"{university} {slug}: уже подтверждена")
            continue
        if terms != expected:
            print(f"{university} {slug}: слагаемые не те, что видел владелец — не подтверждаю: {sorted(terms, key=str)}")
            continue
        print(f"{university} {slug}: слагаемые совпадают с показанными владельцу")
        if apply:
            now = datetime.now(timezone.utc).isoformat()
            execute(client.table("formula").update({"verified_at": now, "verified_by": verified_by}).eq("id", formula["id"]))
            print("  подтверждена")
    if not apply:
        print("проверка — ничего не подтверждено; подтвердит --apply")


if __name__ == "__main__":
    main("--apply" in sys.argv[1:])
