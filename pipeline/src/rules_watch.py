"""Кто из вузов уже выложил правила приёма на следующий учебный год.

До 30 ноября вузы публикуют требования и сроки на следующий год (CLAUDE.md,
«Правила приёма изменились»), и в декабре формулы, требования и сроки
переразбираются (план, Д2). Раньше «вышли ли новые правила» узнавали обходом
сайтов руками. Скрипт открывает страницу, где вуз выкладывает правила, и
ищет на ней — в тексте, ссылках и именах файлов — год приёма: прошлый
(«2026./2027.») и следующий («2027./2028.», «2027-2028», «…_27_28.pdf»).

Отчёт по каждому вузу: новый год найден (и где), только прошлый — правил
ещё нет, ни того ни другого — адрес устарел или страница не читается,
проверить руками. Найденный год — подсказка, а не факт: на странице может
быть, например, объявление о дне открытых дверей. Разбор самих правил —
как и раньше, по документу (правило 5 CLAUDE.md).

Страницы открываются через Playwright с polite.install(): часть сайтов
(РТУ, LBTU, JK) строит содержимое скриптом. Тот же User-Agent, паузы и
robots.txt, что у сборщиков; в базу ничего не пишется.

Нет в списке: Turība, TSI и LMA (их правила мы не разбираем), эстонские
вузы (TalTech — решение сената на oigusaktid.taltech.ee, ТÜ — страницы
программ; см. docs/PLAN-ESTONIA.md), Литва (календарь LAMA BPO).

  python src/rules_watch.py --selftest
  python src/rules_watch.py                # следующий учебный год по сегодняшней дате
  python src/rules_watch.py --year 2027    # приём 2027./2028.
"""

from __future__ import annotations

import re
import sys
from datetime import date

# вуз -> страница, где он выкладывает правила приёма в бакалавриат и колледж
# (адреса проверены 2026-10-25: на каждой стоит год 2026./2027.).
# У ViA страница правил лежит под годом («/uznemsana-2026/…») — поэтому главная.
PAGES = {
    "lu": "https://www.lu.lv/gribustudet/normativie-dokumenti/",
    "rtu": "https://www.rtu.lv/lv/studijas/uznemsana/uznemsanas-noteikumi/uznemsanas-noteikumi-pamatstudijas",
    "rsu": "https://www.rsu.lv/studiju-iespejas/uznemsana-pamatstudiju-programmas",
    "lbtu": "https://www.lbtu.lv/lv/pamatstudijas",
    "du": "https://du.lv/gribu-studet/uznemsana/",
    "venta": "https://www.venta.lv/nac-studet/studentu-uznemsanas-noteikumi",
    "juridiska-koledza": "https://jk.lv/uznemsana/uznemsana/uznemsanas-noteikumi/",
    "psmk": "https://psk.lu.lv/uznemsanas-noteikumi",
    "rnu": "https://rnu.lv/uznemsana/pieteiksanas-kartiba/",
    "bsa": "https://bsa.edu.lv/index.php/lv/uznem-sana/uznemsanas-kartiba.html",
    "via": "https://va.lv/",
    "riseba": "https://riseba.lv/nac-studet/uznemsanas-noteikumi/",
    "bvk": "https://www.bvk.lv/uznemsana/",
    "rbk": "https://www.rck.lv/augstaka-izglitiba/uznemsana/",
    "r1mk": "https://www.rmk1.lv/lv/studiju-iespejas/ieraksts/pirma-limena-profesionalas-augstakas-izglitibas-uznemsanas-noteikumi/",
    "vpk": "https://www.policijas.koledza.gov.lv/lv/uznemsanas-noteikumi-0",
    "jvlma": "https://www.jvlma.lv/studijas/uznemsana",
}


def year_pattern(start: int) -> re.Pattern[str]:
    """Учебный год start/start+1 в тех видах, что встречаются у вузов:
    «2027./2028.», «2027/2028», «2027-2028», «2027_2028», «2027./28.» и
    в именах файлов «…_27_28.pdf» / «27-28». Одиночный год не считается:
    «до 1 июля 2027 года» есть и в правилах прошлого года."""
    a, b = str(start), str(start + 1)
    full = rf"{a}\.?\s*[/_–-]\s*(?:{b}|{b[2:]})(?!\d)"
    short = rf"(?<!\d){a[2:]}[_-]{b[2:]}(?!\d)"
    return re.compile(rf"{full}|{short}")


def default_year(today: date) -> int:
    """Год приёма, к которому готовимся: с сентября — следующий."""
    return today.year + 1 if today.month >= 9 else today.year


def find(pattern: re.Pattern[str], text: str, links: list[tuple[str, str]]) -> list[str]:
    """Где на странице встретился год: ссылки (текст или адрес) — их адрес,
    иначе кусок текста вокруг совпадения."""
    hits = [href for label, href in links if pattern.search(label) or pattern.search(href)]
    if not hits:
        match = pattern.search(text)
        if match:
            hits = ["«…" + text[max(0, match.start() - 50) : match.end() + 30].strip() + "…»"]
    return list(dict.fromkeys(hits))[:3]


def _selftest() -> None:
    next_year = year_pattern(2027)
    for sample in ("2027./2028. akadēmiskajā gadā", "2027/2028", "2027-2028", "uzn_prasibas_pamat_27_28.pdf",
                   "2027./28. gads", "Uznemsanas_noteikumi_2027_2028.pdf", "2027 – 2028"):
        assert next_year.search(sample), sample
    for sample in ("2026./2027.", "līdz 2027. gada 1. jūlijam", "uzn_prasibas_pamat_26_27.pdf", "2027./2029.",
                   "tel. 127-2810", "2027-20281"):
        assert not next_year.search(sample), sample
    assert year_pattern(2026).search("2026./2027. studiju gadā")
    assert default_year(date(2026, 10, 25)) == 2027 and default_year(date(2027, 3, 1)) == 2027
    links = [("Uzņemšanas noteikumi 2027./2028.", "/docs/a.pdf"), ("Noteikumi", "/docs/uzn_27_28.pdf"), ("Sākums", "/")]
    assert find(next_year, "", links) == ["/docs/a.pdf", "/docs/uzn_27_28.pdf"]
    assert find(next_year, "Uzņemšana 2027./2028. gadā sāksies martā", [])[0].startswith("«…Uzņemšana 2027./2028.")
    assert find(next_year, "nekas", links[2:]) == []
    print("selftest: OK")


def main(year: int) -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright

    import polite

    load_dotenv()
    polite.install()
    current, upcoming = year_pattern(year - 1), year_pattern(year)
    published, waiting, unclear = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_default_timeout(30000)
        for slug, url in PAGES.items():
            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)  # страницы, которые достраивает скрипт
                text = re.sub(r"\s+", " ", page.locator("body").inner_text())
                links = page.eval_on_selector_all("a[href]", "els => els.map(a => [a.innerText || '', a.href])")
            except Exception as exc:  # noqa: BLE001 — один сайт не мешает остальным
                unclear.append(f"{slug}: не открылась ({type(exc).__name__}) — {url}")
                continue
            new = find(upcoming, text, links)
            if new:
                published.append(f"{slug}: {', '.join(new)}")
            elif find(current, text, links):
                waiting.append(slug)
            else:
                unclear.append(f"{slug}: нет ни {year - 1}/{year}, ни {year}/{year + 1} — адрес устарел? {url}")
        browser.close()

    print(f"Правила приёма {year}./{year + 1}. — проверено {len(PAGES)} страниц\n")
    print(f"Есть упоминание нового года ({len(published)}) — открыть и проверить, правила ли это:")
    for line in published:
        print(f"  {line}")
    print(f"\nПока только {year - 1}./{year}. ({len(waiting)}): {', '.join(waiting) or '—'}")
    if unclear:
        print(f"\nПроверить руками ({len(unclear)}):")
        for line in unclear:
            print(f"  {line}")
    print("\n" + polite.report_and_reset())


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
    else:
        main(int(args[args.index("--year") + 1]) if "--year" in args else default_year(date.today()))
