"""Добор программ из NIID.lv для вузов, чьи сборщики видели не всё.

Причина. LBTU, DU и Turība собираются с английских разделов сайтов, а в
них нет программ, которые ведутся только по-латышски; у RISEBA и RSU не
собраны магистратура и докторантура. Аудит 2026-09-20 (docs/
AUDIT-COMPLETENESS.md, инструмент audit_completeness.py) насчитал по этим
пяти вузам порядка 100–130 недостающих программ; вариант A из аудита —
добрать их из государственной базы NIID.lv, той же, что уже кормит
колледжи и ViA.

Как это устроено.
- Существующие сборщики (lbtu.py, du.py, turiba.py, riseba.py, rsu.py) не
  меняются и остаются источником для всего, что они собирают: у них есть
  число бюджетных мест и ссылка на сайт вуза. Этот сборщик только ДОБАВЛЯЕТ.
- Программа NIID добавляется, если её нет в COVERED — явном списке
  "название NIID, наш уровень", составленном вручную сверкой NIID с нашим
  каталогом. Автосопоставление по названию ненадёжно: у NIID названия
  латышские, у наших строк по большей части английские.
- Что теряется по сравнению с собственным сборщиком: числа бюджетных мест
  нет (в NIID оно есть только как "Valsts budžets vai par maksu" — это тип
  финансирования 'both'), название только латышское, ссылка ведёт на
  страницу программы в NIID, а не на сайт вуза. Число мест человек
  подтверждает по документам вуза (правило 6 CLAUDE.md).
- Строки идут со слагом "niid-<id>" (у двуязычной записи NIID —
  "-lv" и "-en"), чтобы не пересекаться со слагами собственных сборщиков.
- Город — город вуза из его собственного сборщика. У программ, которые на
  самом деле идут в филиале, он может быть неточным.

Что НЕ берётся: записи без степени высшего образования (в докторантуре
NIID лежит и "Rezidentūra" — резидентура, у нас такого уровня нет).

Когда NIID добавит программу, которая уже есть у нас под другим именем,
она появится второй раз — тогда её название надо внести в COVERED
(audit_completeness.py покажет расхождение по числам).
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

from models import ProgrammeDraft, UniversityDraft
from sources import du, lbtu, niid_colleges as base, riseba, rsu, turiba
from sources.via import _extract_languages, _programme_id

BASE_URL = base.BASE_URL


@dataclass(frozen=True)
class Target:
    university: UniversityDraft
    provider: str  # название учреждения в NIID
    levels: tuple[str, ...]  # level_1 в NIID: 7 бакалавриат и короткие, 8 магистратура, 9 докторантура
    covered: frozenset[tuple[str, str]]  # (наш уровень, название NIID) — уже есть в каталоге


TARGETS = [
    Target(
        university=lbtu.UNIVERSITY,
        provider="Latvijas Biozinātņu un tehnoloģiju universitāte",
        levels=("7", "8", "9"),
        covered=frozenset(
            {
                # английские программы собственного сборщика lbtu.py
                ("bachelor", "Biosistēmu mašinērija un tehnoloģijas"),
                ("bachelor", "Informācijas tehnoloģijas ilgtspējīgai attīstībai"),
                ("bachelor", "Organizāciju un sabiedrības pārvaldes socioloģija"),
                ("master", "Cilvēkresursu vadība un karjeras konsultēšana"),
                ("master", "Informācijas tehnoloģijas"),
                ("master", "Organizāciju un sabiedrības pārvaldes socioloģija"),
                ("master", "Pārtikas zinātne"),
                ("master", "Uzņēmējdarbības vadība"),
                ("master", "Ģeoinformātika un tālizpēte"),
            }
        ),
    ),
    Target(
        university=du.UNIVERSITY,
        provider="Daugavpils Universitāte",
        levels=("7", "8", "9"),
        covered=frozenset(
            {
                # девять программ du.py (англоязычный раздел, но часть — на латышском)
                ("bachelor", "Austrumeiropas kultūras sakari un integrācijas procesi"),
                ("bachelor", "Bioloģija"),
                ("bachelor", "Psiholoģija"),
                ("bachelor", "Stratēģiskie riski un krīžu pārvaldība"),
                ("bachelor", "Tiesību zinātne"),
                ("bachelor", "Valodu un kultūras studijas"),
                ("bachelor", "Vides zinātne"),
                ("bachelor", "Vēsture"),
                ("bachelor", "Ķīmija"),
            }
        ),
    ),
    Target(
        university=turiba.UNIVERSITY,
        provider="Biznesa augstskola Turība",
        levels=("7", "8"),  # докторантура совпала с NIID (4 против 4)
        covered=frozenset(
            {
                ("bachelor", "Biznesa loģistikas vadība"),
                ("bachelor", "Datorsistēmas"),
                ("bachelor", "Starptautiskās komunikācijas vadība"),
                ("bachelor", "Tūrisma un viesmīlības nozares uzņēmumu vadība"),
                ("bachelor", "Uzņēmējdarbības vadība"),
                ("college", "Estētiskā kosmetoloģija"),
                ("college", "Programmētājs"),
                ("master", "Biznesa psiholoģija un cilvēkresursu vadība uzņēmējdarbībā"),
                ("master", "Informācijas tehnoloģijas"),
                ("master", "Organizācijas drošības vadība"),
                ("master", "Stratēģiskā komunikācijas vadība"),
                ("master", "Tūrisma stratēģiskā vadība"),
                ("master", "Uzņēmējdarbības vadība"),
            }
        ),
    ),
    Target(
        university=riseba.UNIVERSITY,
        provider='Biznesa, mākslas un tehnoloģiju augstskola "RISEBA"',
        levels=("8", "9"),  # бакалавриат собран riseba.py полностью (6 против 6)
        covered=frozenset(),
    ),
    Target(
        university=rsu.UNIVERSITY,
        provider="Rīgas Stradiņa universitāte",
        levels=("8",),
        # Докторантуру не берём: NIID делит "Sociālās zinātnes" и "Veselības
        # aprūpe" на десять специализаций, у нас это две программы rsu.py
        # ("Social Sciences", "Health Care") — дробление осознанно не повторяем
        covered=frozenset(
            {
                ("master", "Biomedicīna"),
                ("master", "Biostatistika"),
                ("master", "Digitālās stratēģijas un mākslīgā intelekta vadība"),
                ("master", "Ekonomiskā drošība"),
                ("master", "Klīniskā farmācija"),
                ("master", "Komunikācija un mediju studijas"),
                ("master", "Mākslas terapija"),
                ("master", "Rehabilitācija"),
                ("master", "Sabiedrības veselība"),
                ("master", "Sociālā antropoloģija"),
                ("master", "Sociālais darbs ar bērniem un jauniešiem"),
                ("master", "Starptautiskā mārketinga un biznesa vadība"),
                ("master", "Starptautiskās attiecības un diplomātija"),
                ("master", "Stratēģiskā un sabiedrisko attiecību vadība"),
                ("master", "Tiesību zinātne"),  # две записи NIID: профессиональная и академическая
                ("master", "Uzturzinātne"),
                ("master", "Veselības psiholoģija"),
                ("master", "Veselības vadība"),
                ("master", "Rūpnieciskā farmācija"),
            }
        ),
    ),
]


def _draft(target: Target, entry: dict, level: str) -> list[ProgrammeDraft]:
    fields = entry["fields"]
    fee, funding = base._fee_and_funding(fields.get("Mācību/studiju maksa", ""))
    languages = _extract_languages(fields.get("Valoda", ""))
    programme_id = _programme_id(entry["href"])
    source_url = urljoin(BASE_URL, entry["href"])

    return [
        ProgrammeDraft(
            slug=f"niid-{programme_id}-{language}" if len(languages) > 1 else f"niid-{programme_id}",
            name_lv=entry["name"],
            degree_level=level,
            language_of_instruction=language,
            study_mode=base._study_mode(fields.get("Studiju veids", "")),
            city=target.university.city,
            funding_type=funding,
            tuition_fee_amount=fee,
            duration_years=base._duration_years(fields.get("Ilgums", "")),
            source_url=source_url,
        )
        for language in languages
    ]


def scrape_all() -> list[tuple[UniversityDraft, list[ProgrammeDraft]]]:
    results: list[tuple[UniversityDraft, list[ProgrammeDraft]]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        for target in TARGETS:
            programmes: list[ProgrammeDraft] = []
            seen_ids: set[str] = set()
            for nid_level in target.levels:
                entries, _ = base._scrape_provider(page, target.provider, nid_level)
                for entry in entries:
                    programme_id = _programme_id(entry["href"])
                    if programme_id in seen_ids:
                        continue  # одна запись может лежать в двух уровнях фильтра
                    seen_ids.add(programme_id)

                    level = base._college_level(entry["fields"].get("Programmas veids", ""))
                    if level is None:
                        continue  # не степень высшего образования (например, резидентура)
                    if (level, entry["name"]) in target.covered:
                        continue  # уже есть у собственного сборщика
                    programmes.extend(_draft(target, entry, level))

            results.append((target.university, programmes))

        browser.close()
    return results

