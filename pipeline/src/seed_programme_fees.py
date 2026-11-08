"""Черновики платы за обучение для иностранцев — таблица programme_fee.

Продукт для иностранцев, шаг 1б (docs/PLAN-FOREIGNERS.md). Плата — поле
правила 6 CLAUDE.md («стоимость» подтверждает только человек), поэтому
скрипт пишет ТОЛЬКО ЧЕРНОВИКИ: verified_at проставляет владелец в Studio,
до этого сайт сумму не показывает. Уже подтверждённые строки не трогаются.

Источники по одному; сейчас один — английский реестр РТУ
(rtu.lv/en/studies/all-study-programmes). В его таблицах у каждой программы
две цены за год: «EU countries*» и «Non EU countries». Сноска к первой:
«Citizens of EU, EFTA member countries and EU candidate countries» —
то есть граждане стран-кандидатов (Украина, Молдова, Грузия и др.) платят
по первой колонке. У нас группа eu — «граждане ЕС, ЕЭЗ и Швейцарии», поэтому
сноска дословно лежит в цитате каждой строки, а строки помечены
eu_scope = 'eu_efta_candidates' — сайт показывает под ценами пометку
(решение владельца 2026-11-08).

Программа находится по source_url: тот же адрес карточки записывает в
programme сборщик sources/rtu_english.py. Программа в нескольких городах —
несколько записей с одним адресом, плата пишется каждой.

Учебного года реестр не называет. Черновик берёт учебный год, в котором
цена прочитана (ноябрь 2026 → 2026/27); при проверке его стоит сверить с
правилами приёма РТУ и при необходимости исправить в Studio.

  python src/seed_programme_fees.py            # показать, что будет записано
  python src/seed_programme_fees.py --apply    # записать черновики
  python src/seed_programme_fees.py --selftest # разбор образца таблицы, без сети и базы
"""

from __future__ import annotations

import html
import re
import sys
from datetime import date
from urllib.parse import urljoin

RTU_REGISTRY_URL = "https://www.rtu.lv/en/studies/all-study-programmes"
RTU_FOOTNOTE = "* Citizens of EU, EFTA member countries and EU candidate countries"


def academic_year(today: date) -> str:
    """Учебный год с 1 сентября: 2026-11-08 → «2026/27», 2027-03-01 → «2026/27»."""
    start = today.year if today.month >= 9 else today.year - 1
    return f"{start}/{str(start + 1)[2:]}"


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def parse_price(text: str) -> float | None:
    """«€ 4 030» → 4030.0; прочерк или пусто — пусто."""
    digits = re.sub(r"\D", "", text)
    return float(digits) if digits else None


def parse_rtu_registry(page: str) -> list[dict]:
    """Строки реестра: адрес карточки, название, обе цены и строка-цитата.

    Порядок колонок проверяется по заголовку каждой таблицы: если «EU
    countries» не стоит перед «Non EU countries», таблица пропускается —
    перепутанная цена хуже отсутствующей.
    """
    rows: list[dict] = []
    for table in re.findall(r"<table\b.*?</table>", page, re.S | re.I):
        # Заголовок — всё до первой ссылки на программу: у РТУ он в обычных
        # ячейках <td>, двумя строками («Price per year» над двумя колонками).
        header = _text(table.split("<a", 1)[0])
        eu_at, non_eu_at = header.find("EU countries"), header.find("Non EU countries")
        if eu_at < 0 or non_eu_at < 0 or eu_at > non_eu_at:
            continue
        for tr in re.findall(r"<tr\b.*?</tr>", table, re.S | re.I):
            link = re.search(r'<a\b[^>]*href="([^"]+)"', tr, re.I)
            cells = [_text(cell) for cell in re.findall(r"<td\b.*?</td>", tr, re.S | re.I)]
            if not link or len(cells) < 4:
                continue
            eu, non_eu = parse_price(cells[2]), parse_price(cells[3])
            if eu is None and non_eu is None:
                continue
            rows.append(
                {
                    "source_url": urljoin(RTU_REGISTRY_URL, html.unescape(link.group(1))),
                    "name": cells[0],
                    "eu": eu,
                    "non_eu": non_eu,
                    "excerpt": (
                        f"{cells[0]} | {cells[1]} | Price per year: EU countries* {cells[2]} | "
                        f"Non EU countries {cells[3]}. {RTU_FOOTNOTE}"
                    ),
                }
            )
    return rows


def fee_rows(registry_row: dict, programme_id: str, year: str) -> list[dict]:
    """Черновики programme_fee для одной программы: по строке на группу с ценой."""
    result = []
    for applies_to in ("eu", "non_eu"):
        amount = registry_row[applies_to]
        if amount is None:
            continue
        result.append(
            {
                "programme_id": programme_id,
                "kind": "tuition",
                "applies_to": applies_to,
                "amount": amount,
                "currency": "EUR",
                "period": "year",
                "academic_year": year,
                # Цитата — со страницы реестра, а ссылка — на сам реестр: цена
                # стоит там, на карточке программы её может не быть.
                "source_url": RTU_REGISTRY_URL,
                "source_excerpt": registry_row["excerpt"],
                # Сноска реестра: цену eu платят и граждане ЕАСТ и стран-кандидатов
                # (миграция 20261108130000). Пишется обеим группам — блок на сайте
                # видит пометку, какая бы из них ни была подтверждена.
                "eu_scope": "eu_efta_candidates",
            }
        )
    return result


SAMPLE = """
<table class="study_program_table"><tbody><tr><td rowspan="2">Study programme</td><td rowspan="2">Duration of studies</td><td colspan="2"><b>Price per year</b></td>
<td rowspan="2">Intake</td></tr><tr><td>EU countries*</td><td>Non EU countries</td></tr>
<tr><td colspan="5">First-Cycle Higher Education (Academic Bachelor) Studies:</td></tr>
<tr><td><a href="/en/studies/all-study-programmes/open/civil-construction?id=190&amp;x=1">Civil Construction and
 Real Estate Management</a></td><td>1.5&nbsp;-&nbsp;2.5&nbsp;years</td><td>&euro;&nbsp;4&nbsp;290</td>
<td>&euro;&nbsp;5&nbsp;250</td><td>Autumn</td></tr>
<tr><td><a href="/en/x?id=1">No price</a></td><td>3 years</td><td>-</td><td>-</td><td>Autumn</td></tr>
</table>
<table><tr><th>Study programme</th><th>Non EU countries</th><th>EU countries*</th></tr>
<tr><td><a href="/en/y?id=2">Swapped</a></td><td>3 years</td><td>€ 1</td><td>€ 2</td></tr></table>
"""


def selftest() -> None:
    assert academic_year(date(2026, 11, 8)) == "2026/27"
    assert academic_year(date(2027, 3, 1)) == "2026/27"
    assert academic_year(date(2027, 9, 1)) == "2027/28"
    assert parse_price("€ 4 030") == 4030.0 and parse_price("-") is None

    rows = parse_rtu_registry(SAMPLE)
    assert len(rows) == 1, rows  # строка без цен и таблица с переставленными колонками пропущены
    row = rows[0]
    assert row["source_url"] == "https://www.rtu.lv/en/studies/all-study-programmes/open/civil-construction?id=190&x=1"
    assert row["name"] == "Civil Construction and Real Estate Management"
    assert (row["eu"], row["non_eu"]) == (4290.0, 5250.0)
    assert RTU_FOOTNOTE in row["excerpt"]

    fees = fee_rows(row, "p1", "2026/27")
    assert [(fee["applies_to"], fee["amount"]) for fee in fees] == [("eu", 4290.0), ("non_eu", 5250.0)]
    for fee in fees:
        assert "verified_at" not in fee and "verified_by" not in fee  # их ставит только человек
        assert re.fullmatch(r"\d{4}/\d{2}", fee["academic_year"])
        assert fee["eu_scope"] == "eu_efta_candidates"
    print("selftest ok")


def main(apply: bool) -> None:
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute
    from polite import fetch_text

    load_dotenv()
    client = get_service_client()

    registry = parse_rtu_registry(fetch_text(RTU_REGISTRY_URL))
    university = execute(client.table("university").select("id").eq("slug", "rtu")).data[0]
    programmes = execute(
        client.table("programme").select("id, slug, source_url").eq("university_id", university["id"])
    ).data
    by_url: dict[str, list[dict]] = {}
    for programme in programmes:
        by_url.setdefault(programme["source_url"] or "", []).append(programme)

    try:
        existing_rows = execute(
            client.table("programme_fee").select("programme_id, kind, applies_to, academic_year, verified_at")
        ).data
    except Exception as exc:  # noqa: BLE001
        # Таблицы нет, пока владелец не применил миграцию 20261108120000_foreign_costs.sql.
        # Сухой прогон всё равно показывает черновики; запись без таблицы невозможна.
        if apply:
            raise SystemExit(f"programme_fee не читается ({exc}) — сначала примените миграцию в Studio") from exc
        print("programme_fee ещё нет в базе (миграция не применена) — показываю черновики без сверки\n")
        existing_rows = []
    existing = {
        (row["programme_id"], row["kind"], row["applies_to"], row["academic_year"]): row for row in existing_rows
    }

    year = academic_year(date.today())
    drafts: list[dict] = []
    unmatched: list[str] = []
    for row in registry:
        matches = by_url.get(row["source_url"], [])
        if not matches:
            unmatched.append(f"{row['name']} — {row['source_url']}")
        for programme in matches:
            for fee in fee_rows(row, programme["id"], year):
                drafts.append(fee)
                print(f"{programme['slug']}: {fee['applies_to']} {fee['amount']:.0f} EUR / год ({year})")

    written = skipped_verified = 0
    for fee in drafts:
        key = (fee["programme_id"], fee["kind"], fee["applies_to"], fee["academic_year"])
        prior = existing.get(key)
        if prior and prior["verified_at"]:
            skipped_verified += 1
            continue
        if apply:
            execute(client.table("programme_fee").upsert(fee, on_conflict="programme_id,kind,applies_to,academic_year"))
            written += 1

    if unmatched:
        # Программы, которой нет в каталоге, плата не создаёт — её сначала
        # должен записать сборщик rtu_english.
        print("\nнет в каталоге (по адресу карточки):")
        for line in unmatched:
            print(f"  {line}")
    print(
        f"\nстрок реестра с ценой: {len(registry)}; черновиков: {len(drafts)}; записано: {written}; "
        f"подтверждённых не тронуто: {skipped_verified}"
        + ("" if apply else " (сухой прогон — запись только с --apply)")
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        main("--apply" in sys.argv)
