"""Пакетное подтверждение направлений программ ПО ПРАВИЛУ, не по строке
(план 2026-09-21, неделя 3, пункт 01). Читайте сначала
docs/checks/PROGRAMME-FIELD-REVIEW.md — этот скрипт исполняет то решение,
которое там описано, а не принимает его.

  python src/confirm_programme_fields_by_rule.py            # только отчёт
  python src/confirm_programme_fields_by_rule.py --apply    # подтвердить

Подтверждает РАЗОМ все строки programme_field, которые сегодня дала бы
programme_fields.py (тот же код, что и seed_programme_fields.py; если
после ревью правила не менялись, набор совпадает с уже записанным в базу
"name-rules"). Правило 6 CLAUDE.md сюда не относится: направление
программы не входит в перечень его полей (формула, дедлайн, стоимость,
бюджетные места, язык, через кого подача) — ошибка здесь означает не тот
фильтр интересов, а не поданные не туда документы. Поэтому подтверждение
разовое и по правилу, а не построчно человеком в Studio.

EXCLUDE ниже — программы, которые при чтении PROGRAMME-FIELD-REVIEW.md
владелец счёл неверными или спорными: они остаются неподтверждёнными
(обычная очередь по одной) и в это подтверждение не попадают, даже если
правило для них сработало.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

from db import get_service_client
from graduate_outcomes import download_csv, parse_outcomes
from programme_fields import candidates_for, choose_field, groups_with_data

# (university_slug, programme_slug) — заполняется по итогам ревью выборки
# в docs/checks/PROGRAMME-FIELD-REVIEW.md, ДО первого запуска с --apply.
EXCLUDE: set[tuple[str, str]] = set()

VERIFIED_BY = "Gvasiks (подтверждение по правилу после ревью выборки, docs/checks/PROGRAMME-FIELD-REVIEW.md)"


def main(apply: bool) -> None:
    load_dotenv()
    client = get_service_client()
    data = groups_with_data(parse_outcomes(download_csv()))

    programmes = (
        client.table("programme")
        .select("id, slug, name_en, name_lv, degree_level, university:university_id(slug)")
        .execute()
        .data
    )
    already = {
        row["programme_id"]
        for row in client.table("programme_field").select("programme_id").not_.is_("verified_at", "null").execute().data
    }

    to_confirm: list[str] = []  # programme_id
    skipped_excluded = 0
    unmatched = 0
    for programme in programmes:
        if programme["id"] in already:
            continue
        key = (programme["university"]["slug"], programme["slug"])
        candidates = candidates_for(programme["name_en"], programme["name_lv"])
        if not candidates:
            unmatched += 1
            continue
        if key in EXCLUDE:
            skipped_excluded += 1
            continue
        to_confirm.append(programme["id"])

    print(
        f"к подтверждению по правилу: {len(to_confirm)}; "
        f"исключено (EXCLUDE): {skipped_excluded}; без правила (не трогаем): {unmatched}"
    )

    if not apply:
        print("(сухой прогон — запустите с --apply, когда выборка проверена)")
        return

    now = datetime.now(timezone.utc).isoformat()
    # programme_field.programme_id — первичный ключ, upsert по одному не нужен:
    # эти строки уже существуют (записаны seed_programme_fields.py), просто
    # обновляем поля подтверждения пакетами по 200, чтобы не упереться в
    # лимит одного запроса
    batch = 200
    for start in range(0, len(to_confirm), batch):
        ids = to_confirm[start : start + batch]
        client.table("programme_field").update(
            {"verified_at": now, "verified_by": VERIFIED_BY, "verification_method": "rule"}
        ).in_("programme_id", ids).execute()
    print(f"подтверждено: {len(to_confirm)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    main("--apply" in sys.argv)
