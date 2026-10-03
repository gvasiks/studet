"""Степень и описание программ ЛУ — с английских страниц программ на lu.lv.

Порция 2 работы «диплом и описание для остальных программ» (2026-10-03).
У программ ЛУ в каталоге только английские названия, поэтому найти их в
NIID по названию нельзя (см. match_niid_by_name.py). Зато на странице
программы на lu.lv есть и степень, и описание:

  Obtainable degree or qualification: Bachelor of Humanities in …
  <текст после блока фактов>

  степень  -> programme.degree_awarded_en
  описание -> programme.description_en (начало, как у NIID)

Отдельный скрипт, а не часть сборщика sources/lu.py: еженедельный сбор
пишет в базу всё сразу, и ошибка в разборе описания не должна ломать сбор
цен и мест. Страницы открываются те же, что и у сборщика (их адрес уже
лежит в programme.source_url), с той же вежливой паузой.

  python src/enrich_lu_details.py              # показать, что будет записано
  python src/enrich_lu_details.py --apply      # записать
  python src/enrich_lu_details.py --limit 10   # только первые 10 страниц
  python src/enrich_lu_details.py --all        # перечитать и уже заполненные
  python src/enrich_lu_details.py --selftest   # самотест без сети и базы

Срок аккредитации здесь не берётся: его пишет сам сборщик lu.py, и на
страницах ЛУ он есть лишь у нескольких программ.

Правило 6 CLAUDE.md эти поля не затрагивает; verified_at не трогается.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from enrich_niid_details import clean_line, excerpt, is_due
from sources.lu import SINGLE_LINE_FIELDS, _field_for

SOURCE_KEY = "sources.lu"

# Степень длиннее этого — почти наверняка в значение попал текст описания
# (на части страниц описание идёт сразу за полем, без пустой строки).
MAX_DEGREE_LENGTH = 200

# Описание короче этого — не описание, а обрывок страницы: подпись ссылки
# («Broschure (PDF)»), одиночная строка сноски.
MIN_DESCRIPTION_LENGTH = 80


def description_from(text: str) -> str | None:
    """Текст страницы программы без блока фактов.

    Тот же обход строк, что в lu._parse_facts, но собирается обратное:
    всё, что НЕ относится к полям «метка: значение».
    - строки до первого поля (повтор названия программы) отбрасываются;
    - у однострочных полей (язык, город…) значением считается только первая
      строка — остальные до пустой строки и есть начало описания;
    - у многострочных полей (места, плата, степень) продолжение значения от
      описания отличить нельзя, оно остаётся значением.
    """
    paragraphs: list[str] = []
    current: str | None = None
    value_lines = 0
    seen_field = False
    for line in text.split("\n"):
        stripped = line.strip().replace("\xa0", " ").strip()
        key, colon, rest = stripped.partition(":")
        field = _field_for(key) if colon else None
        if field:
            current = field
            value_lines = 1 if rest.strip() else 0
            seen_field = True
        elif not stripped:
            # как в lu._parse_facts: поле заканчивается пустой строкой только
            # ПОСЛЕ значения. «Метка:» + пустая строка + значение — это всё
            # ещё значение (иначе степень попадала в описание).
            if current is None or value_lines > 0:
                current = None
            if paragraphs and paragraphs[-1] != "":
                paragraphs.append("")  # граница абзаца
        elif current:
            if current in SINGLE_LINE_FIELDS and value_lines >= 1:
                paragraphs.append(stripped)
            else:
                value_lines += 1
        elif seen_field:
            paragraphs.append(stripped)

    # строки одного абзаца — через пробел, абзацы — через пустую строку
    blocks: list[str] = []
    buffer: list[str] = []
    for item in paragraphs + [""]:
        if item:
            buffer.append(item)
        elif buffer:
            blocks.append(" ".join(buffer))
            buffer = []
    description = "\n\n".join(blocks)
    return description if len(description) >= MIN_DESCRIPTION_LENGTH else None


def degree_from(text: str) -> str | None:
    """Значение поля «Obtainable degree…». Тот же обход, что в
    lu._parse_facts, но строки значения соединяются через «; », а не
    пробелом: у программ с подпрограммами степеней несколько, по одной на
    строке («Biology - Bachelor of …» / «Biomedicine - Bachelor of …»)."""
    lines: list[str] = []
    current: str | None = None
    for line in text.split("\n"):
        stripped = line.strip().replace("\xa0", " ").strip()
        key, colon, rest = stripped.partition(":")
        field = _field_for(key) if colon else None
        if field:
            current = field
            if field == "degree" and rest.strip():
                lines.append(rest.strip())
        elif not stripped:
            if current == "degree" and lines:
                break  # значение закончилось
            if current != "degree":
                current = None
        elif current == "degree":
            lines.append(stripped)
    degree = clean_line("; ".join(lines))
    if degree and len(degree) > MAX_DEGREE_LENGTH:
        return None
    return degree


def details_from_text(text: str) -> dict[str, str | None]:
    degree = degree_from(text)
    return {
        "degree_awarded_en": degree,
        "description_en": excerpt(description_from(text)),
    }


def main(apply: bool, everything: bool, limit: int | None) -> None:
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright

    import polite
    from db import get_service_client

    load_dotenv()
    polite.install()
    client = get_service_client()
    now = datetime.now(timezone.utc)

    try:
        rows = (
            client.table("programme")
            .select("id, slug, source_url, degree_awarded_en, details_extracted_at")
            .eq("source_key", SOURCE_KEY)
            .execute()
            .data
        )
    except Exception as exc:  # noqa: BLE001
        print(
            "Не удалось прочитать programme.degree_awarded_en — проверьте, применена ли миграция "
            f"supabase/migrations/20261003180000_programme_degree_en.sql. ({type(exc).__name__}: {exc})"
        )
        if apply:
            sys.exit(1)
        # сухой прогон полезен и до миграции: показывает, что будет записано
        rows = [
            {**row, "details_extracted_at": None}
            for row in client.table("programme").select("id, slug, source_url").eq("source_key", SOURCE_KEY).execute().data
        ]

    due = sorted(
        (row for row in rows if row["source_url"] and (everything or is_due(row["details_extracted_at"], now))),
        key=lambda row: row["slug"],
    )
    if limit:
        due = due[:limit]
    print(
        f"программ ЛУ: {len(rows)}; страниц к обходу: {len(due)}"
        + ("" if apply else " (сухой прогон — запись только с --apply)")
    )

    written = 0
    empty = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for row in due:
            try:
                page.goto(row["source_url"], wait_until="domcontentloaded")
                blocks = page.locator(".ce-bodytext")
                text = "\n".join(blocks.nth(i).inner_text() for i in range(blocks.count()))
            except Exception as exc:  # noqa: BLE001
                print(f"ОШИБКА {row['slug']}: {type(exc).__name__}: {exc}")
                continue

            details = details_from_text(text)
            if not any(details.values()):
                empty += 1
                print(f"ПУСТО {row['slug']}")
                continue

            description = details["description_en"] or ""
            print(
                f"{row['slug']}: degree={details['degree_awarded_en']!r}; "
                f"description={len(description)} chars: {description[:90]!r}"
            )
            if apply:
                # None пишется явно (в отличие от enrich_niid_details.py): эти
                # две колонки у программ ЛУ заполняет только этот скрипт, и
                # после исправления разбора прежнее значение должно исчезнуть.
                update: dict[str, object] = dict(details)
                update["details_source_url"] = row["source_url"]
                update["details_extracted_at"] = now.isoformat()
                client.table("programme").update(update).eq("id", row["id"]).execute()
                written += 1
        browser.close()

    print(polite.report_and_reset())
    print(f"записано программ: {written}; пустых страниц: {empty}")


def selftest() -> None:
    page_text = "\n".join(
        [
            "English, European Languages and Business Studies (EN)",
            'Bachelor\'s study programme "English, European Languages and Business Studies"',
            "",
            "Programme level: Bachelor's Degree Programme",
            "Language of instruction: English",
            "Study form and duration: full-time - 6 semesters, part-time - 8 semesters",
            "Credits: 180 ECTS",
            "Obtainable degree or qualification: Bachelor of Humanities in English and Language Studies",
            "Tuition fee per year: full-time studies - 2600 EUR",
            "Study location: Riga, city centre",
            "The programme consists of three sub-programmes.",
            "Students choose one before starting.",
            "",
            "English Language",
            "It is a classical study programme in English studies.",
        ]
    )
    details = details_from_text(page_text)
    assert details["degree_awarded_en"] == "Bachelor of Humanities in English and Language Studies"
    description = details["description_en"]
    assert description is not None
    assert description.startswith("The programme consists of three sub-programmes. Students choose one"), description
    assert "\n\nEnglish Language It is a classical" in description, "абзацы разделены пустой строкой"
    assert "Riga, city centre" not in description, "значение поля в описание не попадает"
    assert "Bachelor's study programme" not in description, "строки до первого поля отброшены"

    # докторантура: значение на следующей строке после метки
    doctoral = (
        "Level:\nDoctoral\n\nObtainable degree:\nDoctor of Science (Ph.D.) in Physics\n\n"
        "About\nResearch in physics, from condensed matter to astrophysics and applied optics."
    )
    details = details_from_text(doctoral)
    assert details["degree_awarded_en"] == "Doctor of Science (Ph.D.) in Physics"
    assert details["description_en"] == "About Research in physics, from condensed matter to astrophysics and applied optics."

    two = (
        "Obtainable degree or qualification: Biology - Bachelor of Natural Sciences in Biology\n"
        "Biomedicine - Bachelor of Natural Sciences in Biomedicine\n\nText."
    )
    assert degree_from(two) == "Biology - Bachelor of Natural Sciences in Biology; Biomedicine - Bachelor of Natural Sciences in Biomedicine"

    # описание, прилипшее к степени без пустой строки, — не степень
    glued = "Obtainable degree: " + "x" * 250
    assert details_from_text(glued)["degree_awarded_en"] is None

    assert description_from("Just a title\nAnother line") is None, "без полей описания нет"

    # «Метка:» + пустая строка + значение: значение не должно стать описанием
    spaced = (
        "Obtainable degree or qualification:\n\nfor the sub-programme A qualification: Teacher\n"
        "for the sub-programme B qualification: Speech Therapist\n\n" + "Real description sentence. " * 5
    )
    spaced_details = details_from_text(spaced)
    assert spaced_details["degree_awarded_en"] == (
        "for the sub-programme A qualification: Teacher; for the sub-programme B qualification: Speech Therapist"
    ), spaced_details["degree_awarded_en"]
    assert spaced_details["description_en"].startswith("Real description sentence."), spaced_details["description_en"]

    # подпись ссылки и строка об аккредитации — не описание
    assert details_from_text("Language: English\n\nBroschure (PDF)")["description_en"] is None
    assert details_from_text("Language: English\n\nAccreditation until: 24.08.2029.")["description_en"] is None
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    args = sys.argv[1:]
    if "--selftest" in args:
        selftest()
    else:
        limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
        main(apply="--apply" in args, everything="--all" in args, limit=limit)
