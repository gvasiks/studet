"""Диплом, квалификация и описание программы — со страницы программы в NIID.lv.

Комментарий владельца к USER-STORIES (2026-09-30): на карточке программы
нужны описание и название получаемого диплома. Решение 2026-10-01: брать
автоматически, показывать с пометкой «извлечено автоматически».

Обычный сбор (sources/niid_*.py, sources/via.py) читает только СПИСКИ
программ. Этот скрипт открывает страницу каждой программы — там есть поля,
которых в списке нет:

  Grāds                      -> programme.degree_awarded_lv
  Profesionālā kvalifikācija -> programme.qualification_lv
  Izglītības dokuments       -> programme.diploma_document_lv
  Programmas apraksts        -> programme.description_lv (начало, см. ниже)
  Licence / akreditācija     -> programme.accreditation_valid_until

Отдельный скрипт, а не часть main.py: у niid.lv в robots.txt пауза 10
секунд между страницами (polite.py её соблюдает), а сама страница грузится
долго — выходит около 20 секунд на каждую, 242 страницы — примерно 80 минут. Диплом и описание меняются редко, поэтому обход идёт раз в
месяц (.github/workflows/enrich-niid.yml), а не каждую неделю.

  python src/enrich_niid_details.py                 # показать, что будет записано
  python src/enrich_niid_details.py --apply         # записать
  python src/enrich_niid_details.py --limit 5       # только первые 5 страниц
  python src/enrich_niid_details.py --all --apply   # перечитать и уже заполненные
  python src/enrich_niid_details.py --selftest      # самотест без сети и базы

Берутся только программы, у которых источник — страница NIID
(programme.source_url). Программы с собственным сборщиком вуза (ЛУ, РТУ и
другие) этим скриптом не заполняются: надёжно сопоставить их с записями
NIID по названию нельзя.

Описание сохраняется НЕ целиком, а началом (DESCRIPTION_LIMIT знаков, до
конца предложения): это авторский текст вуза, а не факт. На карточке рядом
с ним стоит ссылка на полный текст в NIID.

Правило 6 CLAUDE.md эти поля не затрагивает — подтверждения человеком они
не требуют; verified_at не трогается.
"""

from __future__ import annotations

import re
import sys
from datetime import date, datetime, timedelta, timezone

NIID_PROGRAMME_PATH = "niid.lv/niid_search/program/"

# Сколько дней сведения считаются свежими: при обычном запуске страница
# перечитывается, только если прошло больше.
REFRESH_AFTER_DAYS = 30

# Сколько знаков описания сохраняется (см. пояснение в начале файла).
DESCRIPTION_LIMIT = 600

# Строки таблицы на странице программы: <td class="lo_label"> — подпись,
# <td class="lo_value"> — значение. Ссылки внутри значения убираются: в
# поле квалификации это «Standarts / kvalifikācijas prasības», к названию
# квалификации не относящееся.
EXTRACT_JS = r"""
() => {
  const fields = {};
  for (const row of document.querySelectorAll('tr')) {
    const label = row.querySelector('td.lo_label');
    const value = row.querySelector('td.lo_value');
    if (!label || !value) continue;
    const clone = value.cloneNode(true);
    for (const link of clone.querySelectorAll('a')) link.remove();
    fields[label.innerText.trim()] = {
      text: value.innerText.trim(),
      withoutLinks: clone.innerText.trim(),
    };
  }
  return fields;
}
"""


def clean_line(text: str | None) -> str | None:
    """Одна строка без хвостовой пунктуации и лишних пробелов; пусто -> None."""
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip().rstrip(";,").strip()
    return cleaned or None


def parse_accreditation(text: str | None) -> date | None:
    """«Studiju virziens akreditēts līdz 26.10.2029.» -> 2029-10-26."""
    if not text:
        return None
    match = re.search(r"akreditēt\w*\s+līdz\s+(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def excerpt(text: str | None, limit: int = DESCRIPTION_LIMIT) -> str | None:
    """Начало описания: не длиннее limit, по возможности до конца предложения."""
    if not text:
        return None
    # абзацы сохраняем, пробелы внутри абзаца схлопываем
    paragraphs = [re.sub(r"[ \t]+", " ", part).strip() for part in re.split(r"\n\s*\n", text)]
    cleaned = "\n\n".join(part for part in paragraphs if part)
    if not cleaned:
        return None
    if len(cleaned) <= limit:
        return cleaned
    cut = cleaned[:limit]
    # последнее окончание предложения в пределах лимита — если оно не в самом начале
    end = max(cut.rfind(". "), cut.rfind(".\n"), cut.rfind("! "), cut.rfind("? "))
    if end >= limit // 2:
        return cut[: end + 1].strip()
    return cut.rsplit(" ", 1)[0].strip() + "…"


def details_from_fields(fields: dict[str, dict[str, str]]) -> dict[str, object]:
    """Поля страницы NIID -> значения колонок programme (без служебных)."""

    def text(label: str, key: str = "text") -> str | None:
        return (fields.get(label) or {}).get(key)

    accreditation = parse_accreditation(text("Licence / akreditācija"))
    return {
        "degree_awarded_lv": clean_line(text("Grāds")),
        "qualification_lv": clean_line(text("Profesionālā kvalifikācija", "withoutLinks")),
        "diploma_document_lv": clean_line(text("Izglītības dokuments")),
        "description_lv": excerpt(text("Programmas apraksts")),
        "accreditation_valid_until": accreditation.isoformat() if accreditation else None,
    }


def is_due(extracted_at: str | None, now: datetime) -> bool:
    """Пора ли перечитать страницу."""
    if extracted_at is None:
        return True
    parsed = datetime.fromisoformat(extracted_at.replace("Z", "+00:00"))
    return now - parsed > timedelta(days=REFRESH_AFTER_DAYS)


def main(apply: bool, everything: bool, limit: int | None) -> None:
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright

    import polite
    from db import get_service_client

    load_dotenv()
    polite.install()  # честный User-Agent и пауза из robots.txt (у niid.lv — 10 с)
    client = get_service_client()
    now = datetime.now(timezone.utc)

    def _select(columns: str) -> list[dict]:
        return (
            client.table("programme")
            .select(columns)
            .like("source_url", f"%{NIID_PROGRAMME_PATH}%")
            .execute()
            .data
        )

    try:
        rows = _select("id, slug, name_lv, source_url, details_extracted_at")
    except Exception as exc:  # noqa: BLE001
        # Колонки появляются миграцией 20261003120000_programme_details.sql,
        # а миграции в этом проекте применяет владелец вручную (Studio).
        if apply:
            print(
                "В базе нет колонки details_extracted_at — миграция "
                "supabase/migrations/20261003120000_programme_details.sql ещё не применена. "
                f"Запись невозможна. ({type(exc).__name__})"
            )
            sys.exit(1)
        print("миграция ещё не применена — сухой прогон по всем страницам NIID")
        rows = [{**row, "details_extracted_at": None} for row in _select("id, slug, name_lv, source_url")]
    # Одна страница NIID может давать две программы каталога (latviešu и
    # angļu поток) — страницу открываем один раз.
    by_url: dict[str, list[dict]] = {}
    for row in rows:
        if everything or is_due(row["details_extracted_at"], now):
            by_url.setdefault(row["source_url"], []).append(row)

    urls = sorted(by_url)[:limit] if limit else sorted(by_url)
    print(
        f"программ с источником NIID: {len(rows)}; страниц к обходу: {len(urls)}"
        + ("" if apply else " (сухой прогон — запись только с --apply)")
    )

    written = 0
    empty = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for url in urls:
            try:
                page.goto(url, wait_until="domcontentloaded")
                fields = page.evaluate(EXTRACT_JS)
            except Exception as exc:  # noqa: BLE001
                print(f"ОШИБКА {url}: {type(exc).__name__}: {exc}")
                continue

            details = details_from_fields(fields)
            if not any(details.values()):
                # страница без таблицы программы (удалена из NIID?) — не пишем
                # пустоту поверх прежних значений
                empty += 1
                print(f"ПУСТО {url}")
                continue

            names = ", ".join(row["slug"] for row in by_url[url])
            print(
                f"{names}: grāds={details['degree_awarded_lv']!r}; "
                f"kvalifikācija={details['qualification_lv']!r}; "
                f"dokuments={details['diploma_document_lv']!r}; "
                f"akreditācija={details['accreditation_valid_until']}; "
                f"apraksts={len(details['description_lv'] or '')} zīmes"
            )

            if apply:
                # None не пишем: отсутствие поля на странице не должно стирать
                # значение, пришедшее из другого источника (например, срок
                # аккредитации от собственного сборщика вуза).
                update = {key: value for key, value in details.items() if value is not None}
                update["details_source_url"] = url
                update["details_extracted_at"] = now.isoformat()
                ids = [row["id"] for row in by_url[url]]
                client.table("programme").update(update).in_("id", ids).execute()
                written += len(ids)
        browser.close()

    print(polite.report_and_reset())
    print(f"записано программ: {written}; пустых страниц: {empty}")


def selftest() -> None:
    assert clean_line("  Profesionālā bakalaura diploms;  ") == "Profesionālā bakalaura diploms"
    assert clean_line("") is None and clean_line(None) is None

    assert parse_accreditation("Studiju virziens akreditēts līdz 26.10.2029.") == date(2029, 10, 26)
    assert parse_accreditation("Studiju programma akreditēta līdz 1.6.2027") == date(2027, 6, 1)
    assert parse_accreditation("Licencēta") is None
    assert parse_accreditation("akreditēts līdz 31.02.2029.") is None, "несуществующая дата"

    assert excerpt("Īss apraksts.") == "Īss apraksts."
    long_text = "Pirmais teikums. " + "Otrais teikums ir garāks. " * 40
    cut = excerpt(long_text, 100)
    assert cut is not None and len(cut) <= 100 and cut.endswith("."), cut
    assert excerpt("vārds " * 200, 50).endswith("…"), "без точки — обрезка по слову с многоточием"
    assert excerpt("A.\n\n\n  B   C.") == "A.\n\nB C.", "абзацы сохраняются, пробелы схлопываются"
    assert excerpt("   ") is None

    fields = {
        "Grāds": {"text": "Profesionālais bakalaurs mehatronikā", "withoutLinks": "Profesionālais bakalaurs mehatronikā"},
        "Profesionālā kvalifikācija": {
            "text": "Mehatronikas inženieris (6. PKL) Standarts / kvalifikācijas prasības",
            "withoutLinks": "Mehatronikas inženieris (6. PKL) ",
        },
        "Izglītības dokuments": {"text": "Profesionālā bakalaura diploms;", "withoutLinks": "Profesionālā bakalaura diploms;"},
        "Licence / akreditācija": {"text": "Studiju virziens akreditēts līdz 26.10.2029.", "withoutLinks": ""},
    }
    details = details_from_fields(fields)
    assert details["degree_awarded_lv"] == "Profesionālais bakalaurs mehatronikā"
    assert details["qualification_lv"] == "Mehatronikas inženieris (6. PKL)", "ссылка на стандарт отброшена"
    assert details["diploma_document_lv"] == "Profesionālā bakalaura diploms"
    assert details["accreditation_valid_until"] == "2029-10-26"
    assert details["description_lv"] is None
    assert not any(details_from_fields({}).values()), "пустая страница — все значения пустые"

    now = datetime(2026, 10, 3, 12, 0, tzinfo=timezone.utc)
    assert is_due(None, now) is True
    assert is_due("2026-09-20T12:00:00+00:00", now) is False, "13 дней — свежо"
    assert is_due("2026-08-20T12:00:00+00:00", now) is True, "44 дня — пора"
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    args = sys.argv[1:]
    if "--selftest" in args:
        selftest()
    else:
        limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
        main(apply="--apply" in args, everything="--all" in args, limit=limit)
