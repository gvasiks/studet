"""Разовая простановка disputed_at/disputed_reason (план 2026-09-21, неделя 3,
пункт 03) — как seed_formulas.py: не входит в SOURCES, не часть конвейера,
запускается вручную. verified_at не трогает никогда (см. миграцию
20260922100000_disputed_facts.sql: запись не может быть одновременно
подтверждённой и спорной).

Единственная известная на 2026-09-22 запись с реальной формулой в базе, но
неоднозначным чтением документа — Ventspils "Elektronikas inženierija":
физика в формуле — необязательное слагаемое сверху уже полной суммы 100,
поэтому максимум получается 110 при заявленной документом "шкале 100"
(п. 1. pielikums: "konkursa rezultātus... izsaka 100 punktu vai procentu
skalā"). Это не ошибка разбора — коэффициенты взяты дословно из таблицы
PDF, — а честно неясное место в самом документе: вопрос уже отправлен VeA
(docs/checks/ADMISSION-COMMITTEE-QUESTIONS.md).

Не путать со спорным: LU "Biznesa procesu vadība" и "Finanses" (заочная
формула из того же блока документа отличается от очной, но в каталоге
у этих программ только очная запись study_mode=full_time — это пробел
охвата каталога, не спор о формуле; формула в базе верна для того, что
есть в каталоге). Их сюда специально не включаю — см. коммит.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

from db import get_service_client

# (university_slug, programme_slug, variant) -> причина
DISPUTED: dict[tuple[str, str, str], str] = {
    ("venta", "elektronika-bakalaurs", "ce"): (
        "Формула в 1. pielikums: CE l.k.*P1*0,6 + CE l.k.*P2*0,2 + CE l.k.*P3*0,1 + "
        "0,1*vidējā vērtība = 100 без физики; сверху необязательное 'P4 – CE fizikā "
        "(ja ir kārtots)' с коэффициентом 0,1 — итог до 110 при заявленной документом "
        "\"100 punktu vai procentu skalā\" (1. pielikums, ievaddaļa). Неясно, действительно "
        "ли физика прибавляется сверху без потолка, или должна заменять одно из "
        "остальных слагаемых. Вопрос отправлен VeA (studijas@venta.lv), "
        "docs/checks/ADMISSION-COMMITTEE-QUESTIONS.md."
    ),
}


def main() -> None:
    load_dotenv()
    client = get_service_client()

    for (university_slug, programme_slug, variant), reason in DISPUTED.items():
        university = client.table("university").select("id").eq("slug", university_slug).single().execute().data
        programme = (
            client.table("programme")
            .select("id")
            .eq("university_id", university["id"])
            .eq("slug", programme_slug)
            .single()
            .execute()
            .data
        )
        formula = (
            client.table("formula")
            .select("id, verified_at, disputed_at")
            .eq("programme_id", programme["id"])
            .eq("variant", variant)
            .is_("valid_to", "null")
            .single()
            .execute()
            .data
        )
        if formula["verified_at"]:
            print(f"{university_slug}/{programme_slug}: уже подтверждена человеком — не трогаю")
            continue
        if formula["disputed_at"]:
            print(f"{university_slug}/{programme_slug}: уже помечена спорной, пропуск")
            continue

        now = datetime.now(timezone.utc).isoformat()
        client.table("formula").update({"disputed_at": now, "disputed_reason": reason}).eq(
            "id", formula["id"]
        ).execute()
        print(f"{university_slug}/{programme_slug}: помечена спорной")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    main()
