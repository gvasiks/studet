"""Запись разобранных формул в базу — общая часть для всех разборщиков
документов (formulas_lu.py, formulas_rsu.py, ...).

Правило проекта (5 и 6): формула кладётся ЧЕРНОВИКОМ, verified_at не
трогаем — подтверждает только человек. Что уже подтверждено, то не
перезаписывается: иначе повторный запуск молча подменил бы числа,
которые человек сверял с документом.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class ParsedTerm:
    kind: str
    subject: str | None
    coefficient: float
    optional: bool = False


@dataclass
class Draft:
    """Одна формула к записи: блок документа, программы каталога и слагаемые."""

    block: str
    slugs: list[str]
    terms: list[ParsedTerm]
    excerpt: str  # дословный текст блока документа


@dataclass
class DocumentMeta:
    university_slug: str
    source_url: str
    source_doc: str
    valid_from: date
    # protocol — результат seed_formulas.source_protocol(...)
    protocol: dict


def write_drafts(meta: DocumentMeta, drafts: list[Draft], apply: bool, supersede_older: bool = True) -> None:
    if not apply:
        print(f"\nсухой прогон: было бы записано {len(drafts)} блоков; для записи запустите с --apply")
        return

    from dotenv import load_dotenv

    from db import get_service_client

    load_dotenv()
    client = get_service_client()
    university_id = (
        client.table("university").select("id").eq("slug", meta.university_slug).single().execute().data["id"]
    )

    written = 0
    for draft in drafts:
        for slug in draft.slugs:
            found = (
                client.table("programme").select("id").eq("university_id", university_id).eq("slug", slug).execute().data
            )
            if not found:
                print(f"  [{draft.block}] программы {slug} нет в каталоге — пропуск")
                continue
            programme_id = found[0]["id"]

            existing = (
                client.table("formula")
                .select("id, verified_at")
                .eq("programme_id", programme_id)
                .eq("variant", "ce")
                .eq("valid_from", meta.valid_from.isoformat())
                .execute()
                .data
            )
            if existing and existing[0]["verified_at"]:
                print(f"  [{draft.block}] {slug}: формула уже подтверждена — не трогаю")
                continue

            row = {
                "programme_id": programme_id,
                "variant": "ce",
                "valid_from": meta.valid_from.isoformat(),
                "source_url": meta.source_url,
                "source_doc": meta.source_doc,
                "source_excerpt": draft.excerpt,
                **meta.protocol,
            }
            formula_id = (
                client.table("formula").upsert(row, on_conflict="programme_id,variant,valid_from").execute().data[0]["id"]
            )
            client.table("formula_term").delete().eq("formula_id", formula_id).execute()
            client.table("formula_term").insert(
                [
                    {
                        "formula_id": formula_id,
                        "kind": t.kind,
                        "subject": t.subject,
                        "coefficient": t.coefficient,
                        "optional": t.optional,
                    }
                    for t in draft.terms
                ]
            ).execute()
            written += 1
    print(f"записано формул-черновиков: {written}")

    if not supersede_older:
        return
    # Формулы прошлого учебного года этого вуза больше не действуют: документ
    # заменён. Закрываем их всем (в том числе программам, для которых новую
    # формулу разобрать не удалось): нет формулы честнее, чем формула прошлого года.
    old = (
        client.table("formula")
        .select("id, programme!inner(university_id)")
        .eq("programme.university_id", university_id)
        .eq("variant", "ce")
        .is_("valid_to", "null")
        .lt("valid_from", meta.valid_from.isoformat())
        .execute()
        .data
    )
    for row in old:
        client.table("formula").update({"valid_to": (meta.valid_from - timedelta(days=1)).isoformat()}).eq(
            "id", row["id"]
        ).execute()
    print(f"закрыто формул прошлых лет: {len(old)}")
