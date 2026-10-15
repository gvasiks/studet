"""Эстония: условия конкурса со страницы SAIS — форма обучения, место учёбы,
начало занятий, нагрузка и финансирование с ценой (колонки ee_admission).
Кроме того, сохраняется раздел «Vastuvõtukriteeriumid» как есть и ссылка из
него на страницу программы у вуза: из них правило конкурса разбирает
ee_load_rules.py.

Страница конкурса (sais.ee/AdmissionSearch/View/N) открыта без входа, файла
robots.txt у сайта нет. Устроена одинаково у всех учреждений: слева подписи
(«Õppevorm:», «Õppetöö asukoht:», «Finantseering:»), справа значения.

Читаются только те конкурсы, которые ещё не читались или срок которых не
прошёл (условия открытого конкурса вуз может править). Прошедший конкурс не
меняется, поэтому первый запуск идёт около двадцати минут (около пятисот
страниц с паузами, polite.py), следующие — минуту-две.

Страницы старых конкурсов SAIS удаляет: адрес конкурса 2024 года
переадресует на страницу ошибки (проверено 2026-10-13). Поэтому конкурсы,
срок которых прошёл больше года назад, не запрашиваются вовсе, а у более
свежего конкурса с удалённой страницей условия остаются пустыми — сайт на
такую страницу не ссылается.

Сначала должны пройти каталог и сроки приёма:
  python src/main.py ee_haridusportaal
  python src/ee_load_admissions.py --apply

Колонки — миграции 20261014120000_ee_admission_details.sql и
20261015120000_ee_admission_rule.sql.

Запуск:
  python src/ee_load_admission_details.py --selftest
  python src/ee_load_admission_details.py --limit 10   # прочитать и показать, без записи
  python src/ee_load_admission_details.py --apply
  python src/ee_load_admission_details.py --apply --all  # перечитать все, а не только новые
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

# Подписи полей на странице, по-эстонски (страница открывается с эстонским
# языком браузера — см. main()).
LABEL_INSTITUTION = "Õppeasutus"
LABEL_FORM = "Õppevorm"
LABEL_STARTS = "Õppetöö alguse aeg"
LABEL_LOCATION = "Õppetöö asukoht"
LABEL_FUNDING = "Finantseering"
LABEL_CRITERIA = "Vastuvõtukriteeriumid"

# Конкурсы старше этого срока не запрашиваются: их страниц в SAIS уже нет,
# а каждый такой запрос заводит на той стороне запись об ошибке.
MAX_AGE_DAYS = 365

LOADS = {"täiskoormus": "full", "osakoormus": "part", "määramata": "unspecified"}
PAID = {"tasuta": False, "tasuline": True}

_LOAD_LINE = re.compile(r"^(täiskoormus|osakoormus|määramata)\s*:\s*(tasuta|tasuline)?$", re.IGNORECASE)
_FIELD_LINE = re.compile(r"^(Sihtgrupp|Valuuta|Hind|Periood|Rohkem infot)\s*:\s*(.*)$")

# Вытащить со страницы заголовок и пары «подпись — значение». Значение
# берётся у всей правой колонки, а не у абзаца в ней: в блоке финансирования
# цены свёрстаны блоками внутри абзаца, и браузер выносит их из абзаца наружу.
# Условия конкурса — блок рядом с подписью «Vastuvõtukriteeriumid» (список
# или абзацы); ссылка «Rohkem infot» стоит под ним, в том же разделе.
EXTRACT_JS = """() => {
  const label = [...document.querySelectorAll('label')].find((el) => el.innerText.trim() === 'Vastuvõtukriteeriumid');
  const heading = [...document.querySelectorAll('h2')].find((el) => el.innerText.trim() === 'Vastuvõtukriteeriumid');
  const link = heading && [...heading.parentElement.querySelectorAll('a[href^="http"]')].find((a) => a.innerText.trim() === 'Rohkem infot');
  return {
    title: (document.querySelector('h1') || {}).innerText || '',
    pairs: [...document.querySelectorAll('.form-group')].map((group) => [
      (group.querySelector('label') || {}).innerText || '',
      (group.querySelector('.col-sm-9') || group).innerText || '',
    ]),
    criteria: label && label.nextElementSibling ? label.nextElementSibling.innerText : '',
    info_url: link ? link.href : '',
  };
}"""


class PageChanged(RuntimeError):
    """Страница не похожа на страницу конкурса SAIS."""


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def period_key(text: str) -> str:
    """За что цена: семестр, год, кредитный пункт. Незнакомое — 'other',
    исходный текст остаётся рядом в period_text."""
    lowered = text.lower()
    if "eap" in lowered or "ainepunkt" in lowered:
        return "credit"
    if "semest" in lowered:
        return "semester"
    if "aasta" in lowered:
        return "year"
    return "other"


def amount_of(text: str) -> float | None:
    """«4 050», «1050», «3680,50» -> число; не число — None."""
    digits = re.sub(r"[\s ]", "", text).replace(",", ".")
    if not re.fullmatch(r"\d+(\.\d+)?", digits):
        return None
    value = float(digits)
    return value if value > 0 else None


def parse_funding(text: str) -> list[dict]:
    """Блок «Finantseering»: строки вида

        täiskoormus: tasuta
        osakoormus: tasuline
        Sihtgrupp:
        Valuuta: EUR
        Hind: 1050
        Periood: semester
        Rohkem infot: …

    Вариант нагрузки начинается строкой «нагрузка: платно/бесплатно»; всё,
    что идёт до следующего такого начала, относится к нему. Цена собирается
    от «Sihtgrupp» до «Periood». Пояснения («Rohkem infot») не хранятся."""
    lines = [clean(line) for line in text.splitlines()]
    lines = [line for line in lines if line]
    entries: list[dict] = []
    price: dict | None = None
    skipping_note = False
    index = 0
    while index < len(lines):
        line = lines[index]
        load = _LOAD_LINE.match(line)
        if load:
            paid_word = load.group(2)
            # «tasuta» иногда стоит на следующей строке
            if paid_word is None and index + 1 < len(lines) and lines[index + 1].lower() in PAID:
                paid_word = lines[index + 1]
                index += 1
            if paid_word is not None:
                entries.append({"load": LOADS[load.group(1).lower()], "paid": PAID[paid_word.lower()], "prices": []})
                price, skipping_note = None, False
            index += 1
            continue
        field = _FIELD_LINE.match(line)
        if field and entries:
            name, value = field.group(1), field.group(2).strip()
            skipping_note = name == "Rohkem infot"
            if name == "Sihtgrupp":
                price = {"target": value or None}
            elif name == "Valuuta" and price is not None:
                price["currency"] = value or None
            elif name == "Hind" and price is not None:
                price["amount"] = amount_of(value)
            elif name == "Periood" and price is not None:
                price["period"] = period_key(value)
                price["period_text"] = value or None
                if price.get("amount") is not None and price.get("currency"):
                    entries[-1]["prices"].append(
                        {
                            "amount": price["amount"],
                            "currency": price["currency"],
                            "period": price["period"],
                            "period_text": price["period_text"],
                            "target": price.get("target"),
                        }
                    )
                price = None
        elif price is not None and not skipping_note and "target" in price and price["target"] is None and "currency" not in price:
            # значение «Sihtgrupp» на отдельной строке
            price["target"] = line
        index += 1
    return entries


def parse_date(text: str) -> str | None:
    match = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", clean(text))
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        return datetime(year, month, day).date().isoformat()
    except ValueError:
        return None


def parse_location(text: str) -> str | None:
    """«Eesti ,\\n Tartu» -> «Tartu»; «Tallinn, Kännu 67» остаётся как есть.
    Одна буква («t» у одного конкурса 2026 года) — опечатка в источнике, а
    не место: значение остаётся пустым."""
    value = clean(text)
    value = re.sub(r"^Eesti\s*,\s*", "", value)
    return value if len(value) >= 2 else None


def parse_study_form(text: str) -> str | None:
    """«päevane õpe»; у конкурса бывает две формы, каждая на своей строке —
    тогда «päevane õpe, sessioonõpe». «määramata» («не определена») SAIS
    пишет, когда вуз форму не указал: это отсутствие значения."""
    forms = [clean(line).lower() for line in (text or "").splitlines()]
    forms = [form for form in forms if form and form != "määramata"]
    return ", ".join(dict.fromkeys(forms)) or None


def parse_criteria(text: str) -> str | None:
    """Раздел «Vastuvõtukriteeriumid»: строки как на странице, без пустых и
    без лишних пробелов. Разбирает его ee_rules.py."""
    lines = [clean(line) for line in (text or "").replace("\xa0", " ").splitlines()]
    return "\n".join(line for line in lines if line) or None


def parse_info_url(url: str) -> str | None:
    """Ссылка «Rohkem infot» — только настоящий адрес в интернете."""
    url = (url or "").strip()
    return url if url.startswith("https://") or url.startswith("http://") else None


def parse_page(title: str, pairs: list[list[str]], criteria: str = "", info_url: str = "") -> dict:
    """Условия конкурса из заголовка, пар «подпись — значение» и раздела
    «Vastuvõtukriteeriumid»."""
    fields = {clean(label).rstrip(":").strip(): value for label, value in pairs}
    if LABEL_INSTITUTION not in fields:
        raise PageChanged("на странице нет подписи «Õppeasutus» — это не страница конкурса или она на другом языке")
    return {
        "title": clean(title) or None,
        "study_form": parse_study_form(fields.get(LABEL_FORM, "")),
        "location": parse_location(fields.get(LABEL_LOCATION, "")),
        "starts_on": parse_date(fields.get(LABEL_STARTS, "")),
        "funding": parse_funding(fields.get(LABEL_FUNDING, "")),
        "criteria_text": parse_criteria(criteria),
        "info_url": parse_info_url(info_url),
    }


def _selftest() -> None:
    assert amount_of("1050") == 1050 and amount_of("4 050") == 4050 and amount_of("3680,50") == 3680.5
    assert amount_of("") is None and amount_of("tasuta") is None and amount_of("0") is None
    assert period_key("semester") == "semester" and period_key("aastamakse") == "year"
    assert period_key("1 EAP") == "credit" and period_key("kuu") == "other"
    assert parse_date("01.09.2026") == "2026-09-01" and parse_date("") is None and parse_date("31.02.2026") is None
    assert parse_location("Eesti ,\n Tartu") == "Tartu"
    assert parse_location("Tartu") == "Tartu"
    assert parse_location("Eesti , Tallinn, Kännu 67") == "Tallinn, Kännu 67"
    assert parse_location("") is None and parse_location("t") is None
    assert parse_study_form("päevane õpe \n") == "päevane õpe"
    assert parse_study_form("päevane õpe\nsessioonõpe\n") == "päevane õpe, sessioonõpe"
    assert parse_study_form("määramata") is None and parse_study_form("") is None

    # полная нагрузка бесплатно — без цен
    assert parse_funding("täiskoormus:\ntasuta") == [{"load": "full", "paid": False, "prices": []}]
    assert parse_funding("täiskoormus: tasuta") == [{"load": "full", "paid": False, "prices": []}]
    assert parse_funding("") == []

    # Pallas, «Maal»: три варианта, у двух — цена; пояснение не хранится,
    # даже если в нём есть слова «täiskoormusega» и двоеточия
    pallas = """täiskoormus: tasuta
osakoormus: tasuline
Sihtgrupp:
Valuuta: EUR
Hind: 1050
Periood: semester
Rohkem infot:
Osakoormusega õpe
Täiskoormusega õppivad üliõpilased
– kes õppima asudes on juba immatrikuleeritud kõrgharidustaseme tasuta õppesse;
määramata: tasuline
Sihtgrupp:
Valuuta: EUR
Hind: 40
Periood: 1 EAP
Rohkem infot:"""
    assert parse_funding(pallas) == [
        {"load": "full", "paid": False, "prices": []},
        {"load": "part", "paid": True, "prices": [
            {"amount": 1050.0, "currency": "EUR", "period": "semester", "period_text": "semester", "target": None},
        ]},
        {"load": "unspecified", "paid": True, "prices": [
            {"amount": 40.0, "currency": "EUR", "period": "credit", "period_text": "1 EAP", "target": None},
        ]},
    ], parse_funding(pallas)

    # EBS: две цены у одной нагрузки, у каждой своя целевая группа
    ebs = """täiskoormus: tasuline
Sihtgrupp: Sügissemester
Valuuta: EUR
Hind: 4050
Periood: semester
Sihtgrupp: Kevadsemester
Valuuta: EUR
Hind: 3680
Periood: semester
Rohkem infot: Õppemaksu tasutakse semestri ehk poolaasta kaupa."""
    funding = parse_funding(ebs)
    assert len(funding) == 1 and funding[0]["paid"] is True
    assert [(price["target"], price["amount"]) for price in funding[0]["prices"]] == [("Sügissemester", 4050.0), ("Kevadsemester", 3680.0)]

    # целевая группа на отдельной строке; цена без суммы не записывается
    assert parse_funding("osakoormus: tasuline\nSihtgrupp:\nKõik\nValuuta: EUR\nHind: 3960\nPeriood: aastamakse")[0]["prices"] == [
        {"amount": 3960.0, "currency": "EUR", "period": "year", "period_text": "aastamakse", "target": "Kõik"},
    ]
    assert parse_funding("osakoormus: tasuline\nSihtgrupp:\nValuuta: EUR\nHind:\nPeriood: semester")[0]["prices"] == []

    page = parse_page(
        "Maal ",
        [
            ["Õppeasutus:", "Kõrgem Kunstikool Pallas"],
            ["Õppetase:", "rakenduskõrgharidusõpe (514)"],
            ["Õppevorm:", "päevane õpe \n"],
            ["Õppetöö alguse aeg:", "01.09.2026"],
            ["Õppetöö asukoht:", "Eesti ,\n Tartu"],
            ["Finantseering:", "täiskoormus:\ntasuta"],
        ],
    )
    assert page == {
        "title": "Maal",
        "study_form": "päevane õpe",
        "location": "Tartu",
        "starts_on": "2026-09-01",
        "funding": [{"load": "full", "paid": False, "prices": []}],
        "criteria_text": None,
        "info_url": None,
    }, page
    # условия конкурса: строки списка и абзацев, неразрывные пробелы
    with_criteria = parse_page(
        "Informaatika (BSc)",
        [["Õppeasutus:", "Tartu Ülikool"]],
        "Riigieksamid\neesti keele riigieksam 40%\xa0\n\n  matemaatika riigieksam 60%\nVÕI\n",
        " https://ut.ee/et/oppekavad/informaatika ",
    )
    assert with_criteria["criteria_text"] == "Riigieksamid\neesti keele riigieksam 40%\nmatemaatika riigieksam 60%\nVÕI"
    assert with_criteria["info_url"] == "https://ut.ee/et/oppekavad/informaatika"
    assert parse_info_url("javascript:void(0)") is None and parse_info_url("") is None
    assert parse_page("X", [["Õppeasutus:", "Tallinna Ülikool"], ["Õppevorm:", "määramata"]])["study_form"] is None
    # нет начала занятий и места — пусто, а не догадка
    bare = parse_page("X", [["Õppeasutus:", "Tartu Ülikool"], ["Õppevorm:", "sessioonõpe"]])
    assert (bare["study_form"], bare["location"], bare["starts_on"], bare["funding"]) == ("sessioonõpe", None, None, [])
    # страница на другом языке или не страница конкурса
    try:
        parse_page("X", [["Institution:", "University of Tartu"]])
    except PageChanged:
        pass
    else:
        raise AssertionError("ожидалась ошибка PageChanged")
    print("ee_load_admission_details selftest: ok")


def main() -> None:
    args = sys.argv[1:]
    sys.stdout.reconfigure(encoding="utf-8")
    if "--selftest" in args:
        _selftest()
        return
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright

    import polite
    from db import fetch_all, get_service_client
    from db_retry import execute

    load_dotenv()
    polite.install()
    apply = "--apply" in args
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None

    client = get_service_client()
    columns = "programme_id, admission_id, sais_url, closes_at, details_fetched_at"
    try:
        stored = fetch_all(lambda: client.table("ee_admission").select(columns).order("programme_id"))
    except Exception:  # noqa: BLE001 — колонок деталей ещё нет: миграция не применена
        if apply:
            raise
        print("колонок с условиями конкурса в базе ещё нет (миграция не применена) — читаю без учёта прочитанного")
        stored = fetch_all(
            lambda: client.table("ee_admission").select("programme_id, admission_id, sais_url, closes_at").order("programme_id")
        )

    now = datetime.now(timezone.utc).isoformat()
    oldest = (datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)).isoformat()
    urls: dict[int, str] = {}
    too_old: set[int] = set()
    for row in stored:
        if row["closes_at"] is None or row["closes_at"] < oldest:
            too_old.add(row["admission_id"])
            continue
        open_now = row["closes_at"] >= now
        if "--all" in args or row.get("details_fetched_at") is None or open_now:
            urls[row["admission_id"]] = row["sais_url"]
    # свежие первыми: при пробном запуске с --limit видны действующие страницы
    todo = sorted(urls.items(), reverse=True)[:limit] if limit else sorted(urls.items(), reverse=True)
    print(
        f"конкурсов в базе: {len({row['admission_id'] for row in stored})} | "
        f"старше {MAX_AGE_DAYS} дней или без срока (не запрашиваются): {len(too_old)} | к чтению: {len(todo)}"
    )

    parsed: dict[int, dict] = {}
    gone: list[int] = []
    failed: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # эстонский язык браузера: иначе SAIS может отдать страницу по-английски
        page = browser.new_page(locale="et-EE")
        for number, (admission_id, url) in enumerate(todo, start=1):
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                if response is None or response.status != 200:
                    raise PageChanged(f"ответ {response.status if response else 'пустой'}")
                if "/Error" in page.url:
                    # страницу конкурса SAIS уже удалил — это не сбой чтения
                    gone.append(admission_id)
                    continue
                data = page.evaluate(EXTRACT_JS)
                parsed[admission_id] = parse_page(data["title"], data["pairs"], data["criteria"], data["info_url"])
            except Exception as exc:  # noqa: BLE001 — одна страница не останавливает остальные
                failed.append(f"{admission_id}: {type(exc).__name__}: {str(exc)[:120]}")
            if number % 50 == 0:
                print(f"прочитано {number} из {len(todo)}")
        browser.close()

    forms = Counter(details["study_form"] for details in parsed.values())
    locations = Counter(details["location"] for details in parsed.values())
    loads = Counter(
        ("платно" if entry["paid"] else "бесплатно") + " / " + entry["load"]
        for details in parsed.values()
        for entry in details["funding"]
    )
    priced = sum(1 for details in parsed.values() if any(entry["prices"] for entry in details["funding"]))
    print(f"разобрано: {len(parsed)} | страница удалена в SAIS: {len(gone)} | не прочитано: {len(failed)}")
    print("форма обучения:", forms.most_common())
    print("место учёбы:", locations.most_common(15))
    print("нагрузка и финансирование:", loads.most_common())
    print(f"с ценой: {priced} | без финансирования на странице: {sum(1 for d in parsed.values() if not d['funding'])}")
    print(
        f"с условиями конкурса: {sum(1 for d in parsed.values() if d['criteria_text'])} | "
        f"со ссылкой на страницу вуза: {sum(1 for d in parsed.values() if d['info_url'])}"
    )
    for line in failed[:10]:
        print("  не прочитано —", line)
    if limit:
        for admission_id, details in list(parsed.items())[:limit]:
            print(" ", admission_id, details)

    # Если не прочиталась заметная часть страниц, дело не в отдельных
    # конкурсах, а в сайте или в его вёрстке — ничего не записываем.
    if todo and len(failed) > max(5, len(todo) * 0.2):
        print("\nНе прочитано больше пятой части страниц — похоже, SAIS недоступен или изменил вёрстку. В базу ничего не записано.")
        sys.exit(2)
    if not apply:
        print("\nзаписи не было (добавьте --apply)")
        return

    for admission_id, details in parsed.items():
        execute(
            client.table("ee_admission")
            .update({**details, "details_fetched_at": now})
            .eq("admission_id", admission_id)
        )
    # Удалённая страница: условия пустые, но отметка о чтении стоит — чтобы
    # не запрашивать её снова при каждом запуске.
    empty = {
        "title": None,
        "study_form": None,
        "location": None,
        "starts_on": None,
        "funding": None,
        "criteria_text": None,
        "info_url": None,
    }
    for admission_id in gone:
        execute(
            client.table("ee_admission")
            .update({**empty, "details_fetched_at": now})
            .eq("admission_id", admission_id)
        )
    print(f"записано конкурсов: {len(parsed)} | отмечено удалённых страниц: {len(gone)}")
    print(polite.report_and_reset())
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
