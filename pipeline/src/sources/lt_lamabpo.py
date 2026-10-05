"""Литва: каталог первой ступени (бакалавриат, колледжи, цельные программы).

Два открытых источника, оба государственные или официальные:

1. Файл программ официального калькулятора LAMA BPO (общий приём, 28
   учреждений). Одна запись файла — одна строка общего приёма: программа в
   конкретном городе, форме и расписании. Отсюда берутся: учреждение,
   название, город, форма, ссылка на страницу программы у вуза и на карточку
   в государственном реестре.
2. Государственный реестр AIKOS. Карточка программы даёт уровень, язык
   обучения, степень, длительность и описание; карточка учреждения —
   государственное оно или нет, английское название, город, сайт.

Почему не сайты вузов: 28 сайтов на разных движках против двух источников в
одном формате — то же решение, что с NIID для латвийских колледжей.

Строка каталога = программа вуза в одном городе, на одном языке, в одной
форме. Записи файла, которые различаются только расписанием (дневное /
сессиями) или специализацией, сливаются в одну строку: в каталоге это одна
программа.

Чего здесь нет и почему:
- Магистратуры и докторантуры: в общем приёме LAMA BPO их нет.
- Цены: её нет ни в одном из двух источников (docs/checks/LT-PHASE0-SOURCES.md).
- Бюджетных мест: в Литве они делятся по группам направлений, не по
  программам, поэтому funding_type остаётся пустым, а не угадывается.

Литовские факты показываются без подтверждения человеком, с пометкой
«извлечено автоматически» — решение владельца 2026-10-05, только для Литвы.

Запуск:
  python src/sources/lt_lamabpo.py --selftest   # разбор на встроенных примерах, без сети
  python src/sources/lt_lamabpo.py              # собрать и напечатать сводку, без записи в базу
  python src/main.py lt_lamabpo                 # собрать и записать (источник запускается только по имени)

Сбор открывает около 700 страниц реестра с паузами (polite.py) и идёт
около часа. SCRAPE_CACHE=1 сохраняет страницы на сутки — повторный запуск
в тот же день занимает минуты.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

PROGRAMS_URL = "https://lamabpo.lt/wp-content/plugins/simple-score-calculator/programs_lt.js"

# Правило владельца (2026-10-05): если сокращение литовского учреждения
# совпало с уже занятым кодом, к коду добавляется страна. В адресе это
# суффикс "-lt" (скобки в адресе невозможны), в подписи — "(LT)".
# Коды латвийских учреждений на 2026-10-05; занятый код не переиспользуется.
TAKEN_SLUGS = {
    "alberta", "bsa", "bvk", "dmk", "du", "eka", "ekra", "gfk", "hotel-school", "juridiska-koledza", "jvlma",
    "lbtu", "ljk", "lka", "lma", "lnaa", "lu", "lutera", "malnavas-koledza", "novikonta", "psmk", "r1mk", "rai",
    "rarzi", "rbk", "rgsl", "riseba", "rmenk", "rmk", "rnu", "rsu", "rti", "rtk", "rtu", "siva", "skmk",
    "sse-riga", "tsi", "turiba", "ucak", "venta", "via", "vpk", "vrsk",
}

LANGUAGES = {"lietuvių": "lt", "anglų": "en", "rusų": "ru", "lenkų": "pl", "vokiečių": "de", "prancūzų": "fr"}

_PAIR = re.compile(r"(\w+)\s*:\s*'((?:[^'\\]|\\.)*)'")


def slugify(text: str) -> str:
    plain = unicodedata.normalize("NFD", text)
    plain = "".join(ch for ch in plain if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")


def university_slug(code: str) -> str:
    slug = slugify(code)
    return f"{slug}-lt" if slug in TAKEN_SLUGS else slug


def parse_programs(js_text: str) -> list[dict[str, str]]:
    """Записи из `const programs = [{a:'…',b:'…'}, …]` — литерал JS, не JSON:
    ключи без кавычек, строки в одинарных кавычках."""
    start = js_text.index("[", js_text.index("const programs"))
    entries: list[dict[str, str]] = []
    buffer: list[str] = []
    in_string = False
    index = start + 1
    while index < len(js_text):
        ch = js_text[index]
        if in_string:
            buffer.append(ch)
            if ch == "\\":
                index += 1
                buffer.append(js_text[index])
            elif ch == "'":
                in_string = False
        elif ch == "'":
            in_string = True
            buffer.append(ch)
        elif ch == "{":
            buffer = []
        elif ch == "}":
            entries.append({m.group(1): m.group(2).replace("\\'", "'").strip() for m in _PAIR.finditer("".join(buffer))})
        elif ch == "]":
            break
        else:
            buffer.append(ch)
        index += 1
    return entries


def study_mode(entry: dict[str, str]) -> str:
    if entry.get("n") == "Nuotolinė":
        return "distance"
    return "part_time" if entry.get("o", "").startswith("Ištęstinė") else "full_time"


_LANGUAGE_WORD = r"(angl[ųu]|lietuvi[ųu])"
# "Anglų k. …", "lietuvių ir anglų k." — пометка в начале примечания
_NOTE_HEAD = re.compile(_LANGUAGE_WORD + r"(?:\s+ir\s+" + _LANGUAGE_WORD + r")?\s+k\.")
# "Studijos vykdomos anglų kalba" — в любом месте примечания
_NOTE_TAUGHT = re.compile(r"vykdom\w*\s+" + _LANGUAGE_WORD + r"\s+kalba")


def note_language(note: str) -> str | None:
    """Язык, если запись общего приёма называет его сама. Узнаются только
    две формы пометки (см. выше): просто слово «anglų» в тексте — ещё не
    язык обучения, так называются и предметы."""
    lowered = note.lower()
    words: set[str] = set()
    head = _NOTE_HEAD.search(lowered[:60])
    if head:
        words.update(word for word in head.groups() if word)
    words.update(_NOTE_TAUGHT.findall(lowered))
    found = {"en" if word.startswith("angl") else "lt" for word in words}
    return found.pop() if len(found) == 1 else None


@dataclass
class Card:
    """Что прочитано с карточки программы в реестре."""

    level: str | None = None
    languages: list[str] = field(default_factory=list)
    degree: str | None = None
    years: dict[str, float] = field(default_factory=dict)  # 'full_time' / 'part_time' -> лет
    description: str | None = None
    institution_link: str | None = None


def _after(lines: list[str], label: str) -> str | None:
    for index, line in enumerate(lines):
        if line == label:
            for value in lines[index + 1:]:
                if value:
                    return value
    return None


def parse_card(lines: list[str]) -> Card:
    card = Card()
    kind = _after(lines, "Studijų rūšis") or ""
    # Цельные программы реестр отмечает в поле «ступень» ("Vientisosios
    # studijos"), а не в поле «тип программы» — там у них то же "Pakopinės".
    cycle = _after(lines, "Studijų pakopa") or ""
    if "Vientis" in cycle:
        card.level = "integrated"
    elif "Kolegin" in kind:
        card.level = "college"
    elif "Universitetin" in kind:
        card.level = "bachelor"

    raw_languages = _after(lines, "Programos vykdymo kalba") or ""
    for name in (part.strip().lower() for part in raw_languages.split(",")):
        if name in LANGUAGES and LANGUAGES[name] not in card.languages:
            card.languages.append(LANGUAGES[name])

    card.degree = _after(lines, "Suteikiamas kvalifikacinis laipsnis ir (arba) kvalifikacija")

    # "Nuolatinė, 4, Metais" / "Ištęstinė, 6, Metais"
    for line in lines:
        match = re.fullmatch(r"(Nuolatinė|Ištęstinė),\s*([\d.,]+),\s*Metais", line)
        if match:
            mode = "full_time" if match.group(1) == "Nuolatinė" else "part_time"
            card.years[mode] = float(match.group(2).replace(",", "."))

    card.description = _description(lines)
    return card


_GOAL_LABEL = re.compile(r"Studijų programos tikslas\s*\(-ai\)\s*:\s*")
# Подписи следующих частей карточки: если реестр отдал всё одной строкой,
# описание обрывается на первой из них.
_NEXT_PARTS = ("Studijų rezultatai:", "Sandara:", "Mokymo ir mokymosi veiklos:", "Studijų rezultatų vertinimo būdai:")
MAX_DESCRIPTION = 1500


def _description(lines: list[str]) -> str | None:
    """Цель программы из раздела «Aprašymo santrauka». Раздел свободный:
    цель стоит то после подписи на той же строке, то на следующей, то без
    подписи сразу под заголовком раздела."""
    try:
        start = lines.index("Aprašymo santrauka")
    except ValueError:
        return None
    section = [line for line in lines[start + 1:] if line]
    text = None
    for index, line in enumerate(section[:6]):
        match = _GOAL_LABEL.search(line)
        if match:
            text = line[match.end():] or (section[index + 1] if index + 1 < len(section) else "")
            break
    if text is None and section:
        first = section[0].removeprefix("Bendras apibūdinimas:").strip()
        text = first if not first.endswith(":") else ""
    for label in _NEXT_PARTS:
        text = text.split(label)[0]
    text = text.strip()
    if len(text) > MAX_DESCRIPTION:
        cut = text[:MAX_DESCRIPTION]
        text = cut[: cut.rfind(". ") + 1] or cut
    # Обрывок вместо описания: цель в реестре иногда разбита на пункты, и в
    # первой строке остаётся «Parengti teisininkus, kurie». Законченный текст
    # кончается точкой и не начинается с тире; иначе описания лучше не будет.
    if len(text) <= 40 or text.startswith(("-", "–", "•")) or not text.endswith((".", "!", "?")):
        return None
    return text


def row_language(entries: list[dict[str, str]], card: Card) -> str | None:
    """Язык строки каталога: сначала то, что сказано в самой записи приёма,
    иначе — язык из реестра. Если реестр называет несколько языков и среди
    них литовский, строка считается литовской: отдельную запись для
    иностранного языка вузы в общем приёме помечают сами."""
    noted = {note_language(entry.get("y", "")) for entry in entries} - {None}
    if len(noted) == 1:
        return noted.pop()
    if "lt" in card.languages:
        return "lt"
    return card.languages[0] if card.languages else None


@dataclass
class Institution:
    kind: str | None = None  # 'public' | 'private'
    name_en: str | None = None
    website: str | None = None
    source_url: str | None = None


def parse_institution(lines: list[str]) -> Institution:
    institution = Institution()
    ownership = _after(lines, "Priklausomybė") or ""
    if ownership.startswith("Valstybin"):
        institution.kind = "public"
    elif ownership.startswith("Nevalstybin"):
        institution.kind = "private"
    institution.name_en = clean_english_name(_after(lines, "Pavadinimas anglų kalba"))
    contacts = _after(lines, "Telefonai, faksas, internetinės svetainės ir elektroninio pašto adresai") or ""
    site = re.search(r"https?://[^\s,]+|www\.[^\s,]+", contacts)
    if site:
        institution.website = site.group(0) if site.group(0).startswith("http") else f"http://{site.group(0)}"
    return institution


def clean_english_name(raw: str | None) -> str | None:
    """Английское название из реестра без правовой формы. У части колледжей
    там стоит литовское название с припиской или одна приписка — тогда
    английского названия нет вовсе: лучше показать литовское, чем
    «Higher Education Institution»."""
    if not raw:
        return None
    name = raw.replace('"', "").strip()
    if " / " in name or name.lower() == "higher education institution":
        return None
    name = re.sub(r"^public institution\s+", "", name, flags=re.IGNORECASE)
    name = re.sub(r",\s*(public institution|jsc)$", "", name, flags=re.IGNORECASE)
    return name.strip() or None


def group_rows(entries: list[dict[str, str]], cards: dict[str, Card]) -> dict[tuple, list[dict[str, str]]]:
    """Записи приёма -> строки каталога: вуз, название, направление, город,
    язык, форма."""
    rows: dict[tuple, list[dict[str, str]]] = defaultdict(list)
    for entry in entries:
        card = cards.get(entry["j"], Card())
        language = note_language(entry.get("y", "")) or row_language([entry], card)
        rows[(entry["f"], entry["k"], entry["c"], entry["m"], language, study_mode(entry))].append(entry)
    return rows


def assign_slugs(keys: list[tuple]) -> dict[tuple, str]:
    """Код программы внутри вуза: название, а различитель (город, язык,
    форма, направление) добавляется только там, где без него не обойтись.
    Так адрес не меняется, когда у вуза появляется новый вариант другой
    программы."""
    result: dict[tuple, str] = {}
    by_base: dict[tuple[str, str], list[tuple]] = defaultdict(list)
    for key in keys:
        by_base[(key[0], slugify(key[1]))].append(key)
    for (_, base), group in by_base.items():
        parts = {key: [base] for key in group}
        # порядок различителей: город, язык, форма, код направления
        for position, render in ((3, slugify), (4, lambda v: v or "x"), (5, lambda v: v.replace("_", "-")), (2, slugify)):
            if len({tuple(p) for p in parts.values()}) == len(group):
                break
            if len({key[position] for key in group}) > 1:
                for key in group:
                    parts[key].append(render(key[position]))
        slugs = {key: "-".join(p) for key, p in parts.items()}
        if len(set(slugs.values())) != len(group):
            raise ValueError(f"не удалось развести программы с одним названием: {sorted(slugs.values())}")
        result.update(slugs)
    return result


_LINES_JS = "() => document.body.innerText.split('\\n').map(line => line.trim())"


def _lines(page: Page, url: str, marker: str) -> list[str]:
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    try:
        page.get_by_text(marker, exact=True).first.wait_for(timeout=15000)
    except Exception:  # noqa: BLE001 — карточка без этого поля: разбираем, что есть
        pass
    return page.evaluate(_LINES_JS)


def _institution(page: Page, card_url: str, name: str) -> Institution:
    """С карточки программы — на список учреждений, которые её ведут, оттуда
    на карточку учреждения. Прямого адреса по названию у реестра нет."""
    page.goto(card_url, wait_until="domcontentloaded", timeout=45000)
    link = page.locator("a", has_text="Institucijos, teikiančios šią programą").first
    link.wait_for(timeout=15000)
    page.goto(link.get_attribute("href"), wait_until="domcontentloaded", timeout=45000)
    anchors = page.locator("a[href*='o=INST']")
    anchors.first.wait_for(timeout=15000)
    hrefs = {anchors.nth(i).inner_text().strip(): anchors.nth(i).get_attribute("href") for i in range(anchors.count())}
    href = hrefs.get(name) or next(iter(hrefs.values()))
    institution = parse_institution(_lines(page, href, "Priklausomybė"))
    institution.source_url = href
    return institution


def scrape_all() -> list[tuple[UniversityDraft, list[ProgrammeDraft]]]:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        response = page.goto(PROGRAMS_URL, timeout=45000)
        entries = parse_programs(response.text())

        cards: dict[str, Card] = {}
        for number, url in enumerate(sorted({entry["j"] for entry in entries}), start=1):
            cards[url] = parse_card(_lines(page, url, "Valstybinis kodas"))
            if number % 50 == 0:
                print(f"lt_lamabpo: карточек программ прочитано {number}")

        institutions: dict[str, Institution] = {}
        for entry in entries:
            if entry["f"] not in institutions:
                try:
                    institutions[entry["f"]] = _institution(page, entry["j"], entry["g"])
                except Exception as exc:  # noqa: BLE001 — без карточки учреждения оно не записывается (см. build)
                    print(f"lt_lamabpo: карточка учреждения {entry['f']} не прочитана — {type(exc).__name__}: {exc}")
                    institutions[entry["f"]] = Institution()
        browser.close()

    return build(entries, cards, institutions)


def build(
    entries: list[dict[str, str]], cards: dict[str, Card], institutions: dict[str, Institution]
) -> list[tuple[UniversityDraft, list[ProgrammeDraft]]]:
    now = datetime.now(timezone.utc).isoformat()
    rows = group_rows(entries, cards)
    slugs = assign_slugs(list(rows))

    by_institution: dict[str, list[tuple]] = defaultdict(list)
    for key in rows:
        by_institution[key[0]].append(key)

    result = []
    for code, keys in by_institution.items():
        institution = institutions.get(code, Institution())
        first = rows[keys[0]][0]
        if institution.kind is None:
            # Государственное учреждение или нет — факт, который читается
            # только из реестра. Без него учреждение пропускается целиком,
            # а не записывается с угаданным значением.
            print(f"lt_lamabpo: {code} пропущено — в реестре не найдено, государственное оно или нет")
            continue
        cities = Counter(key[3] for key in keys for _ in rows[key])
        university = UniversityDraft(
            slug=university_slug(code),
            country="LT",
            name_lt=first["g"],
            name_en=institution.name_en,
            kind=institution.kind,
            city=slugify(cities.most_common(1)[0][0]),
            website_url=institution.website,
            source_url=institution.source_url or first["j"],
        )
        programmes = []
        for key in keys:
            _, name, _, city, language, mode = key
            entry = rows[key][0]
            card = cards.get(entry["j"], Card())
            if card.level is None or language is None:
                # уровень и язык обязательны в каталоге; строка без них —
                # карточка реестра не прочиталась, а не «программа без языка»
                print(f"lt_lamabpo: {code} / {name} пропущена — нет уровня или языка в реестре ({entry['j']})")
                continue
            programmes.append(
                ProgrammeDraft(
                    slug=slugs[key],
                    name_lt=name,
                    degree_level=card.level,
                    language_of_instruction=language,
                    study_mode=mode,
                    city=slugify(city),
                    duration_years=card.years.get("part_time" if mode == "part_time" else "full_time"),
                    degree_awarded_lt=card.degree,
                    description_lt=card.description,
                    details_source_url=entry["j"],
                    details_extracted_at=now,
                    source_url=entry["j"],
                )
            )
        result.append((university, programmes))
    return result


def _selftest() -> None:
    js = (
        "const programs = [{a:'E',b:'Inžinerijos mokslai',c:'E14',d:'Aeronautikos inžinerija',e:'177',f:'KTU',"
        "g:'Kauno technologijos universitetas',h:'https://x/',j:'https://aikos/1',k:'Aviacijos inžinerija',"
        "y:'LIETUVIŲ K. Specializacijos: a, b {c}.',l:'2',m:'Kaunas',n:'Dieninė',o:'Nuolatinė (NL)',p:'53',r:'Inžinerija'},"
        "{a:'E',b:'x',c:'E14',d:'x',e:'178',f:'KTU',g:'Kauno technologijos universitetas',h:'',j:'https://aikos/1',"
        "k:'Aviacijos inžinerija',y:'Anglų k. It\\'s taught in English.',l:'2',m:'Kaunas',n:'Dieninė',o:'Nuolatinė (NL)',p:'53',r:'x'},"
        "{a:'S',b:'x',c:'S01',d:'x',e:'9',f:'LKA',g:'Generolo Jono Žemaičio Lietuvos karo akademija',h:'',j:'https://aikos/2',"
        "k:'Nacionalinis saugumas',y:'',l:'1',m:'Vilnius',n:'Sesijinė',o:'Ištęstinė (I)',p:'12',r:'x'}];\n"
        "const other = [];"
    )
    entries = parse_programs(js)
    assert len(entries) == 3, len(entries)
    assert entries[0]["k"] == "Aviacijos inžinerija" and entries[0]["y"].endswith("{c}."), entries[0]
    assert entries[1]["y"] == "Anglų k. It's taught in English.", entries[1]["y"]

    assert slugify("Šiaulių valstybinė kolegija") == "siauliu-valstybine-kolegija"
    assert university_slug("KTU") == "ktu"
    assert university_slug("LKA") == "lka-lt", "занятый латвийский код получает суффикс страны"
    assert university_slug("VILNIUS TECH") == "vilnius-tech"

    assert study_mode(entries[0]) == "full_time" and study_mode(entries[2]) == "part_time"
    assert study_mode({"n": "Nuotolinė", "o": "Nuolatinė (NL)"}) == "distance"
    assert note_language(entries[0]["y"]) == "lt" and note_language(entries[1]["y"]) == "en"
    assert note_language("Lėktuvai (lietuvių ir anglų k.).") is None
    assert note_language("Studijuojami dalykai: istorija, anglų kalba ir literatūra.") is None
    assert note_language("Specializacija: Italistika. Studijos vykdomos ANGLŲ kalba.") == "en"
    assert note_language("Studijos vyksta Vilniuje, anglų k., trukmė – 3,5 m.") == "en"
    assert note_language("") is None

    card_lines = [
        "Studijų rūšis", "Universitetinės studijos", "Studijų programos tipas", "Pakopinės studijos",
        "Studijų pakopa", "Pirmosios pakopos studijos", "Programos vykdymo kalba", "anglų, lietuvių",
        "Suteikiamas kvalifikacinis laipsnis ir (arba) kvalifikacija", "Inžinerijos mokslų bakalauras",
        "Studijų apimtis kreditais ir forma (trukmė metais)", "240", "Ištęstinė, 6, Metais", "Nuolatinė, 4, Metais",
        "Aprašymo santrauka", "Bendras apibūdinimas:", "Studijų programos tikslas (-ai):",
        "Suteikti aviacijos inžinerijos žinias, išugdyti gebėjimus surasti ir taikyti naujus sprendimus.",
        "Studijų rezultatai:", "Žinios ir jų taikymas:",
    ]
    card = parse_card(card_lines)
    assert card.level == "bachelor" and card.languages == ["en", "lt"], card
    assert card.degree == "Inžinerijos mokslų bakalauras" and card.years == {"part_time": 6.0, "full_time": 4.0}, card
    assert card.description.startswith("Suteikti aviacijos") and card.description.endswith("sprendimus."), card.description
    assert parse_card(["Studijų rūšis", "Koleginės studijos"]).level == "college"
    integrated = ["Studijų rūšis", "Universitetinės studijos", "Studijų programos tipas", "Pakopinės studijos", "Studijų pakopa", "Vientisosios studijos"]
    assert parse_card(integrated).level == "integrated"
    # всё одной строкой: описание обрывается на следующей части карточки
    inline = "Bendras apibūdinimas: Studijų programos tikslas(-ai): Rengti aukštos kvalifikacijos farmacijos specialistus visai šaliai. Studijų rezultatai: žinios."
    assert _description(["Aprašymo santrauka", inline]) == "Rengti aukštos kvalifikacijos farmacijos specialistus visai šaliai."
    # без подписи: текст сразу под заголовком раздела
    plain = "Būsimieji teisės bakalaurai studijuoja filosofiją, logiką, teisės istoriją ir teisės teoriją."
    assert _description(["Aprašymo santrauka", plain, "Grįžti atgal"]) == plain
    assert _description(["Aprašymo santrauka", "Bendras apibūdinimas:", "Sandara:"]) is None
    assert _description([]) is None
    assert _description(["Aprašymo santrauka", "Studijų programos tikslas (-ai):", "Parengti kvalifikuotus teisininkus, kurie"]) is None
    assert _description(["Aprašymo santrauka", "- programos turinys (pagrindiniai studijų dalykai ir praktika)."]) is None
    long_text = "Sakinys apie programą. " * 100
    assert len(_description(["Aprašymo santrauka", long_text])) <= MAX_DESCRIPTION
    assert clean_english_name("Kauno kolegija / Higher Education Institution") is None
    assert clean_english_name("Higher Education Institution") is None
    assert clean_english_name('"ISM University of Management and Economics", JSC') == "ISM University of Management and Economics"
    assert clean_english_name("Public Institution Vilnius Business College") == "Vilnius Business College"
    assert clean_english_name("European Humanities University, Public Institution") == "European Humanities University"
    assert clean_english_name("Vilnius University") == "Vilnius University"
    without_scheme = parse_institution([
        "Priklausomybė", "Valstybinė",
        "Telefonai, faksas, internetinės svetainės ir elektroninio pašto adresai", "+370 5 2744949, www.vilniustech.lt, a@vilniustech.lt",
    ])
    assert without_scheme.website == "http://www.vilniustech.lt", without_scheme
    assert parse_card([]).level is None

    institution = parse_institution([
        "Pavadinimas anglų kalba", "Kaunas University of Technology", "Priklausomybė", "Valstybinė",
        "Telefonai, faksas, internetinės svetainės ir elektroninio pašto adresai", "+370 37 300000, http://ktu.edu/, ktu@ktu.lt",
    ])
    assert institution.kind == "public" and institution.website == "http://ktu.edu/", institution
    assert parse_institution(["Priklausomybė", "Nevalstybinė"]).kind == "private"
    assert parse_institution([]).kind is None

    cards = {"https://aikos/1": card, "https://aikos/2": Card(level="bachelor", languages=["lt"], years={"part_time": 4.5})}
    rows = group_rows(entries, cards)
    assert len(rows) == 3, list(rows)
    slugs = assign_slugs(list(rows))
    assert sorted(slugs.values()) == ["aviacijos-inzinerija-en", "aviacijos-inzinerija-lt", "nacionalinis-saugumas"], slugs
    # один язык и город, разные формы -> различитель формы
    same = [("VU", "Teisė", "T01", "Vilnius", "lt", "full_time"), ("VU", "Teisė", "T01", "Vilnius", "lt", "part_time")]
    assert sorted(assign_slugs(same).values()) == ["teise-full-time", "teise-part-time"]
    # разные города -> только город
    cities = [("SMK", "Dizainas", "M01", "Vilnius", "lt", "full_time"), ("SMK", "Dizainas", "M01", "Kaunas", "lt", "full_time")]
    assert sorted(assign_slugs(cities).values()) == ["dizainas-kaunas", "dizainas-vilnius"]

    institutions = {"KTU": institution, "LKA": Institution()}
    built = build(entries, cards, institutions)
    assert len(built) == 1, "учреждение без сведений о форме собственности не записывается"
    university, programmes = built[0]
    assert university.slug == "ktu" and university.country == "LT" and university.name_lt.startswith("Kauno")
    assert university.kind == "public" and university.city == "kaunas"
    assert [p.slug for p in programmes] == ["aviacijos-inzinerija-lt", "aviacijos-inzinerija-en"]
    assert programmes[0].duration_years == 4.0 and programmes[0].degree_level == "bachelor"
    assert programmes[0].name_lt == "Aviacijos inžinerija" and programmes[0].name_lv is None
    assert programmes[0].funding_type is None, "тип финансирования не угадывается"
    print("selftest: OK")


def _report(result: list[tuple[UniversityDraft, list[ProgrammeDraft]]]) -> None:
    programmes = [programme for _, items in result for programme in items]
    print(f"\nучреждений: {len(result)} | строк каталога: {len(programmes)}")
    for university, items in sorted(result, key=lambda pair: -len(pair[1])):
        print(f"  {university.slug:13} {university.kind:8} {university.city:11} {len(items):4}  {university.name_lt} | {university.name_en} | {university.website_url}")
    for label, values in (
        ("уровень", [p.degree_level for p in programmes]),
        ("язык", [p.language_of_instruction for p in programmes]),
        ("форма", [p.study_mode for p in programmes]),
        ("город", [p.city for p in programmes]),
        ("лет", [p.duration_years for p in programmes]),
    ):
        print(f"{label}: {Counter(values).most_common()}")
    print("без степени:", sum(1 for p in programmes if not p.degree_awarded_lt), "| без описания:", sum(1 for p in programmes if not p.description_lt), "| без срока:", sum(1 for p in programmes if p.duration_years is None))
    print("самые длинные коды:", sorted((p.slug for p in programmes), key=len)[-5:])


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        from dotenv import load_dotenv

        import polite

        load_dotenv()
        polite.install()
        sys.stdout.reconfigure(encoding="utf-8")
        _report(scrape_all())
        print(polite.report_and_reset())
