"""Эстония: каталог высшего образования с государственного портала.

Источник — список программ портала haridusportaal.edu.ee (ведёт министерство
образования и науки). Страница https://haridusportaal.edu.ee/erialad получает
его запросом к api.hp.edu.ee; тот же запрос делает этот сборщик. Проверено
2026-10-11: robots.txt путь /api/ не запрещает, в списке 1131 программа у
21 учреждения (счётчик «1857» на странице завышен: сам портал показывает
половину).

Это внутренний интерфейс портала, а не объявленные открытые данные: он может
измениться без предупреждения. Поэтому сборщик проверяет ответ и при
непонятном формате останавливается, ничего не записав.

Что есть в записи: название, учреждение и форма собственности, уровень,
языки обучения, длительность, присваиваемая степень, адрес учреждения.

Чего в источнике нет:
- формы обучения (study_mode остаётся пустым — она указана только на
  странице конкурса в SAIS, а конкурс открыт не у каждой программы);
- цены и бюджетных мест (funding_type и плата пустые);
- английских названий (запрос с lang=en возвращает эстонские);
- описания программы.

Строка каталога = программа на одном языке обучения. Программа, у которой
портал называет два языка, пишется двумя записями — так же, как латвийские
программы с двумя языками в NIID (решение владельца 2026-10-10). Оговорка
та же: два языка в реестре значат, что программу разрешено вести на обоих,
а не что на оба идёт набор.

Город — из адреса учреждения, который портал показывает у программы. У вуза
с филиалами (Нарва, Пярну, Вильянди) это город головного здания, а не
место учёбы; уточнить можно будет по странице конкурса в SAIS.

Не записываются:
- записи без уровня (ординатура врачей и ещё около двадцати без пометки);
- программа без языка, если её ещё нет в базе (общее правило main.py).

Эстонские факты показываются без подтверждения человеком, с пометкой
«извлечено автоматически» — решение владельца 2026-10-11, как для Литвы.

Запуск:
  python src/sources/ee_haridusportaal.py --selftest   # разбор на встроенных примерах, без сети
  python src/sources/ee_haridusportaal.py              # собрать и напечатать сводку, без записи в базу
  python src/main.py ee_haridusportaal                 # собрать и записать (источник запускается только по имени)

Сбор — около двадцати запросов с паузами (polite.py), меньше минуты.
"""

from __future__ import annotations

import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from models import ProgrammeDraft, UniversityDraft

PORTAL = "https://haridusportaal.edu.ee"
CATALOG_URL = f"{PORTAL}/erialad"
LIST_URL = "https://api.hp.edu.ee/api/list?_format=json&content_type=study_programme&offset={offset}&limit={limit}"

# Сервер отдаёт не больше половины запрошенного (на limit=100 приходит до
# 50 записей, реже до 100), но смещение считает по limit — поэтому шаг
# смещения равен limit, а не числу пришедших записей.
PAGE_LIMIT = 100
# Счётчик count в ответе примерно вдвое больше числа видимых записей. Обход
# идёт до него; запас — на случай, если пропорция изменится.
MAX_OFFSET = 6000

LEVELS = {
    "Bakalaureuseõpe": "bachelor",
    "Magistriõpe": "master",
    "Doktoriõpe": "doctoral",
    # Прикладное высшее образование (3–4,5 года после школы) — то же место в
    # каталоге, что у латвийских и литовских колледжей.
    "Rakenduskõrgharidusõpe": "college",
    "Integreeritud õpe": "integrated",
}

LANGUAGES = {"eesti keel": "et", "inglise keel": "en", "vene keel": "ru"}
# В каком порядке языки одной программы получают записи: первая сохраняет
# код программы, остальные — с суффиксом языка.
LANGUAGE_ORDER = ["et", "en", "ru"]

# Форма собственности учреждения. Публично-правовые университеты и
# государственные высшие школы — 'public'.
OWNERSHIP = {"Avalik-õiguslik": "public", "Riigiomandus": "public", "Eraomand": "private"}

# Коды учреждений в адресах сайта. Правило владельца (2026-10-05): если
# сокращение совпало с уже занятым кодом, к коду добавляется страна — у
# Эстонской академии художеств это "eka-ee" (код "eka" занят латвийской
# Ekonomikas un kultūras augstskola). Учреждение, которого здесь нет,
# получает код из названия (см. university_slug).
SLUGS = {
    "Tartu Ülikool": "ut",
    "Tallinna Ülikool": "tlu",
    "Tallinna Tehnikaülikool": "taltech",
    "Eesti Maaülikool": "emu",
    "Eesti Kunstiakadeemia": "eka-ee",
    "Eesti Muusika- ja Teatriakadeemia": "emta",
    "Tallinna Tehnikakõrgkool": "tktk",
    "Eesti Ettevõtluskõrgkool Mainor": "eek",
    "Euroakadeemia": "euroakadeemia",
    "Estonian Business School": "ebs",
    "Sisekaitseakadeemia": "ska",
    "Tartu Tervishoiu Kõrgkool": "tartuh",
    "Tallinna Tervishoiu Kõrgkool": "ttk",
    "Kõrgem Kunstikool Pallas": "pallas",
    "Eesti Lennuakadeemia": "eava",
    "Kaitseväe Akadeemia": "kvak",
    "Võrumaa Haridus- ja Tehnoloogiakeskus": "vorumaa-htk",
    "Lääne-Viru Rakenduskõrgkool": "lvrkk",
    "Eesti Metodisti Kiriku Teoloogiline Seminar": "emkts",
    "EELK Usuteaduse Instituut": "eelkui",
    "Eesti EKB Liit Kõrgem Usuteaduslik Seminar": "kus",
}

# Коды латвийских и литовских учреждений на 2026-10-11; занятый код не
# переиспользуется.
TAKEN_SLUGS = {
    "alberta", "bsa", "bvk", "dmk", "du", "eka", "ekra", "gfk", "hotel-school", "juridiska-koledza", "jvlma",
    "lbtu", "ljk", "lka", "lma", "lnaa", "lu", "lutera", "malnavas-koledza", "novikonta", "psmk", "r1mk", "rai",
    "rarzi", "rbk", "rgsl", "riseba", "rmenk", "rmk", "rnu", "rsu", "rti", "rtk", "rtu", "siva", "skmk",
    "sse-riga", "tsi", "turiba", "ucak", "venta", "via", "vpk", "vrsk",
    "ehu", "ilk", "ism", "kk", "kok", "ksu", "ktu", "ku", "kvk", "lcc", "lik", "lka-lt", "lmta", "lsmu", "lsu",
    "ltvk", "mru", "pk", "smk", "svk", "uk", "vda", "vdk", "vdu", "vilnius-tech", "vk", "vu", "vvk",
}


class PortalChanged(RuntimeError):
    """Ответ портала не похож на список программ — формат изменился."""


def slugify(text: str) -> str:
    plain = unicodedata.normalize("NFD", text)
    plain = "".join(ch for ch in plain if not unicodedata.combining(ch)).lower()
    out = "".join(ch if ch.isascii() and ch.isalnum() else "-" for ch in plain)
    return "-".join(part for part in out.split("-") if part)


def university_slug(name: str) -> str:
    slug = SLUGS.get(name) or slugify(name)
    return f"{slug}-ee" if slug in TAKEN_SLUGS else slug


def values(node: object) -> list:
    """Поле-справочник портала: {"1689": "eesti keel"}; пустое приходит как
    null или пустой список."""
    if isinstance(node, dict):
        return list(node.values())
    if isinstance(node, list):
        return node
    return [] if node is None else [node]


def city_of(address: str | None) -> str | None:
    """Город из адреса вида «улица, поселение, самоуправление, уезд».

    «Kesklinna linnaosa, Tallinn, Harju maakond» -> tallinn
    «Tartu linn, Tartu linn, Tartu maakond»      -> tartu
    «Reola küla, Kambja vald, Tartu maakond»     -> reola (волость — не город,
                                                    берём поселение)
    """
    parts = [part.strip() for part in (address or "").split(",") if part.strip()]
    if len(parts) < 3 or not parts[-1].endswith("maakond"):
        return None
    municipality, settlement = parts[-2], parts[-3]
    name = settlement if municipality.endswith(" vald") else municipality
    for suffix in (" linn", " küla", " alevik", " alev"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return slugify(name) or None


def languages_of(record: dict) -> list[str | None]:
    """Языки обучения в порядке записи. [None] — портал языка не называет
    или назвал только незнакомый: такая программа записывается без языка."""
    found = {LANGUAGES[name] for name in values(record.get("fieldTeachingLanguage")) if name in LANGUAGES}
    return [language for language in LANGUAGE_ORDER if language in found] or [None]


def programme_slug(record: dict) -> str:
    """Код программы — последний сегмент её адреса на портале: он уникален
    на всём портале и не меняется при переименовании полей."""
    return slugify(unquote(str(record.get("path") or "")).rstrip("/").split("/")[-1])


def years_of(record: dict) -> float | None:
    try:
        months = int(record.get("fieldDuration"))
    except (TypeError, ValueError):
        return None
    return round(months / 12, 2) if months > 0 else None


def institution_of(record: dict) -> dict | None:
    institutions = values(record.get("fieldEducationalInstitution"))
    return institutions[0] if len(institutions) == 1 and isinstance(institutions[0], dict) else None


def institution_address(institution: dict) -> str | None:
    locations = values(institution.get("fieldSchoolLocation"))
    return next((loc.get("fieldAddress") for loc in locations if isinstance(loc, dict) and loc.get("fieldAddress")), None)


def check_records(records: list[dict]) -> None:
    """Формат изменился, если записей нет или у большинства пропали поля, на
    которых стоит каталог."""
    if not records:
        raise PortalChanged("портал не вернул ни одной программы")
    for field in ("title", "path", "fieldStudyProgrammeLevel", "fieldEducationalInstitution"):
        present = sum(1 for record in records if record.get(field))
        if present < len(records) * 0.8:
            raise PortalChanged(
                f"поле {field} есть только у {present} записей из {len(records)} — похоже, портал изменил формат. "
                "В базу ничего не записано."
            )


def build(records: list[dict]) -> list[tuple[UniversityDraft, list[ProgrammeDraft]]]:
    check_records(records)
    now = datetime.now(timezone.utc).isoformat()

    by_institution: dict[str, list[dict]] = defaultdict(list)
    skipped = Counter()
    for record in records:
        institution = institution_of(record)
        if institution is None or not institution.get("title"):
            skipped["нет учреждения"] += 1
            continue
        by_institution[institution["title"]].append(record)

    result = []
    for name, items in by_institution.items():
        institution = institution_of(items[0])
        ownership = values(institution.get("fieldOwnershipType"))
        kind = OWNERSHIP.get(ownership[0]) if len(ownership) == 1 else None
        home_city = city_of(institution_address(institution))
        if kind is None or home_city is None:
            # Форма собственности и город — факты, которые читаются только
            # из источника. Без них учреждение пропускается целиком, а не
            # записывается с угаданным значением.
            print(f"ee_haridusportaal: {name} пропущено — не прочитана форма собственности ({ownership}) или город")
            skipped["учреждение без формы собственности или города"] += len(items)
            continue

        programmes: list[ProgrammeDraft] = []
        seen: set[str] = set()
        for record in items:
            levels = [LEVELS[level] for level in values(record.get("fieldStudyProgrammeLevel")) if level in LEVELS]
            if len(levels) != 1:
                skipped["нет уровня"] += 1
                continue
            base = programme_slug(record)
            if not base or not record.get("title"):
                skipped["нет адреса или названия"] += 1
                continue
            degree = "; ".join(str(value) for value in values(record.get("fieldDegreeOrDiplomaAwarded"))) or None
            source_url = PORTAL + str(record["path"])
            for index, language in enumerate(languages_of(record)):
                slug = base if index == 0 else f"{base}-{language}"
                if slug in seen:
                    # два адреса портала дали один код — различаем номером записи
                    slug = f"{slug}-{record.get('nid')}"
                seen.add(slug)
                programmes.append(
                    ProgrammeDraft(
                        slug=slug,
                        name_et=str(record["title"]).strip(),
                        degree_level=levels[0],
                        language_of_instruction=language,
                        city=city_of(record.get("fieldSchoolSearchAddress")) or home_city,
                        duration_years=years_of(record),
                        degree_awarded_et=degree,
                        details_source_url=source_url if degree else None,
                        details_extracted_at=now if degree else None,
                        source_url=source_url,
                    )
                )

        university = UniversityDraft(
            slug=university_slug(name),
            country="EE",
            name_et=name,
            kind=kind,
            city=home_city,
            website_url=institution.get("fieldSchoolWebpageAddress") or None,
            source_url=CATALOG_URL,
        )
        result.append((university, programmes))

    if skipped:
        print("ee_haridusportaal: не записано — " + ", ".join(f"{reason}: {count}" for reason, count in skipped.items()))
    return result


def collect() -> list[dict]:
    """Все записи списка программ портала, без повторов. Отдельно от build():
    те же записи понадобятся загрузчикам направлений и сроков приёма."""
    records: dict[str, dict] = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        offset, total = 0, None
        while total is None or offset < total:
            url = LIST_URL.format(offset=offset, limit=PAGE_LIMIT)
            response = page.goto(url, timeout=45000)
            if response is None or response.status != 200:
                raise PortalChanged(f"портал ответил {response.status if response else 'ничем'} на {url}")
            data = response.json()
            if not isinstance(data, dict) or "entities" not in data or "count" not in data:
                raise PortalChanged(f"в ответе нет списка entities или счётчика count — {url}")
            total = min(int(data["count"]), MAX_OFFSET)
            for record in data["entities"] or []:
                records[str(record.get("nid"))] = record
            offset += PAGE_LIMIT
        browser.close()
    return list(records.values())


def scrape_all() -> list[tuple[UniversityDraft, list[ProgrammeDraft]]]:
    return build(collect())


def _selftest() -> None:
    assert slugify("Ettevõtlus ja ärijuhtimine") == "ettevotlus-ja-arijuhtimine"
    assert university_slug("Eesti Kunstiakadeemia") == "eka-ee"
    assert university_slug("Tartu Ülikool") == "ut"
    # незнакомое учреждение — код из названия; занятый код получает страну
    assert university_slug("Uus Kõrgkool") == "uus-korgkool"
    assert university_slug("LU") == "lu-ee"
    assert not set(SLUGS.values()) & TAKEN_SLUGS, "код из таблицы уже занят"
    assert len(set(SLUGS.values())) == len(SLUGS), "два учреждения с одним кодом"

    assert values({"1": "a", "2": "b"}) == ["a", "b"] and values([]) == [] and values(None) == []

    assert city_of("Narva mnt 25, Kesklinna linnaosa, Tallinn, Harju maakond") == "tallinn"
    assert city_of("Kesklinna linnaosa, Tallinn, Harju maakond") == "tallinn"
    assert city_of("Tartu linn, Tartu linn, Tartu maakond") == "tartu"
    assert city_of("Lennu tn 40, Reola küla, Kambja vald, Tartu maakond") == "reola"
    assert city_of("Kooli tee 1, Väimela alevik, Võru vald, Võru maakond") == "vaimela"
    assert city_of(None) is None and city_of("Tallinn") is None

    def record(nid: str, path: str, **fields: object) -> dict:
        base = {
            "nid": nid,
            "path": path,
            "title": "Õigusteadus",
            "fieldStudyProgrammeLevel": {"1": "Bakalaureuseõpe"},
            "fieldTeachingLanguage": {"1689": "eesti keel"},
            "fieldDuration": "36",
            "fieldDegreeOrDiplomaAwarded": {"9": "Sotsiaalteaduse bakalaureus"},
            "fieldSchoolSearchAddress": "Tartu linn, Tartu linn, Tartu maakond",
            "fieldEducationalInstitution": {
                "5": {
                    "title": "Tartu Ülikool",
                    "fieldOwnershipType": {"1": "Avalik-õiguslik"},
                    "fieldSchoolWebpageAddress": "http://www.ut.ee/",
                    "fieldSchoolLocation": {"7": {"fieldAddress": "Ülikooli tn 18, Tartu linn, Tartu linn, Tartu maakond"}},
                }
            },
        }
        base.update(fields)
        return base

    records = [
        record("1", "/erialad/%C3%B5igusteadus"),
        # два языка — две записи: эстонская сохраняет код, английская с суффиксом
        record("2", "/erialad/informaatika", title="Informaatika", fieldTeachingLanguage={"1689": "eesti keel", "1690": "inglise keel"}),
        # языка нет — запись без языка (новую main.py не запишет)
        record("3", "/erialad/keemia", title="Keemia", fieldTeachingLanguage=[], fieldDuration=None),
        # уровня нет (ординатура) — не записывается
        record("4", "/erialad/kirurgia", title="Kirurgia", fieldStudyProgrammeLevel=[]),
        # адреса у программы нет — город учреждения
        record("5", "/erialad/ajalugu", title="Ajalugu", fieldSchoolSearchAddress=None, fieldDuration="42", fieldDegreeOrDiplomaAwarded=None),
    ]
    result = build(records)
    assert len(result) == 1
    university, programmes = result[0]
    assert (university.slug, university.country, university.kind, university.city) == ("ut", "EE", "public", "tartu")
    assert university.name_et == "Tartu Ülikool" and university.name_lv is None
    by_slug = {programme.slug: programme for programme in programmes}
    assert sorted(by_slug) == ["ajalugu", "informaatika", "informaatika-en", "keemia", "oigusteadus"], sorted(by_slug)
    law = by_slug["oigusteadus"]
    assert (law.degree_level, law.language_of_instruction, law.city, law.duration_years) == ("bachelor", "et", "tartu", 3.0)
    assert law.study_mode is None and law.funding_type is None
    assert law.degree_awarded_et == "Sotsiaalteaduse bakalaureus"
    assert law.source_url == "https://haridusportaal.edu.ee/erialad/%C3%B5igusteadus"
    assert by_slug["informaatika"].language_of_instruction == "et" and by_slug["informaatika-en"].language_of_instruction == "en"
    assert by_slug["keemia"].language_of_instruction is None and by_slug["keemia"].duration_years is None
    assert by_slug["ajalugu"].city == "tartu" and by_slug["ajalugu"].duration_years == 3.5
    assert by_slug["ajalugu"].degree_awarded_et is None and by_slug["ajalugu"].details_source_url is None

    # частное учреждение; незнакомая форма собственности — учреждение пропускается
    private = record("6", "/erialad/arijuhtimine")
    private["fieldEducationalInstitution"]["5"].update(title="Estonian Business School", fieldOwnershipType={"1": "Eraomand"})
    unknown = record("7", "/erialad/teoloogia")
    unknown["fieldEducationalInstitution"]["5"].update(title="Uus Kõrgkool", fieldOwnershipType={"1": "Munitsipaalomand"})
    built = dict((university.slug, university.kind) for university, _ in build([private, unknown]))
    assert built == {"ebs": "private"}, built

    # ответ не похож на список программ — остановка
    for broken in ([], [{"nid": "1", "foo": "bar"}]):
        try:
            build(broken)
        except PortalChanged:
            pass
        else:
            raise AssertionError("ожидалась ошибка PortalChanged")
    print("ee_haridusportaal selftest: ok")


def _report(result: list[tuple[UniversityDraft, list[ProgrammeDraft]]]) -> None:
    programmes = [programme for _, items in result for programme in items]
    print(f"\nучреждений: {len(result)} | строк каталога: {len(programmes)}")
    for university, items in sorted(result, key=lambda pair: -len(pair[1])):
        print(f"  {university.slug:14} {university.kind:8} {university.city:9} {len(items):4}  {university.name_et} | {university.website_url}")
    for label, column in (
        ("уровень", [p.degree_level for p in programmes]),
        ("язык", [p.language_of_instruction for p in programmes]),
        ("город", [p.city for p in programmes]),
        ("лет", [p.duration_years for p in programmes]),
    ):
        print(f"{label}: {Counter(column).most_common()}")
    print("без степени:", sum(1 for p in programmes if not p.degree_awarded_et), "| без срока:", sum(1 for p in programmes if p.duration_years is None))
    print("самые длинные коды:", sorted((p.slug for p in programmes), key=len)[-3:])


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.stdout.reconfigure(encoding="utf-8")
        _selftest()
    else:
        from dotenv import load_dotenv

        import polite

        load_dotenv()
        polite.install()
        sys.stdout.reconfigure(encoding="utf-8")
        _report(scrape_all())
        print(polite.report_and_reset())
