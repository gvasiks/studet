"""Колледжи — НЕ с их собственных сайтов, а из государственной базы
NIID.lv (тот же источник и та же разметка, что у via.py).

Почему NIID, а не сайты: колледжей около двадцати, у каждого свой сайт
на своём движке; по NIID все они лежат в одном формате
"название + Programmas veids/Valoda/Ilgums/Mācību maksa". Один сборщик
вместо двадцати — по правилу "скучное вместо элегантного" из CLAUDE.md.
Цена — данные, поэтому такие поля и так подтверждает человек.

Структура найдена вручную в браузере 2026-09-20 (страница
niid_search/provider/<название>?qy&tg=&level_1=7). Фильтр level_1=7
("Augstākā izglītība pēc vidējās izglītības") отсекает средние
профессиональные программы (код 33, "Profesionālā vidējā izglītība") —
у колледжей они идут в том же списке, но это не высшее образование и в
каталог не берутся.

Филиалы (Juridiskā koledža в Гулбене, Лиепае, Валмиере, Вентспилсе;
Grāmatvedības un finanšu koledža в Латгале; LU P.Stradiņa medicīnas
koledža в Резекне) — отдельные "провайдеры" NIID с теми же программами;
они добавляются к своему колледжу с переопределением города
(programme.city), а не отдельными записями каталога.

Пропущено из списка пользователя (в NIID их нет как колледжей):
Jēkabpils Agrobiznesa koledža (теперь Jēkabpils Tehnoloģiju tehnikums —
среднее профессиональное), Olaines Mehānikas un tehnoloģijas koledža
(влита в Rīgas Valsts tehnikums), Rīgas Uzņēmējdarbības koledža,
Latvijas Biznesa koledža, Starptautiskā Kosmetoloģijas koledža; Latvijas
Kultūras koledža — структурное подразделение LKA, у NIID нет своей
записи. Добавлены три колледжа, которых нет в списке, но есть в NIID и в
датасете выпускников: HOTEL SCHOOL, Novikontas Jūras koledža, Rīgas
Menedžmenta Koledža.

Сюда же добавлены два рижских филиала Латеранского
Папского университета (Laterāna Pontifikālās universitātes filiāle):
Rīgas Teoloģijas institūts и Rīgas Augstākais reliģijas zinātņu institūts.
Это не колледжи, но у них та же картина — одна-две программы, данные
только в NIID (собственные сайты garigais.lv и rarzi.lv — одностраничные).
У обоих в поле оплаты стоит не цена: у RTI — "Katoļu Baznīcas
finansējums" (финансирует Католическая церковь), поэтому цена пуста, а
funding_type остаётся осторожным 'paid'.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import quote, urljoin

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft
from sources.via import _EXTRACT_JS, _extract_languages, _programme_id

BASE_URL = "https://www.niid.lv"
LISTING = BASE_URL + "/niid_search/provider/{name}?qy&tg=&level_1=7&page={page}"
MAX_PAGES = 10  # страховка от бесконечного цикла; у самого большого — 2 страницы


@dataclass(frozen=True)
class College:
    slug: str
    name_lv: str
    kind: str  # 'public' | 'private'
    city: str
    # (название провайдера в NIID, город программ этого провайдера или None = город колледжа)
    providers: list[tuple[str, str | None]] = field(default_factory=list)


COLLEGES = [
    College("dmk", "Daugavpils medicīnas koledža", "public", "daugavpils",
            [("DU Daugavpils medicīnas koledža", None)]),
    College("psmk", "Latvijas Universitātes P.Stradiņa medicīnas koledža", "public", "riga",
            [("LU P.Stradiņa medicīnas koledža", None),
             ("LU P.Stradiņa medicīnas koledžas Rēzeknes filiāle", "rezekne")]),
    College("rmk", "Latvijas Universitātes Rīgas Medicīnas koledža", "public", "riga",
            [("LU Rīgas Medicīnas koledža", None)]),
    College("r1mk", "Latvijas Universitātes Rīgas 1. medicīnas koledža", "public", "riga",
            [("LU Rīgas 1. medicīnas koledža", None)]),
    College("ljk", "RTU Liepājas Jūrniecības koledža", "public", "liepaja",
            [("RTU Liepājas Jūrniecības koledža", None)]),
    College("malnavas-koledza", "LBTU Malnavas koledža", "public", "malnava",
            [("LBTU Malnavas koledža", None)]),
    College("rbk", "Rīgas Būvniecības koledža", "public", "riga",
            [("Rīgas Būvniecības koledža", None)]),
    College("skmk", "RSU Sarkanā Krusta medicīnas koledža", "public", "riga",
            [("RSU Sarkanā Krusta medicīnas koledža", None)]),
    College("rtk", "Rīgas Tehniskā koledža", "public", "riga",
            [("Rīgas Tehniskā koledža", None)]),
    College("siva", "Sociālās integrācijas valsts aģentūra", "public", "jurmala",
            [("Sociālās integrācijas valsts aģentūra", None)]),
    College("ucak", "Ugunsdrošības un civilās aizsardzības koledža", "public", "riga",
            [("Ugunsdrošības un civilās aizsardzības koledža", None)]),
    College("vpk", "Valsts policijas koledža", "public", "riga",
            [("Valsts policijas koledža", None)]),
    College("vrsk", "Valsts robežsardzes koledža", "public", "rezekne",
            [("Valsts robežsardzes koledža", None)]),
    College("alberta", "Alberta koledža", "private", "riga",
            [("Alberta koledža", None)]),
    College("gfk", "Grāmatvedības un finanšu koledža", "private", "riga",
            [("Grāmatvedības un finanšu koledža", None),
             ("Grāmatvedības un finanšu koledžas Latgales filiāle", "daugavpils")]),
    College("juridiska-koledza", "Juridiskā koledža", "private", "riga",
            [("Juridiskā koledža", None),
             ("Juridiskās koledžas Gulbenes filiāle", "gulbene"),
             ("Juridiskās koledžas Liepājas filiāle", "liepaja"),
             ("Juridiskās koledžas Valmieras filiāle", "valmiera"),
             ("Juridiskās koledžas Ventspils filiāle", "ventspils")]),
    College("bvk", "Biznesa vadības koledža", "private", "riga",
            [("Biznesa vadības koledža", None)]),
    College("rmenk", "Rīgas Menedžmenta Koledža", "private", "riga",
            [("Rīgas Menedžmenta Koledža", None)]),
    College("hotel-school", "HOTEL SCHOOL Viesnīcu biznesa koledža", "private", "riga",
            [('"HOTEL SCHOOL" Viesnīcu biznesa koledža', None)]),
    College("novikonta", "Novikontas Jūras koledža", "private", "riga",
            [("Novikontas Jūras koledža", None)]),
    College("rti", "Rīgas Teoloģijas institūts (Laterāna Pontifikālās universitātes filiāle)", "private", "riga",
            [("Laterāna Pontifikālās universitātes filiāle Rīgas Teoloģijas institūts", None)]),
    College("rarzi", "Rīgas Augstākais reliģijas zinātņu institūts (Laterāna Pontifikālās universitātes filiāle)", "private", "riga",
            [("Laterāna Pontifikālās universitātes filiāle Rīgas Augstākais reliģijas zinātņu institūts", None)]),
]

_WEBSITE_JS = """
() => {
  const links = Array.from(document.querySelectorAll('a[href^="http"]'));
  const own = links.find(a => !/niid\\.lv|facebook|instagram|twitter|youtube|linkedin/.test(a.href));
  return own ? own.href : null;
}
"""


def _college_level(programme_type: str) -> str | None:
    """None — не высшее образование, пропускаем."""
    lowered = programme_type.lower()
    # у бакалавриата в NIID нет слова "augstākā" ("Pirmā cikla bakalaura
    # studiju programma - 6. LKI"), поэтому признак — либо оно, либо
    # название степени; средние профессиональные отсекаются словом "vidējā"
    if "vidējā izglītība" in lowered or "pamatizglītīb" in lowered:
        return None
    if not any(word in lowered for word in ("augstāk", "bakalaura", "maģistra", "doktora")):
        return None
    if "doktora" in lowered or "trešā cikla" in lowered:
        return "doctoral"
    if "maģistra" in lowered or "otrā cikla" in lowered:
        return "master"
    if "īsā cikla" in lowered:
        return "college"
    return "bachelor"


def _duration_years(value: str) -> float | None:
    """"2,5 gadi" -> 2.5; "3 gadi un 3 mēneši" -> 3.25."""
    years = re.search(r"(\d+(?:[.,]\d+)?)\s*gad", value)
    months = re.search(r"(\d+)\s*mēnes", value)
    if not years and not months:
        return None
    total = float(years.group(1).replace(",", ".")) if years else 0.0
    return total + (int(months.group(1)) / 12 if months else 0)


def _study_mode(value: str) -> str:
    lowered = value.lower()
    if re.search(r"(?<!ne)pilna laika", lowered):
        return "full_time"
    if "nepilna" in lowered:
        return "part_time"
    return "full_time"


def _fee_and_funding(fee_text: str) -> tuple[float | None, str]:
    lowered = fee_text.lower()
    has_budget = "budžet" in lowered
    # цена берётся только если она явно за год: "1220 EUR gadā". Цена за
    # семестр/месяц/кредитпункт молча превратилась бы в неверную годовую
    per_year = re.search(r"(\d+(?:[.,]\d+)?)\s*EUR\s*gadā", fee_text)
    fee = float(per_year.group(1).replace(",", ".")) if per_year else None
    if has_budget and fee is None and "eur" not in lowered:
        return None, "budget"
    if has_budget:
        return fee, "both"
    return fee, "paid"


def _scrape_provider(page: Page, name: str) -> tuple[list[dict], str | None]:
    entries: dict[str, dict] = {}
    website: str | None = None
    for number in range(1, MAX_PAGES + 1):
        page.goto(LISTING.format(name=quote(name), page=number), wait_until="domcontentloaded")
        if website is None:
            website = page.evaluate(_WEBSITE_JS)
        found = page.evaluate(_EXTRACT_JS)
        new = [entry for entry in found if _programme_id(entry["href"]) not in entries]
        if not new:
            break
        for entry in new:
            entries[_programme_id(entry["href"])] = entry
    return list(entries.values()), website


def _programmes_from(entries: list[dict], city: str) -> list[ProgrammeDraft]:
    programmes: list[ProgrammeDraft] = []
    for entry in entries:
        fields = entry["fields"]
        level = _college_level(fields.get("Programmas veids", ""))
        if level is None:
            continue
        fee, funding = _fee_and_funding(fields.get("Mācību/studiju maksa", ""))
        languages = _extract_languages(fields.get("Valoda", ""))
        programme_id = _programme_id(entry["href"])
        for language in languages:
            programmes.append(
                ProgrammeDraft(
                    slug=f"{programme_id}-{language}" if len(languages) > 1 else programme_id,
                    name_lv=entry["name"],
                    degree_level=level,
                    language_of_instruction=language,
                    study_mode=_study_mode(fields.get("Studiju veids", "")),
                    city=city,
                    funding_type=funding,
                    tuition_fee_amount=fee,
                    duration_years=_duration_years(fields.get("Ilgums", "")),
                    source_url=urljoin(BASE_URL, entry["href"]),
                )
            )
    return programmes


def scrape_all() -> list[tuple[UniversityDraft, list[ProgrammeDraft]]]:
    results: list[tuple[UniversityDraft, list[ProgrammeDraft]]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for college in COLLEGES:
            programmes: list[ProgrammeDraft] = []
            website: str | None = None
            for provider, city in college.providers:
                entries, provider_site = _scrape_provider(page, provider)
                website = website or provider_site
                programmes.extend(_programmes_from(entries, city or college.city))

            # колледж без единой программы высшего образования (у SIVA,
            # например, могут быть только профессиональные средние) в
            # каталог не попадает — его нечем наполнить
            if not programmes:
                print(f"niid_colleges: {college.slug} — нет программ высшего образования, пропущен")
                continue

            university = UniversityDraft(
                slug=college.slug,
                name_lv=college.name_lv,
                kind=college.kind,
                city=college.city,
                website_url=website,
                source_url=LISTING.format(name=quote(college.providers[0][0]), page=1),
            )
            results.append((university, programmes))

        browser.close()
    return results
