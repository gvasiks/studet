from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from db import get_service_client
from sources import riseba, turiba

SOURCES = [turiba, riseba]


def main() -> None:
    load_dotenv()
    client = get_service_client()
    now = datetime.now(timezone.utc).isoformat()

    for source in SOURCES:
        university, programmes = source.scrape()

        uni_row = university.model_dump(exclude_none=True)
        uni_row["extracted_at"] = now
        result = client.table("university").upsert(uni_row, on_conflict="slug").execute()
        university_id = result.data[0]["id"]

        programme_rows = []
        for programme in programmes:
            row = programme.model_dump(exclude_none=True, mode="json")
            row["university_id"] = university_id
            row["extracted_at"] = now
            programme_rows.append(row)

        if programme_rows:
            client.table("programme").upsert(
                programme_rows, on_conflict="university_id,slug"
            ).execute()

        print(f"{source.__name__}: upserted 1 university, {len(programme_rows)} programmes")


if __name__ == "__main__":
    main()
