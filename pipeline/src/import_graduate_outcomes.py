"""Разовый (раз в год) импорт данных о выпускниках в graduate_outcome —
ревью 2026-09, пункт 14. Не входит в SOURCES/main.py: это не обход
сайтов вузов, а загрузка одного официального CSV. Повторный запуск
безопасен — upsert по естественному ключу, лишние строки не плодятся.

  python src/import_graduate_outcomes.py
  python src/import_graduate_outcomes.py path/to/file.csv   # локальный файл
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from db import get_service_client
from graduate_outcomes import DATASET_URL, download_csv, parse_outcomes

BATCH_SIZE = 500


def main(csv_path: str | None) -> None:
    text = Path(csv_path).read_text(encoding="utf-8-sig") if csv_path else download_csv()
    rows = parse_outcomes(text)

    client = get_service_client()
    universities = client.table("university").select("id, slug").execute().data
    id_by_slug = {row["slug"]: row["id"] for row in universities}

    payload = []
    for row in rows:
        university_id = id_by_slug.get(row.university_slug)
        if university_id is None:
            raise SystemExit(f"В базе нет университета {row.university_slug!r} — сначала прогнать main.py")
        payload.append(
            {
                "university_id": university_id,
                "graduation_year": row.graduation_year,
                "tax_year": row.tax_year,
                "level_code": row.level_code,
                "programme_group": row.programme_group,
                "graduates": row.graduates,
                "employed": row.employed,
                "unemployed_or_inactive": row.unemployed_or_inactive,
                "emigrated": row.emigrated,
                "no_info": row.no_info,
                "avg_income_eur": row.avg_income_eur,
                "median_income_eur": row.median_income_eur,
                "source_url": DATASET_URL,
            }
        )

    for start in range(0, len(payload), BATCH_SIZE):
        client.table("graduate_outcome").upsert(
            payload[start : start + BATCH_SIZE],
            on_conflict="university_id,graduation_year,tax_year,level_code,programme_group",
        ).execute()

    print(f"graduate_outcome: upserted {len(payload)} rows for {len({r.university_slug for r in rows})} universities")


if __name__ == "__main__":
    load_dotenv()
    main(sys.argv[1] if len(sys.argv) > 1 else None)
