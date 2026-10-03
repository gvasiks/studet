"""Степень и описание программы — со страницы программы на сайте самого вуза.

Порция 3 работы «диплом и описание для остальных программ» (2026-10-03).
Для вузов, у которых в каталоге только английские названия программ (в
NIID их по названию не найти) и чьи собственные страницы содержат и
степень, и описание на английском. ЛУ живёт в отдельном скрипте
(enrich_lu_details.py) — он появился раньше; новые вузы добавляются сюда.

  степень  -> programme.degree_awarded_en
  описание -> programme.description_en (начало, как у NIID и ЛУ)

Сейчас: RSU, LMA, TSI, EKA, BSA, DU, LKA, LBTU, RGSL, RISEBA, RNU, Turība, SSE Riga.

Как добавить вуз: написать функцию-разборщик `(текст страницы, заголовок h1,
уровень программы) -> {"degree_awarded_en", "description_en"}` — чистую, с
примером в selftest() — и внести её в PARSERS под ключом source_key. Сеть и
база у всех общие. Разборщик может вернуть и необязательный ключ
"accreditation_valid_until" (ISO-дата, так делает EKA): он записывается,
только когда найден, — это поле заполняют и сборщики каталога.

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


def _field(lines: list[str], *labels: str) -> str | None:
    """Значение поля «Подпись: значение» или «Подпись<TAB>значение».

    Подпись сравнивается целиком и без учёта регистра («Degree» не совпадёт
    с «Degree to be obtained»); вариантов подписи может быть несколько — на
    одном сайте страницы подписаны по-разному. Если после подписи пусто —
    берётся следующая строка (так у RISEBA).
    """
    wanted = {label.lower() for label in labels}
    for index, line in enumerate(lines):
        match = re.match(r"([^:\t]*)[:\t](.*)", line)
        if not match or match.group(1).strip().lower() not in wanted:
            continue
        value = match.group(2).strip()
        return value or next((candidate for candidate in lines[index + 1 : index + 3] if candidate), None)
    return None


def _first_paragraphs(lines: list[str]) -> list[str]:
    """Первые абзацы текста, идущего после названия или блока фактов.

    Заголовком считается короткая строка или строка с двоеточием в конце;
    так же отбрасывается пункт списка — строка со строчной буквы.
    Заголовки в начале пропускаются; первый заголовок после абзаца — конец
    описания (дальше идут списки, учебный план, контакты).
    """
    lead: list[str] = []
    for line in lines:
        if not line:
            continue
        if len(line) < MIN_DESCRIPTION_LENGTH or line.endswith(":") or line[0].islower():
            if lead:
                break
            continue
        if line not in lead:
            lead.append(line)
    return lead


def _after_table(lines: list[str]) -> list[str]:
    """Строки после таблицы фактов (её строки — «Подпись<TAB>значение»)."""
    rows = [index for index, line in enumerate(lines) if "\t" in line]
    if not rows:
        return []
    end = rows[0]
    for row in rows[1:]:
        # значение ячейки бывает в две строки (DU: «Language») и между
        # строками бывают пустые — небольшой разрыв таблицу не кончает
        if row - end > 4:
            break
        end = row
    return lines[end + 1 :]


def _details(degree_lines: list[str | None], lead: list[str], accreditation: str | None = None) -> Details:
    # точка в конце слова — опечатка сайта («…hospitality business.»);
    # сокращения («Ph.D.», «Mg.sc.ing.») не трогаем
    parts = [re.sub(r"(?<=[a-z]{4})\.$", "", line.strip()) for line in degree_lines if line]
    details: Details = {
        "degree_awarded_en": _degree(parts),
        "description_en": excerpt(_join_paragraphs(lead)),
    }
    if accreditation:
        details["accreditation_valid_until"] = accreditation
    return details


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


# ---------- TSI: tsi.lv/study_programmes/<slug>/ ----------


def tsi_details(body: str, title: str, level: str) -> Details:
    """Страница программы TSI.

    У сайта два вида страниц.

    Новый: степень — значение поля блока «Key Data», чья подпись начинается с
    «AWARDED» («AWARDED ACADEMIC DEGREE»…), на следующей строке. У программ
    двойного диплома значений два, каждое вида «ВУЗ: степень» — берутся оба.
    Описание — абзац между названием программы и кнопкой «Apply Now».
    Название встречается на странице несколько раз (меню, хлебные крошки),
    поэтому берётся то вхождение, за которым в пределах нескольких строк
    идёт «Apply Now».

    Старый (докторантура и одна магистратура): степень — в той же строке,
    «Awarded academic degree: …»; описание — абзацы под заголовком
    «About the Programme» до следующего заголовка.
    """
    lines = _lines(body)

    degree_lines: list[str] = []
    for index, line in enumerate(lines):
        if not line.upper().startswith("AWARDED"):
            continue
        inline = line.partition(":")[2].strip()
        if inline:
            values = [inline]
        else:
            following = [candidate for candidate in lines[index + 1 : index + 6] if candidate]
            values = following[:1]
            # вторая строка — только у двойного диплома: обе вида «ВУЗ: степень»
            if len(following) > 1 and ": " in following[0] and ": " in following[1]:
                values.append(following[1])
        for value in values:
            if value not in degree_lines:
                degree_lines.append(value)

    lead: list[str] = []
    if title:
        for index, line in enumerate(lines):
            if line != title:
                continue
            between: list[str] = []
            for candidate in lines[index + 1 : index + 8]:
                if candidate == title:
                    break  # ниже есть вхождение ближе к кнопке — возьмём его
                if candidate.startswith("Apply Now"):
                    lead = between
                    break
                if candidate:
                    between.append(candidate)
            if lead:
                break

    if not lead:  # страница старого вида
        for index, line in enumerate(lines):
            if line.lower() != "about the programme":
                continue
            for candidate in lines[index + 1 :]:
                if not candidate:
                    continue
                # короткая строка или строка с двоеточием в конце — заголовок
                # следующего раздела или начало списка
                if candidate.endswith(":") or len(candidate) < MIN_DESCRIPTION_LENGTH:
                    break
                lead.append(candidate)
            if lead:
                break

    return {"degree_awarded_en": _degree(degree_lines), "description_en": excerpt(_join_paragraphs(lead))}


# ---------- EKA: augstskola.lv/?parent=<id>&lng=eng ----------

_MONTHS = {
    name: number
    for number, name in enumerate(
        ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
         "november", "december"],
        start=1,
    )
}


# «accredited until July 1, 2027», «accredited till August 26th, 2027»,
# «Accredited until: May 27, 2027», «Accredited until<TAB>31 December 2027»,
# «is accreditate for 6 years till June 20, 2030» (так у BSA).
_ACCREDITED_UNTIL = re.compile(
    r"accredit\w*\b[^.\n]{0,40}?\b(?:until|till)\b:?\s+"
    r"(?:([A-Za-z]+),?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})|(\d{1,2})\s+([A-Za-z]+)\s+(\d{4}))",
    re.IGNORECASE,
)


def accredited_until(text: str) -> str | None:
    """«…accredited until July 1, 2027.» -> «2027-07-01»; нет даты -> None."""
    match = _ACCREDITED_UNTIL.search(text)
    if not match:
        return None
    month_name, day, year = (
        (match.group(1), match.group(2), match.group(3))
        if match.group(1)
        else (match.group(5), match.group(4), match.group(6))
    )
    month = _MONTHS.get(month_name.lower())
    if month is None:
        return None
    try:
        return datetime(int(year), month, int(day)).date().isoformat()
    except ValueError:
        return None


def _page_accreditation(lines: list[str]) -> str | None:
    """Первая строка страницы, где назван срок аккредитации."""
    return next((found for found in map(accredited_until, lines) if found), None)


def eka_details(body: str, title: str, level: str) -> Details:
    """Страница программы EKA.

    Блок фактов — строки «Language: …», «Degree to Be Achieved: …»,
    «Accreditation: …». Описание — строки между названием программы
    (написано ПРОПИСНЫМИ над описанием) и строкой «Language:».
    """
    lines = _lines(body)

    degree_lines = [
        line.split(":", 1)[1].strip() for line in lines if line.lower().startswith("degree to be achieved:")
    ][:1]
    accreditation = next(
        (accredited_until(line) for line in lines if line.lower().startswith("accreditation:")), None
    )

    lead: list[str] = []
    language_index = next((i for i, line in enumerate(lines) if line.startswith("Language:")), None)
    if language_index is not None:
        # идём от «Language:» вверх до названия программы — строки из прописных букв
        start = language_index
        while start > 0:
            candidate = lines[start - 1]
            if candidate and candidate == candidate.upper() and any(ch.isalpha() for ch in candidate):
                break
            start -= 1
        if start > 0:  # название найдено; без него не угадываем, где начало описания
            lead = [line for line in lines[start:language_index] if line]

    return {
        "degree_awarded_en": _degree(degree_lines),
        "description_en": excerpt(_join_paragraphs(lead)),
        "accreditation_valid_until": accreditation,
    }


# ---------- Ещё девять вузов (2026-10-03) ----------
# У всех одна схема: степень (и квалификация, если названа отдельно) — из
# строки-поля, описание — первые абзацы после названия или блока фактов,
# срок аккредитации — если он назван на странице.


def bsa_details(body: str, title: str, level: str) -> Details:
    """BSA: bsa.edu.lv/index.php/en/<уровень>/<slug>.html"""
    lines = _lines(body)
    after_title = lines[lines.index(title) + 1 :] if title in lines else []
    # сразу под названием — строка о сроке аккредитации направления; в описание не идёт
    lead = _first_paragraphs([line for line in after_title if "accredit" not in line.lower()])
    return _details(
        [_field(lines, "Course Degree"), _field(lines, "Qualification to be obtained")],
        lead,
        _page_accreditation(lines),
    )


def du_details(body: str, title: str, level: str) -> Details:
    """DU: du.lv/en/studies/study-programmes/<уровень>/<slug>/"""
    lines = _lines(body)
    degree = _field(lines, "Obtainable Degree", "Obtainable Degree and Qualification", "Degree to be acquired")
    return _details([degree], _first_paragraphs(_after_table(lines)))


def lka_details(body: str, title: str, level: str) -> Details:
    """LKA: lka.edu.lv/en/studies/study-programmes/<уровень>/<slug>/

    Блок «Course Brief» — строки «Подпись: значение», последняя нужная —
    «Degree to be obtained». Описание — абзацы под первым заголовком
    ПРОПИСНЫМИ после неё (обычно «THE AIM AND OBJECTIVES OF THE STUDY
    PROGRAMME»); у докторантуры такого заголовка нет — тогда первый абзац
    после блока. Строки-факты в описание не идут, поиск кончается на
    подвале («Important shortcuts»).
    """
    lines = _lines(body)
    lead: list[str] = []
    degree_index = next(
        (index for index, line in enumerate(lines) if line.lower().startswith("degree to be obtained")), None
    )
    if degree_index is not None:
        end = lines.index("Important shortcuts") if "Important shortcuts" in lines else len(lines)
        region = [line for line in lines[degree_index + 1 : end] if not re.match(r"[^:]{3,45}: ", line)]
        heading = next(
            (
                index
                for index, line in enumerate(region)
                if len(line) >= 10 and line == line.upper() and any(ch.isalpha() for ch in line)
            ),
            None,
        )
        if heading is not None:
            lead = _first_paragraphs(region[heading + 1 :])
        elif "Profesors" in region:
            # без заголовков: описание — только абзац сразу под списком
            # вкладок (последняя — «Profesors», так на сайте). Если там
            # подзаголовок («Application procedure»), дальше идут правила
            # подачи, а не описание.
            after_tabs = [line for line in region[region.index("Profesors") + 1 :] if line]
            if after_tabs and len(after_tabs[0]) >= MIN_DESCRIPTION_LENGTH:
                lead = _first_paragraphs(after_tabs)
    degree = _field(lines, "Degree to be obtained")
    return _details([re.sub(r"^the\s+", "", degree) if degree else None], lead)


def lbtu_details(body: str, title: str, level: str) -> Details:
    """LBTU: llu.lv/en/<slug>. Описание — абзацы прямо над строкой «Degree:»."""
    lines = [line for line in _lines(body) if line]
    lead: list[str] = []
    degree_index = next((index for index, line in enumerate(lines) if line.startswith("Degree:")), None)
    if degree_index is not None:
        index = degree_index - 1
        while index >= 0 and len(lines[index]) >= MIN_DESCRIPTION_LENGTH and lines[index] != title:
            lead.insert(0, lines[index])
            index -= 1
    return _details([_field(lines, "Degree")], lead, _page_accreditation(lines))


def rgsl_details(body: str, title: str, level: str) -> Details:
    """RGSL: rgsl.edu.lv/programmes/<slug>"""
    lines = _lines(body)
    degree = _field(lines, "Degree", "Degree awarded")
    return _details([degree], _first_paragraphs(_after_table(lines)), _page_accreditation(lines))


def riseba_details(body: str, title: str, level: str) -> Details:
    """RISEBA: riseba.lv/en/program/<slug>/

    Описание — абзац между названием и блоком «General information».
    Строка «Programme degree:» есть не у всех программ.
    """
    lines = _lines(body)
    lead: list[str] = []
    if "General information" in lines:
        general = lines.index("General information")
        titles = [index for index in range(general) if lines[index] == title]
        if titles:
            lead = _first_paragraphs(lines[titles[-1] + 1 : general])
    return _details([_field(lines, "Programme degree")], lead, _page_accreditation(lines))


def rnu_details(body: str, title: str, level: str) -> Details:
    """RNU: rnu.lv/en/studies/study-programs/<уровень>/<slug>/

    Описание — под заголовком «PROGRAMME DESCRIPTION» («PROGRAM
    DESCRIPTION»); где его нет — первый абзац после кнопки «APPLY HERE!»
    (раздел «Goal»). Если там только список — описания нет.
    """
    lines = _lines(body)
    upper = [line.upper() for line in lines]
    start = next((index for index, line in enumerate(upper) if line in ("PROGRAMME DESCRIPTION", "PROGRAM DESCRIPTION")), None)
    if start is None:
        start = next((index for index, line in enumerate(upper) if line.startswith("APPLY HERE")), None)
    lead = _first_paragraphs(lines[start + 1 :]) if start is not None else []
    return _details(
        [_field(lines, "Degree to be awarded", "Degree Awarded"), _field(lines, "Qualifications", "Qualification")], lead
    )


def turiba_details(body: str, title: str, level: str) -> Details:
    """Turība: turiba.lv/en/admission/study-programs/<уровень>/<slug>

    Название стоит дважды: над блоком фактов и над описанием — нужно второе.
    """
    lines = _lines(body)
    titles = [index for index, line in enumerate(lines) if title and line == title]
    lead = _first_paragraphs(lines[titles[-1] + 1 :]) if titles else []
    return _details(
        [_field(lines, "DEGREE AWARDED"), _field(lines, "QUALIFICATION AWARDED")], lead, _page_accreditation(lines)
    )


def sse_details(body: str, title: str, level: str) -> Details:
    """SSE Riga: sseriga.edu/education/bachelor — одна программа, текст прозой."""
    lines = [line for line in _lines(body) if line]
    match = re.search(r"Graduate with a (Bachelor[’']s Degree in [A-Za-z ]+?)[,.]", body)
    lead: list[str] = []
    for index, line in enumerate(lines[:-1]):
        # название страницы есть и в меню — нужно то, за которым сразу идёт абзац
        if title and line == title and len(lines[index + 1]) >= MIN_DESCRIPTION_LENGTH:
            lead = [lines[index + 1]]
            break
    return _details([match.group(1) if match else None], lead)


# source_key -> (короткое имя для командной строки, разборщик)
PARSERS: dict[str, tuple[str, Callable[[str, str, str], Details]]] = {
    "sources.rsu": ("rsu", rsu_details),
    "sources.lma": ("lma", lma_details),
    "sources.tsi": ("tsi", tsi_details),
    "sources.eka": ("eka", eka_details),
    "sources.bsa": ("bsa", bsa_details),
    "sources.du": ("du", du_details),
    "sources.lka": ("lka", lka_details),
    "sources.lbtu": ("lbtu", lbtu_details),
    "sources.rgsl": ("rgsl", rgsl_details),
    "sources.riseba": ("riseba", riseba_details),
    "sources.rnu": ("rnu", rnu_details),
    "sources.turiba": ("turiba", turiba_details),
    "sources.sse_riga": ("sse", sse_details),
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
                # Срок аккредитации — необязательная находка разборщика (EKA).
                # Записывается, только когда найден: это поле заполняют и
                # сборщики, и стирать их значение пустотой нельзя.
                accreditation = details.pop("accreditation_valid_until", None)
                if not any(details.values()):
                    empty += 1
                    print(f"ПУСТО {row['slug']} ({url})")
                    continue
                description = details["description_en"] or ""
                print(
                    f"{row['slug']}: degree={details['degree_awarded_en']!r}; "
                    + (f"accreditation={accreditation}; " if accreditation else "")
                    + f"description={len(description)} chars: {description[:90]!r}"
                )
                if apply:
                    # None пишется явно: эти колонки у таких программ заполняет
                    # только этот скрипт, и после правки разборщика прежнее
                    # значение должно исчезнуть (как в enrich_lu_details.py).
                    update: dict[str, object] = dict(details)
                    if accreditation:
                        update["accreditation_valid_until"] = accreditation
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

    tsi_page = "\n".join(
        [
            "Study Programmes",
            "Aviation Engineering",  # пункт меню — за ним нет «Apply Now»
            "Key Data",
            "ENGINEERING FACULTY",
            "Aviation Engineering",
            "Study the technologies that keep aircraft safe and operational, from aerodynamics to airworthiness management.",
            "Apply Now →",
            "Explore Courses ↓",
            "KEY DATA",
            "PROGRAMME VOLUME ECTS (CP)",
            "240",
            "AWARDED ACADEMIC DEGREE",
            "BSc Engineering in Mechanical Engineering",
            "LOCATION",
            "TSI Campus, Riga",
        ]
    )
    details = tsi_details(tsi_page, "Aviation Engineering", "bachelor")
    assert details["degree_awarded_en"] == "BSc Engineering in Mechanical Engineering", details
    assert details["description_en"].startswith("Study the technologies that keep aircraft safe"), details
    assert "Key Data" not in details["description_en"]
    assert tsi_details("nothing", "X", "bachelor") == {"degree_awarded_en": None, "description_en": None}

    double = "AWARDED ACADEMIC DEGREE\nTSI: MSc Smart Electronic Systems and Robotics\nUWE Bristol: MSc Robotics and Artificial Intelligence\nLOCATION\nTSI Campus, Riga or online"
    assert (
        tsi_details(double, "", "master")["degree_awarded_en"]
        == "TSI: MSc Smart Electronic Systems and Robotics; UWE Bristol: MSc Robotics and Artificial Intelligence"
    )
    single = "AWARDED ACADEMIC DEGREE\nMSc Management\nLOCATION\nTSI Campus, Riga: main building"
    assert tsi_details(single, "", "master")["degree_awarded_en"] == "MSc Management", "вторая строка — не степень"

    old_page = "\n".join(
        [
            "Awarded academic degree: MSc Transport and Logistics",
            "In the frame of study project and master thesis students can specialize in:",
            "Urban Mobility",
            "Complete study program volume ECTS (CP): 120 and 90",
            "Director of the Programme",
            "About the Programme",
            "Transportation serves as a foundation for progress across all domains of human activity, ensuring the reliable supply of goods.",
            "The programme is designed on the knowledge and research of European-level experts in an intellectual environment.",
            "Competences acquired as a result of studying at the programme:",
            "perform the independent critical analysis, synthesis and evaluation of significant research tasks in engineering",
        ]
    )
    details = tsi_details(old_page, "Intelligent Transport and Smart Logistics", "master")
    assert details["degree_awarded_en"] == "MSc Transport and Logistics", details
    assert details["description_en"].startswith("Transportation serves as a foundation"), details
    assert details["description_en"].endswith("intellectual environment."), "список компетенций в описание не попадает"

    eka_page = "\n".join(
        [
            "Professional Bachelor Study Programme",
            "ACCOUNTING AND FINANCE MANAGEMENT",
            "Are numbers your language? Make it your career!",
            "Accounting and financial management is a profession that requires an understanding of a company's finances.",
            "Language: Latvian",
            "Degree to Be Achieved: Bachelor's degree in accounting and financial management",
            "Accreditation: Study programme is accredited until July 1, 2027.",
            "What will you learn?",
            "Accounting basics: Accounting for economic transactions.",
        ]
    )
    details = eka_details(eka_page, "", "bachelor")
    assert details["degree_awarded_en"] == "Bachelor's degree in accounting and financial management", details
    assert details["accreditation_valid_until"] == "2027-07-01", details
    assert details["description_en"].startswith("Are numbers your language? Make it your career!\n\nAccounting and"), details
    assert "ACCOUNTING AND FINANCE" not in details["description_en"], "название в описание не попадает"
    assert "What will you learn" not in details["description_en"]
    assert accredited_until("accredited until February 30, 2027") is None, "несуществующая дата"
    assert accredited_until("is licensed") is None
    assert accredited_until("Study direction is accredited till January 18, 2030.") == "2030-01-18"
    assert accredited_until("accredited until August 26th, 2027.") == "2027-08-26"
    # нет названия прописными над описанием — начало описания не угадываем
    assert eka_details("Some text\nLanguage: Latvian", "", "bachelor")["description_en"] is None

    long_a = "This programme will enable you to become a leader within established organizations by providing comprehensive knowledge."
    long_b = "The second paragraph continues the description and is long enough to be treated as a paragraph, not a heading."

    assert accredited_until("Accredited until: May 27, 2027") == "2027-05-27"
    assert accredited_until("Accredited until\t31 December 2027") == "2027-12-31"
    assert accredited_until('study Direction "X" is accreditate for 6 years till June 20, 2030') == "2030-06-20"
    assert accredited_until("The study program is accredited until August 5, 2027.") == "2027-08-05"
    assert accredited_until("Information on study programme accreditation") is None
    assert accredited_until('study Direction "Y" is accreditate for 6 years till October, 3, 2030') == "2030-10-03"
    assert _field(["Degree awarded\tBachelor in Social Science in Law"], "Degree", "Degree awarded") == "Bachelor in Social Science in Law"
    assert _first_paragraphs(["learning modern management and governance methodologies based on international experience in this field;"]) == []
    table = ["Language\tLatvian (for studies in Latvian);", "English (for studies in English)", "Amount (CP)\t180 ECTS CP", "After"]
    assert _after_table(table) == ["After"], "ячейка в две строки таблицу не кончает"
    assert _details(["Professional Bachelor degree in tourism and hospitality business.", "Travel Manager"], [])["degree_awarded_en"] == "Professional Bachelor degree in tourism and hospitality business; Travel Manager"
    assert _details(["Doctor of Science, Ph.D."], [])["degree_awarded_en"] == "Doctor of Science, Ph.D."

    assert _field(["Degree to be obtained: A"], "Degree") is None, "подпись сравнивается целиком"
    assert _field(["Degree\tBachelor in Social Science in Law"], "degree") == "Bachelor in Social Science in Law"
    assert _field(["Programme degree:", "Bachelor's Degree in Audiovisual Arts"], "Programme degree") == "Bachelor's Degree in Audiovisual Arts"
    assert _first_paragraphs(["Heading", long_a, long_b, "Next heading", long_a]) == [long_a, long_b]
    assert _first_paragraphs([long_a, "Tasks of the study programme and everything that follows after this long heading line:", long_b]) == [long_a]

    bsa_page = "\n".join(
        [
            "STUDIESADMISSIONABOUT US",
            "Entrepreneurship management",
            'According decisions by the Study Quality Commission from June 19, 2024 study Direction "MANAGEMENT" is accreditate for 6 years till June 20, 2030',
            "Advantages of the program",
            long_a,
            "Competencies acquired",
            long_b,
            "Course Degree: Professional Bachelor’s degree in Business Management",
            "Qualification to be obtained: Manager of an Enterprise",
            "Course Length: 4 years - Full-Time",
        ]
    )
    details = bsa_details(bsa_page, "Entrepreneurship management", "bachelor")
    assert details["degree_awarded_en"] == "Professional Bachelor’s degree in Business Management; Manager of an Enterprise", details
    assert details["description_en"] == long_a, details
    assert details["accreditation_valid_until"] == "2030-06-20", details

    du_page = "\n".join(
        [
            "Biology",
            "Faculty\tFaculty of Natural Sciences and Healthcare",
            "Obtainable Degree\tNatural Sciences Bachelor’s Degree in Biology",
            "Study course descriptions\tStudy course descriptions",
            "Aim of the study programme",
            long_a,
            "Tasks of the study programme:",
            long_b,
        ]
    )
    details = du_details(du_page, "Biology", "bachelor")
    assert details == {"degree_awarded_en": "Natural Sciences Bachelor’s Degree in Biology", "description_en": long_a}, details

    lka_page = "\n".join(
        [
            "Audiovisual Art",
            "Course Brief",
            "Language of study: Latvian",
            "Degree to be obtained: Bachelor of Arts in Audiovisual Art",
            "International mobility opportunities: Studies, internships and graduate internships within the ERASMUS + exchange programme",
            "Study Overview",
            "THE AIM AND OBJECTIVES OF THE STUDY PROGRAMME",
            long_a,
            "STUDENT PROFILE",
            long_b,
        ]
    )
    details = lka_details(lka_page, "Audiovisual Art", "bachelor")
    assert details == {"degree_awarded_en": "Bachelor of Arts in Audiovisual Art", "description_en": long_a}, details
    lka_doctoral = "\n".join(
        [
            "Course Brief",
            "THE PROGRAMME IS PROVIDED IN COLLABORATION WITH RIGA TECHNICAL UNIVERSITY",  # над фактами — не заголовок описания
            "Degree to be obtained: the Bachelor of Arts in Creative Industries",
            "Place of study: LAC (Riga, Ludzas Street 24); RTU Faculty of Engineering Economics and Management (Riga, Kalnciema Street 6)",
            "Programme description",
            "Handbook for the Development and Submission of Theoretical Research in Final Theses for Professional Doctoral Study Programs",
            "Profesors",
            long_b,
            "Important shortcuts",
            "National Film School of the Latvian Academy of Culture / Department of Audiovisual Art and something else",
        ]
    )
    details = lka_details(lka_doctoral, "", "doctoral")
    assert details == {"degree_awarded_en": "Bachelor of Arts in Creative Industries", "description_en": long_b}, details
    no_text = lka_doctoral.replace(long_b, "Profesors")
    assert lka_details(no_text, "", "bachelor")["description_en"] is None, "подвал сайта — не описание"
    rules = lka_doctoral.replace(long_b, "Application procedure\n" + long_b)
    assert lka_details(rules, "", "doctoral")["description_en"] is None, "под вкладками подзаголовок — это не описание"

    lbtu_page = "\n".join(
        [
            "About University",
            "Geoinformatics and Remote Sensing",
            long_a,
            "",
            "Degree: Master Degree in Geoinformatics and Remote Sensing (Mg.sc.ing.)",
            "Credits: 120 ECTS",
            "Accredited until: October 27, 2028",
            "Abstract",
            long_b,
        ]
    )
    details = lbtu_details(lbtu_page, "Geoinformatics and Remote Sensing", "master")
    assert details["degree_awarded_en"] == "Master Degree in Geoinformatics and Remote Sensing (Mg.sc.ing.)", details
    assert details["description_en"] == long_a, details
    assert details["accreditation_valid_until"] == "2028-10-27", details
    long_title = "Professional master study programme – Human Resource Management and Career Counselling"
    details = lbtu_details(lbtu_page.replace("Geoinformatics and Remote Sensing\n", long_title + "\n"), long_title, "master")
    assert details["description_en"] == long_a, "длинное название — не абзац описания"

    rgsl_page = "\n".join(
        [
            "LL.B.",
            "Degree\tBachelor in Social Science in Law",
            "Programme duration\t3 years",
            "Accredited until\t31 December 2027",
            long_a,
            long_b,
            "The bachelor programmes brochure is available here:",
            "Apply",
        ]
    )
    details = rgsl_details(rgsl_page, "", "bachelor")
    assert details["degree_awarded_en"] == "Bachelor in Social Science in Law", details
    assert details["description_en"] == long_a + "\n\n" + long_b, details
    assert details["accreditation_valid_until"] == "2027-12-31", details

    riseba_page = "\n".join(
        [
            "Programmes",
            "Architecture",
            "Academic bachelor’s programme 210 ECTS",
            long_a,
            "Apply",
            "General information",
            "Credit points:",
            "210 ECTS",
            "Programme degree:",
            "Bachelor's Degree in Architecture",
            "About the Programme",
            long_b,
        ]
    )
    details = riseba_details(riseba_page, "Architecture", "bachelor")
    assert details == {"degree_awarded_en": "Bachelor's Degree in Architecture", "description_en": long_a}, details
    without_degree = riseba_details(riseba_page.replace("Programme degree:", "Other:"), "Architecture", "bachelor")
    assert without_degree["degree_awarded_en"] is None and without_degree["description_en"] == long_a

    rnu_page = "\n".join(
        [
            "BUSINESS ADMINISTRATION",
            "PROGRAMME DESCRIPTION",
            long_a,
            "PROGRAMME OVERVIEW",
            "Degree to be awarded: Professional Bachelor of Business Administration",
            "Qualifications: Business Administrator",
            "During the conversation, you will be able to discuss study opportunities and ask any questions you have.",
            "APPLY HERE!",
            "Goal",
            long_b,
        ]
    )
    details = rnu_details(rnu_page, "BUSINESS ADMINISTRATION", "bachelor")
    assert details["degree_awarded_en"] == "Professional Bachelor of Business Administration; Business Administrator", details
    assert details["description_en"] == long_a, details
    no_heading = rnu_details(rnu_page.replace("PROGRAMME DESCRIPTION", "Intro"), "", "master")
    assert no_heading["description_en"] == long_b, "без заголовка — абзац после кнопки APPLY HERE!"

    turiba_page = "\n".join(
        [
            "BUSINESS ADMINISTRATION",
            "Professional Bachelor's Study Program",
            "DEGREE AWARDED: Professional Bachelor's Degree in Business Administration",
            "QUALIFICATION AWARDED: Company Manager",
            "INTERNSHIP: Companies of various sectors, Turība University Business incubator and other partner companies",
            "BUSINESS ADMINISTRATION",
            long_a,
            "The study program is accredited until August 5, 2027.",
            "LECTURE TIMES:",
        ]
    )
    details = turiba_details(turiba_page, "BUSINESS ADMINISTRATION", "bachelor")
    assert details["degree_awarded_en"] == "Professional Bachelor's Degree in Business Administration; Company Manager", details
    assert details["description_en"] == long_a, details
    assert details["accreditation_valid_until"] == "2027-08-05", details

    sse_page = "\n".join(
        [
            "BSc Programme",
            "Curriculum",
            "BSc Programme",
            long_a,
            "Bachelor's degree",
            "Graduate with a Bachelor’s Degree in Social Sciences in Economics, a valuable credential for your future goals.",
        ]
    )
    details = sse_details(sse_page, "BSc Programme", "bachelor")
    assert details == {"degree_awarded_en": "Bachelor’s Degree in Social Sciences in Economics", "description_en": long_a}, details
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
