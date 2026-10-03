"""Степень и описание программы — со страницы программы на сайте самого вуза.

Порция 3 работы «диплом и описание для остальных программ» (2026-10-03).
Для вузов, у которых в каталоге только английские названия программ (в
NIID их по названию не найти) и чьи собственные страницы содержат и
степень, и описание на английском. ЛУ живёт в отдельном скрипте
(enrich_lu_details.py) — он появился раньше; новые вузы добавляются сюда.

  степень  -> programme.degree_awarded_en
  описание -> programme.description_en (начало, как у NIID и ЛУ)

Как добавить вуз: написать функцию-разборщик `(текст страницы, заголовок h1,
уровень программы) -> {"degree_awarded_en", "description_en"}` — чистую, с
примером в selftest() — и внести её в PARSERS под ключом source_key. Сеть и
база у всех общие.

  python src/enrich_site_details.py                # показать, что будет записано
  python src/enrich_site_details.py --apply        # записать
  python src/enrich_site_details.py rsu --limit 5  # только RSU, первые 5 страниц
  python src/enrich_site_details.py --all          # перечитать и уже заполненные
  python src/enrich_site_details.py --skip-local   # без вузов, не отвечающих GitHub
  python src/enrich_site_details.py --local        # только такие вузы
  python src/enrich_site_details.py --selftest     # самотест без сети и базы

--skip-local / --local — те же флаги и тот же список, что у main.py
(scrape_scope.LOCAL_ONLY): lma.lv не отдаёт страницы серверу GitHub, поэтому
ежемесячный workflow запускает скрипт с --skip-local, а LMA заполняется на
компьютере владельца.

Правило 6 CLAUDE.md эти поля не затрагивает; verified_at не трогается.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from datetime import datetime, timezone

from enrich_niid_details import clean_line, excerpt, is_due
from scrape_scope import LOCAL_ONLY

Details = dict[str, str | None]

# Описание короче этого — обрывок страницы, а не описание (как в
# enrich_lu_details.py).
MIN_DESCRIPTION_LENGTH = 80
MAX_DEGREE_LENGTH = 200


def _lines(text: str) -> list[str]:
    return [line.replace("\xa0", " ").strip() for line in text.split("\n")]


def _join_paragraphs(lines: list[str]) -> str | None:
    """Непустые строки -> абзацы через пустую строку; коротышка -> None."""
    paragraphs = [line for line in lines if line]
    description = "\n\n".join(paragraphs)
    return description if len(description) >= MIN_DESCRIPTION_LENGTH else None


# Латышские буквы с диакритикой. На английских страницах RSU у двух программ
# степень написана по-латышски; в degree_awarded_en (на странице у него
# lang="en") такой текст не кладём.
_LATVIAN_LETTERS = re.compile("[āčēģīķļņšūžĀČĒĢĪĶĻŅŠŪŽ]")


def _degree(lines: list[str]) -> str | None:
    degree = clean_line("; ".join(line.rstrip(",;") for line in lines if line))
    if not degree or len(degree) > MAX_DEGREE_LENGTH or _LATVIAN_LETTERS.search(degree):
        return None
    return degree


# ---------- RSU: rsu.lv/en/study-programme/<slug> ----------

_RSU_FACT_LABEL = re.compile(r"^(Language|ECTS|Study location|Places|Study direction)\b", re.IGNORECASE)
_RSU_SECTION_END = ("Learning methods", "Director of Programme", "Teaching Staff", "Contact Information")


def rsu_details(body: str, title: str, level: str) -> Details:
    """Страница программы RSU.

    Степень — строки после «Degree conferred / qualification obtained:» до
    следующего поля. Описание — вступление между заголовком программы и
    блоком «Programme Fact File»; если его нет — начало раздела «Study
    content».
    """
    lines = _lines(body)

    degree_lines: list[str] = []
    for index, line in enumerate(lines):
        if line.lower().startswith("degree conferred"):
            for value in lines[index + 1 :]:
                if not value or _RSU_FACT_LABEL.match(value) or re.match(r"^\d", value):
                    break
                degree_lines.append(value)
            break

    lead: list[str] = []
    if "Programme Fact File" in lines and title:
        fact_index = lines.index("Programme Fact File")
        # название программы может встречаться и в меню — берём последнее
        # вхождение перед блоком фактов
        candidates = [i for i, line in enumerate(lines[:fact_index]) if line == title]
        if candidates:
            lead = [
                line
                for line in lines[candidates[-1] + 1 : fact_index]
                # «This programme is only offered in Latvian.» — язык и так отдельное поле
                if line and not re.match(r"^This programme is (only )?offered", line, re.IGNORECASE)
            ]

    description = _join_paragraphs(lead)
    if description is None and "Study content" in lines:
        start = lines.index("Study content")
        content: list[str] = []
        for line in lines[start + 1 :]:
            if line in _RSU_SECTION_END:
                break
            content.append(line)
        description = _join_paragraphs(content)

    return {"degree_awarded_en": _degree(degree_lines), "description_en": excerpt(description)}


# ---------- LMA: lma.lv/en/studies/nozares/<slug> ----------

_LMA_LEVEL_WORD = {"bachelor": "bachelor", "master": "master", "doctoral": "doctor"}
_LMA_ABOUT_END = re.compile(r"^(ECTS course catalogue|CONTACTS|TUTORS|STUDENTS WORKS)\b", re.IGNORECASE)


def lma_details(body: str, title: str, level: str) -> Details:
    """Страница специализации LMA — одна на бакалавриат и магистратуру.

    «DEGREE TO BE OBTAINED» — степени через «/»: «Bachelor of … / Master of
    …»; берётся та, что соответствует уровню программы. Описание — раздел
    «ABOUT» до каталога курсов или контактов; оно общее для обоих уровней.
    """
    lines = _lines(body)
    upper = [line.upper() for line in lines]

    degree: str | None = None
    facts_end = 0  # строка, после которой начинается содержимое страницы
    if "DURATION OF STUDY" in upper:
        facts_end = upper.index("DURATION OF STUDY")
    if "DEGREE TO BE OBTAINED" in upper:
        index = upper.index("DEGREE TO BE OBTAINED")
        facts_end = index
        value = next((line for line in lines[index + 1 :] if line), "")
        parts = [part.strip() for part in value.split("/") if part.strip()]
        word = _LMA_LEVEL_WORD.get(level, level)
        matching = [part for part in parts if word in part.lower()]
        if matching:
            degree = _degree(matching)
        elif len(parts) == 1 and not any(w in parts[0].lower() for w in _LMA_LEVEL_WORD.values()):
            # одна степень без слова уровня — относится к единственному уровню страницы
            degree = _degree(parts)

    description: str | None = None
    # «About» есть и в меню сайта (Structure / Our people / …) — нужен раздел
    # страницы, а он идёт после блока фактов. Без блока фактов не угадываем.
    if facts_end and "ABOUT" in upper[facts_end:]:
        index = upper.index("ABOUT", facts_end)
        about: list[str] = []
        for line in lines[index + 1 :]:
            if _LMA_ABOUT_END.match(line):
                break
            about.append(line)
        description = _join_paragraphs(about)

    return {"degree_awarded_en": degree, "description_en": excerpt(description)}


# source_key -> (короткое имя для командной строки, разборщик)
PARSERS: dict[str, tuple[str, Callable[[str, str, str], Details]]] = {
    "sources.rsu": ("rsu", rsu_details),
    "sources.lma": ("lma", lma_details),
}


def main(apply: bool, everything: bool, limit: int | None, only: set[str], skip_local: bool) -> None:
    from dotenv import load_dotenv
    from playwright.sync_api import sync_playwright

    import polite
    from db import get_service_client

    load_dotenv()
    polite.install()
    client = get_service_client()
    now = datetime.now(timezone.utc)

    keys = [
        key
        for key, (name, _) in PARSERS.items()
        if (not only or name in only) and not (skip_local and name in LOCAL_ONLY)
    ]
    rows = (
        client.table("programme")
        .select("id, slug, degree_level, source_url, source_key, details_extracted_at")
        .in_("source_key", keys)
        .execute()
        .data
    )
    # одна страница может описывать несколько программ (LMA: бакалавриат и
    # магистратура специализации) — открываем её один раз
    by_url: dict[str, list[dict]] = {}
    for row in rows:
        if row["source_url"] and (everything or is_due(row["details_extracted_at"], now)):
            by_url.setdefault(row["source_url"], []).append(row)
    urls = sorted(by_url)[:limit] if limit else sorted(by_url)
    print(
        f"источники: {', '.join(PARSERS[key][0] for key in keys) or '—'}; программ: {len(rows)}; "
        f"страниц к обходу: {len(urls)}" + ("" if apply else " (сухой прогон — запись только с --apply)")
    )

    written = 0
    empty = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for url in urls:
            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(700)
                body = page.locator("body").inner_text()
                heading = page.locator("h1").first
                title = heading.inner_text().strip() if heading.count() > 0 else ""
            except Exception as exc:  # noqa: BLE001
                print(f"ОШИБКА {url}: {type(exc).__name__}: {exc}")
                continue

            for row in by_url[url]:
                details = PARSERS[row["source_key"]][1](body, title, row["degree_level"])
                if not any(details.values()):
                    empty += 1
                    print(f"ПУСТО {row['slug']} ({url})")
                    continue
                description = details["description_en"] or ""
                print(
                    f"{row['slug']}: degree={details['degree_awarded_en']!r}; "
                    f"description={len(description)} chars: {description[:90]!r}"
                )
                if apply:
                    # None пишется явно: эти колонки у таких программ заполняет
                    # только этот скрипт, и после правки разборщика прежнее
                    # значение должно исчезнуть (как в enrich_lu_details.py).
                    update: dict[str, object] = dict(details)
                    update["details_source_url"] = url
                    update["details_extracted_at"] = now.isoformat()
                    client.table("programme").update(update).eq("id", row["id"]).execute()
                    written += 1
        browser.close()

    print(polite.report_and_reset())
    print(f"записано программ: {written}; пустых: {empty}")


def selftest() -> None:
    rsu_page = "\n".join(
        [
            "Galvenā izvēlne",
            "Biomedicine",  # то же название в меню — не начало описания
            "Breadcrumb",
            "Study programme",
            "Biomedicine",
            "The programme develops a deep understanding and competences in the core aspects of biomedicine.",
            "This programme is only offered in Latvian.",
            "Programme Fact File",
            "Study direction:",
            "Life Sciences",
            "Professional Master’s study programme",
            "accredited until 20.12.2029.",
            "Degree conferred / qualification obtained:",
            "Master's degree in Biomedicine",
            "Language: Latvian",
            "ECTS: 120",
            "Study content",
            "The programme will equip you with the theoretical knowledge and practical skills needed for science.",
            "Learning methods",
            "RSU provides students with a comprehensive study process.",
        ]
    )
    details = rsu_details(rsu_page, "Biomedicine", "master")
    assert details["degree_awarded_en"] == "Master's degree in Biomedicine", details
    assert details["description_en"] == (
        "The programme develops a deep understanding and competences in the core aspects of biomedicine."
    ), details["description_en"]

    # нет вступления — берётся «Study content», но не «Learning methods»
    no_lead = rsu_page.replace(
        "The programme develops a deep understanding and competences in the core aspects of biomedicine.\n", ""
    )
    details = rsu_details(no_lead, "Biomedicine", "master")
    assert details["description_en"].startswith("The programme will equip you"), details["description_en"]
    assert "RSU provides" not in details["description_en"]

    # две строки степени — через «; »; цифра (длительность) заканчивает значение
    two = "Degree conferred / qualification obtained:\nBachelor's degree in Health Care\nNurse\n4 years\n"
    assert rsu_details(two, "X", "bachelor")["degree_awarded_en"] == "Bachelor's degree in Health Care; Nurse"
    assert rsu_details("nothing here", "X", "bachelor") == {"degree_awarded_en": None, "description_en": None}
    comma = "Degree conferred / qualification obtained:\nsports coach,\nFitness Instructor\nLanguage: Latvian\n"
    assert rsu_details(comma, "X", "college")["degree_awarded_en"] == "sports coach; Fitness Instructor"
    latvian = "Degree conferred / qualification obtained:\nmaģistra grāds digitālās stratēģijas vadībā\nLanguage: Latvian\n"
    assert rsu_details(latvian, "X", "master")["degree_awarded_en"] is None, "латышский текст — не в английское поле"

    lma_page = "\n".join(
        [
            "About",  # пункт меню сайта — не раздел страницы
            "Structure",
            "Our people",
            "Current projects, documents, procurements, photo galleries and other menu items of the site",
            "CERAMICS",
            "DURATION OF STUDY",
            "Bachelor 4 years / Master 2 years / Full-time",
            "DEGREE TO BE OBTAINED",
            "Bachelor of Humanities in Visual Plastic Arts / Master of Humanities in Visual Plastic Arts",
            "ON WEB",
            "ABOUT",
            "The Department of Ceramics provides students with a comprehensive understanding of ceramic materials.",
            "Students and the teaching staff are actively involved in symposiums.",
            "ECTS course catalogue I (SPRING) SEMESTER:",
            "BA level 2nd year",
            "CONTACTS",
            "Ainārs Rimicāns",
        ]
    )
    bachelor = lma_details(lma_page, "", "bachelor")
    master = lma_details(lma_page, "", "master")
    assert bachelor["degree_awarded_en"] == "Bachelor of Humanities in Visual Plastic Arts"
    assert master["degree_awarded_en"] == "Master of Humanities in Visual Plastic Arts"
    assert bachelor["description_en"] == master["description_en"], "описание общее для уровней"
    assert bachelor["description_en"].startswith("The Department of Ceramics"), bachelor["description_en"]
    assert "Structure" not in bachelor["description_en"], "меню сайта в описание не попадает"
    assert "BA level" not in bachelor["description_en"] and "Rimicāns" not in bachelor["description_en"]
    assert "\n\nStudents and the teaching staff" in bachelor["description_en"]

    # страница только магистратуры: степень бакалавра не подставляется
    ma_only = lma_page.replace("Bachelor of Humanities in Visual Plastic Arts / ", "")
    assert lma_details(ma_only, "", "bachelor")["degree_awarded_en"] is None
    assert lma_details(ma_only, "", "master")["degree_awarded_en"] == "Master of Humanities in Visual Plastic Arts"
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    args = sys.argv[1:]
    if "--selftest" in args:
        selftest()
    else:
        limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
        names = {arg for arg in args if not arg.startswith("--") and not arg.isdigit()}
        if "--local" in args:
            names |= {name for name, _ in PARSERS.values() if name in LOCAL_ONLY}
        main(
            apply="--apply" in args,
            everything="--all" in args,
            limit=limit,
            only=names,
            skip_local="--skip-local" in args,
        )
