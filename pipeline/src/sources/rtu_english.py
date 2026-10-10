"""RTU — программы на английском языке, из английского реестра
(rtu.lv/en/studies/all-study-programmes).

Зачем отдельный источник. На латышской карточке программы язык часто
указан как «Latviešu, Angļu» (78 карточек из 150, подсчёт 2026-10-10), но
это не значит, что на программу набирают на английском: в английском
реестре, по которому поступают, программ 55 (бакалавриат 13, магистратура
22, докторантура 20), а бакалавриата по химии, например, там нет вовсе.
Две официальные страницы расходятся; владелец решил (2026-10-10) брать
английские программы из реестра для поступающих. Латышский реестр
(rtu_catalog.py) даёт латышские записи.

Реестр устроен как латышский: одна страница, таблицы в сворачиваемых
панелях. В строке — название, длительность, цена в год для граждан ЕС и
для остальных, время набора. Язык, форма и город — на карточке программы.

Что откуда берётся:
- название (name_en), уровень, длительность, цена — из строки реестра.
  Цена — колонка «EU countries» (граждане ЕС, ЕАСТ и стран-кандидатов):
  она же подписана на сайте «Maksa gadā (ES/EEZ)». Цена для остальных стран
  не сохраняется — поля под неё в каталоге нет;
- язык, форма обучения, город — с карточки. Язык не подставляется: если на
  карточке не «English», запись остаётся без языка, и main.py новую такую
  программу не запишет;
- вид финансирования пустой: реестр называет цену, но о бюджетных местах
  не говорит ничего — ни что они есть, ни что их нет.

Слаг — название из адреса плюс номер программы в реестре
(«civil-engineering-188»): названия повторяются на разных уровнях
(«Civil Engineering» — и бакалавриат, и докторантура), номер их различает.
Номер бывает отрицательным: докторантура «Educational Sciences» в Резекне —
id=250, в Лиепае — id=-250. Минус в слаге пишется буквой «n»
(«educational-sciences-n250»), иначе две программы получили бы один слаг.

Латышский реестр помечает девять программ как только-английские
(rtu_catalog.py пишет их по-прежнему, со старыми слагами — на двух висят
подтверждённые формулы). Часть из них есть и здесь под английским
названием: такие программы окажутся в каталоге дважды. Общего ключа у
реестров нет (там код «KBM», здесь номер «195»), сопоставлять по названию
на разных языках сборщик не берётся — см. docs/checks/AUDIT-2026-10-04.md.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft
# Запись о вузе — та же, что пишет rtu_catalog: каждый сбор перезаписывает
# строку вуза, и со своей копией адрес источника у РТУ менялся бы от того,
# какой из двух сборщиков отработал последним.
from sources.rtu_catalog import UNIVERSITY, _facts

REGISTRY_URL = "https://www.rtu.lv/en/studies/all-study-programmes"

# Строка-заголовок уровня — единственная ячейка без ссылки; строка программы —
# со ссылкой и пятью ячейками.
_DISCOVER_JS = """
() => {
  const rows = [];
  for (const panel of document.querySelectorAll('.collapse-panel')) {
    let level = '';
    for (const tr of panel.querySelectorAll('table tr')) {
      const link = tr.querySelector('a');
      const cells = Array.from(tr.querySelectorAll('td')).map(c => c.textContent.replace(/\\s+/g, ' ').trim());
      if (!link) { if (cells.length === 1) level = cells[0]; continue; }
      rows.push({
        href: link.getAttribute('href'), level,
        name: cells[0] || '', duration: cells[1] || '', price_eu: cells[2] || '',
      });
    }
  }
  return rows;
}
"""

LEVELS = (("short-cycle", "college"), ("first-cycle", "bachelor"), ("second-cycle", "master"), ("third-cycle", "doctoral"))
CITIES = {"riga": "riga", "liepaja": "liepaja", "rezekne": "rezekne", "daugavpils": "daugavpils", "ventspils": "ventspils"}
_PLAIN = str.maketrans("āēīūĀĒĪŪ", "aeiuAEIU")


def map_level(text: str) -> str | None:
    lowered = text.lower()
    return next((code for word, code in LEVELS if word in lowered), None)


def parse_years(text: str) -> float | None:
    """«3 years» → 3.0, «4.5 years» → 4.5. Диапазон («1.5 - 2.5 years») —
    пусто: одним числом его не выразить."""
    numbers = re.findall(r"\d+(?:[.,]\d+)?", text)
    return float(numbers[0].replace(",", ".")) if len(numbers) == 1 else None


def parse_price(text: str) -> float | None:
    """«€ 4 030» → 4030.0; прочерк или пусто — пусто."""
    digits = re.sub(r"\D", "", text)
    return float(digits) if digits else None


def slug_from(href: str) -> str | None:
    """«…/open/civil-engineering?id=188» → «civil-engineering-188»."""
    match = re.search(r"/open/([a-z0-9-]+)\?(?:.*&)?id=(-?)(\d+)", href)
    if not match:
        return None
    return f"{match.group(1)}-{'n' if match.group(2) else ''}{match.group(3)}"


def cities_from(venue: str) -> list[str]:
    """Города с карточки («Riga», «Liepāja»). Незнакомое название пропускается."""
    names = [part.strip().translate(_PLAIN).lower() for part in re.split(r"[,/;]", venue)]
    return [CITIES[name] for name in names if name in CITIES]


def study_mode_from(form: str) -> str | None:
    lowered = form.lower()
    if "part-time" in lowered or "part time" in lowered:
        return "part_time"
    if "full-time" in lowered or "full time" in lowered:
        return "full_time"
    return None


def _detail(page: Page, url: str) -> dict[str, str]:
    """Факты с карточки программы. Один повтор при сбое, как в rtu_catalog;
    не вышло — пусто, и программа в этот раз останется без языка."""
    for attempt in (1, 2):
        try:
            page.goto(url, wait_until="domcontentloaded")
            return _facts(page)
        except Exception as exc:  # noqa: BLE001
            if attempt == 2:
                print(f"rtu_english: не прочиталась {url}: {type(exc).__name__}")
    return {}


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(5000)
        page.goto(REGISTRY_URL, wait_until="domcontentloaded")
        rows = page.evaluate(_DISCOVER_JS)

        for row in rows:
            url = urljoin(REGISTRY_URL, row["href"])
            slug = slug_from(row["href"])
            level = map_level(row["level"])
            if slug is None or level is None:
                # Уровень и адрес не угадываем: строка пропускается, и это видно в журнале.
                print(f"rtu_english: пропущена строка «{row['name']}» — уровень «{row['level']}», адрес {row['href']}")
                continue

            facts = _detail(page, url)
            language = "en" if "english" in facts.get("language", "").lower() else None
            if facts and language is None:
                print(f"rtu_english: язык не «English» на {url}: «{facts.get('language', '')}»")
            mode = study_mode_from(facts.get("study form", ""))
            cities = cities_from(facts.get("venue", ""))
            if facts and (mode is None or not cities):
                print(
                    f"rtu_english: на {url} не распознаны форма «{facts.get('study form', '')}» "
                    f"или город «{facts.get('venue', '')}»"
                )

            # Программа в нескольких городах — по записи на город, как в rtu_catalog.
            for city in cities or [None]:
                programmes.append(
                    ProgrammeDraft(
                        slug=f"{slug}-{city}" if len(cities) > 1 else slug,
                        name_en=row["name"],
                        degree_level=level,
                        language_of_instruction=language,
                        # Форма обучения — поле обязательное. В реестре для
                        # поступающих из-за рубежа все программы очные; если
                        # карточка не прочиталась, пишем так же и сообщаем выше.
                        study_mode=mode or "full_time",
                        city=city,
                        tuition_fee_amount=parse_price(row["price_eu"]),
                        duration_years=parse_years(row["duration"]),
                        source_url=url,
                    )
                )

        browser.close()

    return UNIVERSITY, programmes


def selftest() -> None:
    assert map_level("First-Cycle Higher Education (Academic Bachelor) Studies:") == "bachelor"
    assert map_level("First-Cycle Higher Education (Professional Bachelor) Studies:") == "bachelor"
    assert map_level("Second-Cycle Higher Education (Professional Master) Studies:") == "master"
    assert map_level("Third-Cycle Higher Education (Doctoral) Studies:") == "doctoral"
    assert map_level("Something new") is None
    assert parse_years("3 years") == 3.0 and parse_years("4.5 years") == 4.5 and parse_years("4,3 years") == 4.3
    assert parse_years("1.5 - 2.5 years") is None and parse_years("") is None
    assert parse_price("€ 4 030") == 4030.0 and parse_price("€ 10 770") == 10770.0
    assert parse_price("-") is None and parse_price("") is None
    assert slug_from("/en/studies/all-study-programmes/open/civil-engineering?id=188") == "civil-engineering-188"
    assert slug_from("/en/studies/all-study-programmes/open/x?foo=1&id=7") == "x-7"
    assert slug_from("/en/studies/all-study-programmes/open/educational-sciences?id=-250") == "educational-sciences-n250"
    assert slug_from("/en/studies/all-study-programmes") is None
    assert cities_from("Riga") == ["riga"] and cities_from("Liepāja") == ["liepaja"]
    assert cities_from("Riga, Rēzekne") == ["riga", "rezekne"] and cities_from("Mars") == []
    assert study_mode_from("Full-time studies") == "full_time" and study_mode_from("Part-time studies") == "part_time"
    assert study_mode_from("") is None
    print("самотест пройден")
