"""Черновики платы за обучение для иностранцев — таблица programme_fee.

Продукт для иностранцев, шаг 1б (docs/PLAN-FOREIGNERS.md). Плата — поле
правила 6 CLAUDE.md («стоимость» подтверждает только человек), поэтому
скрипт пишет ТОЛЬКО ЧЕРНОВИКИ: verified_at проставляет владелец в Studio,
до этого сайт сумму не показывает. Уже подтверждённые строки не трогаются.

Источников два. Цена пишется, только когда источник прямо называет группы;
одна цена без слов «для кого» не превращается в цену для иностранцев.

1. РТУ — английский реестр (rtu.lv/en/studies/all-study-programmes). В его
   таблицах у каждой программы две цены за год: «EU countries*» и «Non EU
   countries». Сноска к первой: «Citizens of EU, EFTA member countries and EU
   candidate countries» — граждане стран-кандидатов (Украина, Молдова…) платят
   по первой колонке. Строки помечены eu_scope = 'eu_efta_candidates', сайт
   показывает под ценами пометку (решение владельца 2026-11-08). Программа
   находится по source_url — тот же адрес пишет сборщик sources/rtu_english.py;
   программа в нескольких городах — несколько записей с одним адресом.
   Учебного года реестр не называет: черновик берёт год, в котором цена
   прочитана (ноябрь 2026 → 2026/27), — сверить при проверке.

2. ЛУ — страница каждой программы из каталога (lu.lv/en/…), поле «Tuition
   fee» в блоке фактов (тот же разбор, что у sources/lu.py). Большинство
   страниц называет две цены: «… EUR for EU/EEA/Swiss citizens, EU Long-term
   resident permit holders and their family members. … EUR for citizens of
   other countries». Первая шире нашей группы eu — строки помечены
   eu_scope = 'eu_long_term_residents'. Страница с одной ценой без групп и
   страница, где цены очной и заочной формы перемешаны, пропускаются —
   их видно в журнале. Учебный год — как у РТУ.

3. RISEBA — страницы бакалаврских программ (riseba.lv/en/program/…), поле
   «Tuition fee per year (for the 2026/2027 academic year)»: группа «Citizens
   and permanent residents of Latvia, as well as citizens of other EU, EEA, and
   EU candidate countries» и группа «Other countries», в каждой строки «цена
   (форма, язык)». Учебный год — из подписи поля. Вариант пишется, только
   если у одной формы и языка есть обе цены; программа — по адресу страницы,
   языку и форме. Группа ЕС включает страны-кандидаты — eu_scope =
   'eu_efta_candidates' (Швейцарии RISEBA не называет — сверить при проверке).
   Магистратура RISEBA в каталоге из NIID, там цен по группам нет.

Turība и TSI в robots.txt запрещают обход агентам Anthropic: их цены
собирать этим путём нельзя, черновики для них — вручную владельцем.

  python src/seed_programme_fees.py            # показать, что будет записано
  python src/seed_programme_fees.py --apply    # записать черновики
  python src/seed_programme_fees.py --only lu  # один источник: rtu, lu или riseba
  python src/seed_programme_fees.py --selftest # разбор образцов, без сети и базы
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
                    # Цитата — со страницы реестра, и ссылка — на сам реестр: цена
                    # стоит там, на карточке программы её может не быть.
                    "fee_source_url": RTU_REGISTRY_URL,
                    "eu_scope": "eu_efta_candidates",
                }
            )
    return rows


LU_EU_GROUP = re.compile(r"EUR\s+for\s+EU/EEA/Swiss", re.I)
LU_OTHER_GROUP = re.compile(r"EUR\s+for\s+citizens\s+of\s+other\s+countries", re.I)
_LU_AMOUNT = r"(\d[\d\s\xa0]*(?:,\d{2})?)\s*"


def parse_amount(text: str) -> float:
    """«4100» → 4100.0, «3700,00» → 3700.0, «4 100» → 4100.0."""
    whole = re.sub(r",\d{2}$", "", text.strip())
    return float(re.sub(r"\D", "", whole))


def lu_fee_text(page: str) -> str | None:
    """Значение поля «Tuition fee» из блока фактов страницы программы ЛУ."""
    from sources.lu import _parse_facts

    blocks = re.findall(r'<div class="ce-bodytext">(.*?)</div>', page, re.S)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</li>", "\n", "\n".join(blocks))
    return _parse_facts(html.unescape(re.sub(r"<[^>]+>", "", text))).get("fee")


def parse_lu_fee(fee_text: str) -> tuple[float, float] | str:
    """(цена eu, цена non_eu) или причина пропуска.

    Пишется только запись с ровно одной ценой каждой группы. Упоминание
    заочной формы («Part-time online studies – 3000 EUR») — пропуск: какая
    цена к какой форме, по одной строке не разобрать надёжно.
    """
    if re.search(r"part[- ]time", fee_text, re.I):
        return "цены очной и заочной формы в одном поле"
    eu = re.findall(_LU_AMOUNT + LU_EU_GROUP.pattern, fee_text, re.I)
    other = re.findall(_LU_AMOUNT + LU_OTHER_GROUP.pattern, fee_text, re.I)
    if not eu and not other:
        return "одна цена без групп"
    if len(eu) != 1 or len(other) != 1:
        return "не по одной цене на группу"
    return parse_amount(eu[0]), parse_amount(other[0])


def lu_excerpt(fee_text: str) -> str:
    # Хвост «Place of study: …» прилипает к полю у части страниц докторантуры.
    return "Tuition fee: " + re.split(r"\s*Place of study:", fee_text)[0].strip()


RISEBA_EU_HEADER = "citizens and permanent residents of latvia"
RISEBA_OTHER_HEADER = "other countries"


def parse_riseba_fees(page: str) -> tuple[str | None, list[dict]]:
    """(учебный год из подписи поля, варианты), вариант — mode, language, eu, non_eu, excerpt.

    Поле «Tuition fee per year (for the 2026/2027 academic year)»: под
    заголовком группы ЕС строки «3750 EUR (Full-time in Latvian)», под
    «Other countries» — свои. Вариант пишется, только если у одной формы и
    одного языка есть цена в обеих группах.
    """
    from sources.riseba import _extract_language, _extract_mode

    field = re.search(
        r'<div class="key">\s*(Tuition fee per year[^<]*)</div>\s*<div class="value">(.*?)</div>', page, re.S | re.I
    )
    if not field:
        return None, []
    label = _text(field.group(1))
    year_match = re.search(r"(\d{4})/(\d{4})", label)
    year = f"{year_match.group(1)}/{year_match.group(2)[2:]}" if year_match else None

    lines = [_text(line) for line in re.split(r"<br\s*/?>", field.group(2), flags=re.I)]
    groups: dict[str, dict[tuple[str, str], float]] = {"eu": {}, "non_eu": {}}
    group: str | None = None
    for line in lines:
        lowered = line.lower()
        if lowered.startswith(RISEBA_EU_HEADER):
            group = "eu"
            continue
        if lowered.startswith(RISEBA_OTHER_HEADER):
            group = "non_eu"
            continue
        match = re.match(r"([\d\s,.]+)\s*EUR\s*\(([^)]+)\)", line, re.I)
        if not match or group is None:
            continue
        mode, language = _extract_mode(match.group(2)), _extract_language(match.group(2))
        if mode and language:
            groups[group][(mode, language)] = parse_amount(match.group(1).replace(".", ""))

    excerpt = f"{label} " + " ".join(line for line in lines if line)
    variants = [
        {"mode": mode, "language": language, "eu": eu, "non_eu": groups["non_eu"][(mode, language)], "excerpt": excerpt}
        for (mode, language), eu in groups["eu"].items()
        if (mode, language) in groups["non_eu"]
    ]
    return year, variants


def fee_rows(registry_row: dict, programme_id: str, year: str) -> list[dict]:
    """Черновики programme_fee для одной программы: по строке на группу с ценой.
    registry_row — цена из любого источника: eu, non_eu, excerpt, fee_source_url, eu_scope."""
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
                "source_url": registry_row["fee_source_url"],
                "source_excerpt": registry_row["excerpt"],
                # Кого вуз относит к цене eu (миграция 20261108130000). Пишется
                # обеим группам — блок на сайте видит пометку, какая бы из них
                # ни была подтверждена.
                "eu_scope": registry_row["eu_scope"],
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


LU_SAMPLE = """<div class="ce-bodytext"><p>Programme level: Master<br>Language of instruction: English<br>
Tuition fee: 2800 EUR for EU/EEA/Swiss citizens, EU Long-term resident permit holders and their family
members. 3200 EUR for citizens of other countries<br>Study location: Riga</p></div>"""


RISEBA_SAMPLE = """<li class="list-group-item ps-0"><div class="key">
    Tuition fee per year (for the 2026/2027 academic year):
</div>
<div class="value">
    Citizens and permanent residents of Latvia, as well as citizens of other EU, EEA, and EU candidate countries:<br />
3750 EUR (Full-time in Latvian)<br />
3200 EUR (Part-time in Latvian)<br />
4500 EUR (Full-time in English)<br />
<br />
Other countries:<br />
5600 EUR (Full-time in English)                                    </div></li>"""


def selftest() -> None:
    assert academic_year(date(2026, 11, 8)) == "2026/27"
    assert academic_year(date(2027, 3, 1)) == "2026/27"
    assert academic_year(date(2027, 9, 1)) == "2027/28"
    assert parse_price("€ 4 030") == 4030.0 and parse_price("-") is None

    # РТУ
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
        assert fee["eu_scope"] == "eu_efta_candidates" and fee["source_url"] == RTU_REGISTRY_URL

    # ЛУ: формулировки, встреченные на страницах 2026-11-09
    fee_text = lu_fee_text(LU_SAMPLE)
    assert fee_text and parse_lu_fee(fee_text) == (2800.0, 3200.0), fee_text
    assert parse_lu_fee(
        "full-time - 4100 EUR for EU/EEA/Swiss citizens, EU Long-term resident permit holders and their family "
        "members. 4100 EUR for citizens of other countries."
    ) == (4100.0, 4100.0)
    assert parse_lu_fee(
        "3700,00 EUR for EU/EEA/Swiss citizens, EU Long-term resident permit holders and their family members. "
        "4700,00 EUR for citizens of other countries"
    ) == (3700.0, 4700.0)
    doctoral = (
        "-3300 EUR for EU/EEA/Swiss Confederation citizens, permanent residents and their family members "
        "-7500 EUR for citizens of other countries Place of study: Riga, Jelgavas Street 1"
    )
    assert parse_lu_fee(doctoral) == (3300.0, 7500.0)
    assert not lu_excerpt(doctoral).endswith("Street 1") and lu_excerpt(doctoral).startswith("Tuition fee: -3300")
    assert parse_lu_fee("2900 EUR per year") == "одна цена без групп"
    assert parse_lu_fee(
        "full-time studies – 4000 EUR for EU/EEA/Swiss Confederation citizens, permanent residents and their family "
        "members; 5200 EUR for citizens of other countries. Part-time online studies – 3000 EUR"
    ) == "цены очной и заочной формы в одном поле"
    # RISEBA: вариант только с обеими ценами; учебный год — из подписи
    year, variants = parse_riseba_fees(RISEBA_SAMPLE)
    assert year == "2026/27", year
    assert [(v["mode"], v["language"], v["eu"], v["non_eu"]) for v in variants] == [
        ("full_time", "en", 4500.0, 5600.0)
    ], variants
    assert "EU candidate countries" in variants[0]["excerpt"] and "Other countries" in variants[0]["excerpt"]
    assert parse_riseba_fees("<html></html>") == (None, [])
    print("selftest ok")


def rtu_prices(fetch, programmes: list[dict]) -> tuple[list[tuple[dict, dict]], list[str]]:
    """(программа, цена) по реестру РТУ и строки реестра, которых нет в каталоге."""
    by_url: dict[str, list[dict]] = {}
    for programme in programmes:
        by_url.setdefault(programme["source_url"] or "", []).append(programme)
    pairs: list[tuple[dict, dict]] = []
    skipped: list[str] = []
    for row in parse_rtu_registry(fetch(RTU_REGISTRY_URL)):
        matches = by_url.get(row["source_url"], [])
        if not matches:
            # Программы, которой нет в каталоге, плата не создаёт — её сначала
            # должен записать сборщик rtu_english.
            skipped.append(f"{row['name']}: нет в каталоге — {row['source_url']}")
        pairs.extend((programme, row) for programme in matches)
    return pairs, skipped


def lu_prices(fetch, programmes: list[dict]) -> tuple[list[tuple[dict, dict]], list[str]]:
    """(программа, цена) со страниц программ ЛУ и пропущенные страницы с причиной."""
    pairs: list[tuple[dict, dict]] = []
    skipped: list[str] = []
    for programme in programmes:
        url = programme["source_url"] or ""
        if not url.startswith("https://www.lu.lv/en/"):
            continue
        try:
            fee_text = lu_fee_text(fetch(url))
        except Exception as exc:  # noqa: BLE001 — страница пропала: в журнал, не падаем
            skipped.append(f"{programme['slug']}: страница не открылась ({type(exc).__name__}) — {url}")
            continue
        parsed = parse_lu_fee(fee_text) if fee_text else "нет поля Tuition fee"
        if isinstance(parsed, str):
            skipped.append(f"{programme['slug']}: {parsed} — {url}")
            continue
        eu, non_eu = parsed
        pairs.append(
            (
                programme,
                {
                    "eu": eu,
                    "non_eu": non_eu,
                    "excerpt": lu_excerpt(fee_text or ""),
                    "fee_source_url": url,
                    "eu_scope": "eu_long_term_residents",
                },
            )
        )
    return pairs, skipped


def riseba_prices(fetch, programmes: list[dict]) -> tuple[list[tuple[dict, dict]], list[str]]:
    """(программа, цена) со страниц бакалавриата RISEBA и пропущенные варианты."""
    pairs: list[tuple[dict, dict]] = []
    skipped: list[str] = []
    by_url: dict[str, list[dict]] = {}
    for programme in programmes:
        if (programme["source_url"] or "").startswith("https://riseba.lv/en/program/"):
            by_url.setdefault(programme["source_url"], []).append(programme)
    for url, candidates in by_url.items():
        try:
            year, variants = parse_riseba_fees(fetch(url))
        except Exception as exc:  # noqa: BLE001 — страница пропала: в журнал, не падаем
            skipped.append(f"{url}: страница не открылась ({type(exc).__name__})")
            continue
        if not variants:
            skipped.append(f"{url}: нет варианта с ценой в обеих группах")
        for variant in variants:
            matches = [
                p
                for p in candidates
                if p["language_of_instruction"] == variant["language"] and p["study_mode"] == variant["mode"]
            ]
            if not matches:
                skipped.append(f"{url}: {variant['mode']}/{variant['language']} — нет в каталоге")
            for programme in matches:
                pairs.append(
                    (
                        programme,
                        {
                            "eu": variant["eu"],
                            "non_eu": variant["non_eu"],
                            "excerpt": variant["excerpt"],
                            "fee_source_url": url,
                            "eu_scope": "eu_efta_candidates",
                            "academic_year": year,
                        },
                    )
                )
    return pairs, skipped


# университет в базе → источник цен
SOURCES = {"rtu": rtu_prices, "lu": lu_prices, "riseba": riseba_prices}


def main(apply: bool, only: str | None) -> None:
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute
    from polite import fetch_text

    load_dotenv()
    client = get_service_client()

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
    for slug, source in SOURCES.items():
        if only and slug != only:
            continue
        university = execute(client.table("university").select("id").eq("slug", slug)).data[0]
        programmes = execute(
            client.table("programme")
            .select("id, slug, source_url, language_of_instruction, study_mode")
            .eq("university_id", university["id"])
        ).data
        pairs, skipped = source(fetch_text, programmes)

        drafts: list[dict] = []
        for programme, price in pairs:
            # год из источника (RISEBA называет его), иначе — год прочтения
            for fee in fee_rows(price, programme["id"], price.get("academic_year") or year):
                drafts.append(fee)
                print(f"{slug} {programme['slug']}: {fee['applies_to']} {fee['amount']:.0f} EUR / год ({fee['academic_year']})")

        written = skipped_verified = 0
        for fee in drafts:
            prior = existing.get((fee["programme_id"], fee["kind"], fee["applies_to"], fee["academic_year"]))
            if prior and prior["verified_at"]:
                skipped_verified += 1
                continue
            if apply:
                execute(
                    client.table("programme_fee").upsert(fee, on_conflict="programme_id,kind,applies_to,academic_year")
                )
                written += 1

        if skipped:
            print(f"\n{slug}: пропущено {len(skipped)}:")
            for line in skipped:
                print(f"  {line}")
        print(
            f"\n{slug}: программ с ценой: {len(pairs)}; черновиков: {len(drafts)}; записано: {written}; "
            f"подтверждённых не тронуто: {skipped_verified}"
            + ("" if apply else " (сухой прогон — запись только с --apply)")
            + "\n"
        )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
        if only is not None and only not in SOURCES:
            raise SystemExit(f"--only: один из {', '.join(SOURCES)}")
        main("--apply" in sys.argv, only)
