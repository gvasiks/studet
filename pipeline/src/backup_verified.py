"""Снимок подтверждённых человеком фактов (план 2026-09-21, неделя 1,
пункт 06). Самое дорогое в проекте — не код (он в git), а часы владельца,
потраченные на подтверждение формул, сроков, типов отбора и направлений
через Supabase Studio. На бесплатном тарифе у Supabase нет ежедневных
резервных копий; полный дамп базы можно потерять вместе с проектом.

Этот скрипт кладёт JSON со всеми ПОДТВЕРЖДЁННЫМИ (`verified_at is not
null`) записями в docs/backups/verified-facts.json — файл КОММИТИТСЯ
в репозиторий (см. .github/workflows/backup.yml), поэтому подтверждения
живут в истории git и переживают потерю самой базы. Черновики (ещё не
подтверждённые) сюда намеренно не попадают: это не полный дамп, а
компактный список того, что стоило человеческого времени — полный дамп
делает та же ветка workflow отдельным шагом с pg_dump (SUPABASE_DB_URL),
он идёт в артефакт прогона, не в git (см. .github/workflows/backup.yml).

Ключи — не UUID (они не переживают пересоздание базы, а формулы
seed-скриптов и так снова генерируют свои id при каждом запуске), а
устойчивые слаги: university_slug + programme_slug. Так снимок можно
свериться глазами в PR-диффе, а не только машиной.

Что в снимке: формулы, сроки подачи, типы отбора, направления программ,
требования к поступающим и каналы подачи (два последних — с 2026-10-10).
Чего в снимке НЕТ: пометок verified_at у самих программ и вузов (цена,
бюджетные места) и у коэффициентов уровня — подтверждённых записей там
пока нет (проверено 2026-10-10). Когда появятся — дописать сюда и в
restore_verified.py, иначе эти подтверждения копия не сохранит.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from db import fetch_all, get_service_client

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = REPO_ROOT / "docs" / "backups" / "verified-facts.json"


def _formulas(client) -> list[dict]:  # type: ignore[no-untyped-def]
    rows = fetch_all(
        lambda: client.table("formula")
        .select(
            "id, variant, valid_from, valid_to, source_url, source_doc, source_doc_number, "
            "source_doc_date, source_copy_path, source_copy_sha256, source_copy_fetched_on, source_excerpt, "
            "verified_at, verified_by, "
            "programme!inner(slug, name_lv, university!inner(slug))"
        )
        .not_.is_("verified_at", "null")
        .order("id")
    )
    ids = [row["id"] for row in rows]
    # Слагаемых у формулы несколько, так что их больше тысячи раньше, чем
    # самих формул. Пачками по 100 формул: длинный список id не влезает в
    # адрес запроса.
    terms: list[dict] = []
    gates: list[dict] = []
    for start in range(0, len(ids), 100):
        chunk = ids[start : start + 100]
        terms += fetch_all(lambda: client.table("formula_term").select("*").in_("formula_id", chunk).order("id"))
        gates += fetch_all(lambda: client.table("formula_gate").select("*").in_("formula_id", chunk).order("id"))
    terms_by_formula: dict[str, list[dict]] = {}
    for term in terms:
        terms_by_formula.setdefault(term["formula_id"], []).append(
            {"kind": term["kind"], "subject": term["subject"], "coefficient": term["coefficient"], "optional": term["optional"]}
        )
    gates_by_formula: dict[str, list[dict]] = {}
    for gate in gates:
        gates_by_formula.setdefault(gate["formula_id"], []).append(
            {"subject": gate["subject"], "min_percent": gate["min_percent"], "note": gate["note"]}
        )

    out = []
    for row in rows:
        programme = row["programme"]
        out.append(
            {
                "university_slug": programme["university"]["slug"],
                "programme_slug": programme["slug"],
                # план 2026-09-21, пункт 06: имя на момент подтверждения — не для
                # отображения, а чтобы restore_verified.py мог заметить, что слаг
                # при повторном сборе стал указывать на ДРУГУЮ программу, а не
                # молча приписать восстановленный факт не той записи
                "programme_name": programme.get("name_lv"),
                "variant": row["variant"],
                "valid_from": row["valid_from"],
                "valid_to": row["valid_to"],
                "source_url": row["source_url"],
                "source_doc": row["source_doc"],
                "source_doc_number": row["source_doc_number"],
                "source_doc_date": row["source_doc_date"],
                "source_copy_path": row["source_copy_path"],
                "source_copy_sha256": row["source_copy_sha256"],
                "source_copy_fetched_on": row["source_copy_fetched_on"],
                "source_excerpt": row["source_excerpt"],
                "verified_at": row["verified_at"],
                "verified_by": row["verified_by"],
                "terms": sorted(terms_by_formula.get(row["id"], []), key=lambda t: (t["kind"], t["subject"] or "")),
                "gates": sorted(gates_by_formula.get(row["id"], []), key=lambda g: g["subject"]),
            }
        )
    return sorted(out, key=lambda r: (r["university_slug"], r["programme_slug"], r["variant"], r["valid_from"]))


def _application_rounds(client) -> list[dict]:  # type: ignore[no-untyped-def]
    rows = (
        client.table("application_round")
        .select(
            "degree_level, language_of_instruction, label, opens_on, closes_on, note, "
            "source_url, verified_at, verified_by, university!inner(slug)"
        )
        .not_.is_("verified_at", "null")
        .execute()
        .data
    )
    out = [
        {
            "university_slug": row["university"]["slug"],
            "degree_level": row["degree_level"],
            "language_of_instruction": row["language_of_instruction"],
            "label": row["label"],
            "opens_on": row["opens_on"],
            "closes_on": row["closes_on"],
            "note": row["note"],
            "source_url": row["source_url"],
            "verified_at": row["verified_at"],
            "verified_by": row["verified_by"],
        }
        for row in rows
    ]
    return sorted(out, key=lambda r: (r["university_slug"], r["label"]))


def _admission_types(client) -> list[dict]:  # type: ignore[no-untyped-def]
    rows = (
        client.table("university_admission_type")
        .select("selection_type, source_url, verified_at, verified_by, university!inner(slug)")
        .not_.is_("verified_at", "null")
        .execute()
        .data
    )
    out = [
        {
            "university_slug": row["university"]["slug"],
            "selection_type": row["selection_type"],
            "source_url": row["source_url"],
            "verified_at": row["verified_at"],
            "verified_by": row["verified_by"],
        }
        for row in rows
    ]
    return sorted(out, key=lambda r: r["university_slug"])


def _programme_fields(client) -> list[dict]:  # type: ignore[no-untyped-def]
    # Страницами: подтверждённых направлений 892 (2026-10-10) — вплотную к
    # пределу в 1000 строк, за которым снимок молча стал бы неполным.
    rows = fetch_all(
        lambda: client.table("programme_field")
        .select(
            "field_code, source, verified_at, verified_by, verification_method, "
            "programme!inner(slug, name_lv, university!inner(slug))"
        )
        .not_.is_("verified_at", "null")
        .order("programme_id")
    )
    out = [
        {
            "university_slug": row["programme"]["university"]["slug"],
            "programme_slug": row["programme"]["slug"],
            "programme_name": row["programme"].get("name_lv"),
            "field_code": row["field_code"],
            "source": row["source"],
            "verified_at": row["verified_at"],
            "verified_by": row["verified_by"],
            # Без способа подтверждения база подтверждённую запись не примет
            # (ограничение programme_field_verified_needs_method) — без этого
            # поля восстановление падало на первой же строке.
            "verification_method": row["verification_method"],
        }
        for row in rows
    ]
    return sorted(out, key=lambda r: (r["university_slug"], r["programme_slug"]))


# Протокол источника — одни и те же колонки у формулы и у набора требований.
_PROTOCOL_COLUMNS = (
    "source_url",
    "source_doc",
    "source_doc_number",
    "source_doc_date",
    "source_copy_path",
    "source_copy_sha256",
    "source_copy_fetched_on",
    "source_excerpt",
)


def _requirement_sets(client) -> list[dict]:  # type: ignore[no-untyped-def]
    rows = fetch_all(
        lambda: client.table("programme_requirement_set")
        .select(
            "id, " + ", ".join(_PROTOCOL_COLUMNS) + ", verified_at, verified_by, "
            "programme!inner(slug, name_lv, university!inner(slug))"
        )
        .not_.is_("verified_at", "null")
        .order("id")
    )
    ids = [row["id"] for row in rows]
    requirements: dict[str, list[dict]] = {}
    for start in range(0, len(ids), 100):
        chunk = ids[start : start + 100]
        for item in fetch_all(
            lambda: client.table("programme_requirement").select("*").in_("requirement_set_id", chunk).order("id")
        ):
            requirements.setdefault(item["requirement_set_id"], []).append(
                {
                    "subject": item["subject"],
                    "min_level": item["min_level"],
                    "alternative_group": item["alternative_group"],
                    "note": item["note"],
                }
            )

    out = []
    for row in rows:
        programme = row["programme"]
        out.append(
            {
                "university_slug": programme["university"]["slug"],
                "programme_slug": programme["slug"],
                # как у формулы: по имени restore_verified.py замечает, что слаг
                # стал указывать на другую программу
                "programme_name": programme.get("name_lv"),
                **{column: row[column] for column in _PROTOCOL_COLUMNS},
                "verified_at": row["verified_at"],
                "verified_by": row["verified_by"],
                "requirements": sorted(
                    requirements.get(row["id"], []), key=lambda r: (r["alternative_group"] or "", r["subject"])
                ),
            }
        )
    return sorted(out, key=lambda r: (r["university_slug"], r["programme_slug"]))


def _application_channels(client) -> list[dict]:  # type: ignore[no-untyped-def]
    rows = fetch_all(
        lambda: client.table("application_channel")
        .select(
            "degree_level, channel_type, url, source_url, source_excerpt, verified_at, verified_by, "
            "university!inner(slug)"
        )
        .not_.is_("verified_at", "null")
        .order("id")
    )
    out = [
        {
            "university_slug": row["university"]["slug"],
            # null — запись на все уровни вуза
            "degree_level": row["degree_level"],
            "channel_type": row["channel_type"],
            "url": row["url"],
            "source_url": row["source_url"],
            "source_excerpt": row["source_excerpt"],
            "verified_at": row["verified_at"],
            "verified_by": row["verified_by"],
        }
        for row in rows
    ]
    return sorted(out, key=lambda r: (r["university_slug"], r["degree_level"] or ""))


def build_snapshot(client) -> dict:  # type: ignore[no-untyped-def]
    return {
        "formulas": _formulas(client),
        "application_rounds": _application_rounds(client),
        "admission_types": _admission_types(client),
        "programme_fields": _programme_fields(client),
        "requirement_sets": _requirement_sets(client),
        "application_channels": _application_channels(client),
    }


def main() -> None:
    load_dotenv()
    client = get_service_client()
    snapshot = build_snapshot(client)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys + отступ 2 + завершающий перевод строки: стабильный вид,
    # чтобы дифф в PR показывал только реальные изменения, не переупорядочивание
    OUT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    counts = {key: len(value) for key, value in snapshot.items()}
    print(f"записано {OUT_PATH.relative_to(REPO_ROOT)}: {counts}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    main()
