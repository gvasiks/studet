"""Разметка программ каталога по направлениям (ревью 2026-09, пункты 14
и 16) — правила в programme_fields.py.

  python src/seed_programme_fields.py            # только отчёт, ничего не пишет
  python src/seed_programme_fields.py --list     # ещё и полный список назначений
  python src/seed_programme_fields.py --apply    # записать в programme_field

verified_at скрипт не трогает и не пишет (правило 6 CLAUDE.md), а уже
подтверждённые человеком строки пропускает целиком — смена правил не
должна тихо менять код у программы, которую человек уже проверил.

Как подтвердить (Supabase Studio -> SQL editor), просмотрев отчёт:

  update programme_field
  set verified_at = now(), verified_by = '<кто>'
  where verified_at is null
    and programme_id in (select id from programme where university_id =
        (select id from university where slug = 'lu'));

Проверять удобнее по вузу, а не 339 строк сразу — сначала те, где в
отчёте "нет данных" (там правило могло промахнуться).
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from db import get_service_client
from graduate_outcomes import download_csv, parse_outcomes
from programme_fields import candidates_for, choose_field, groups_with_data


def main(apply: bool, list_all: bool) -> None:
    client = get_service_client()
    data = groups_with_data(parse_outcomes(download_csv()))

    programmes = (
        client.table("programme")
        .select("id, slug, name_en, name_lv, degree_level, university:university_id(slug)")
        .execute()
        .data
    )
    verified = {
        row["programme_id"]
        for row in client.table("programme_field").select("programme_id").not_.is_("verified_at", "null").execute().data
    }

    to_write = []
    listing = []
    unmatched = []
    no_data = []
    for programme in programmes:
        if programme["id"] in verified:
            continue
        candidates = candidates_for(programme["name_en"], programme["name_lv"])
        label = f"{programme['university']['slug']}/{programme['slug']} ({programme['degree_level']})"
        if not candidates:
            unmatched.append(label)
            continue
        code, confirmed = choose_field(programme["university"]["slug"], programme["degree_level"], candidates, data)
        if not confirmed:
            no_data.append(f"{label} -> {code} (candidates {','.join(candidates)})")
        name = programme["name_en"] or programme["name_lv"]
        listing.append(f"{label} | {name} -> {code}{'' if confirmed else ' (no data)'}")
        to_write.append({"programme_id": programme["id"], "field_code": code, "source": "name-rules"})

    print(f"programmes: {len(programmes)}, already verified (skipped): {len(verified)}")
    print(f"classified: {len(to_write)}, no rule matched: {len(unmatched)}, code has no data for that uni/level: {len(no_data)}")
    print("\nNO RULE MATCHED:")
    for item in unmatched:
        print("  " + item)
    print("\nNO DATA FOR CODE (rule may have missed, or the cell is suppressed as too small):")
    for item in no_data:
        print("  " + item)

    if list_all:
        print("\nALL CLASSIFIED:")
        for item in sorted(listing):
            print("  " + item)

    if apply and to_write:
        client.table("programme_field").upsert(to_write, on_conflict="programme_id").execute()
        print(f"\nwritten: {len(to_write)} rows")
    elif not apply:
        print("\n(dry run — pass --apply to write)")


if __name__ == "__main__":
    load_dotenv()
    main("--apply" in sys.argv, "--list" in sys.argv)
