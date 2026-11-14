"""Черновики требований к английскому — таблица english_requirement.

Продукт для иностранцев, шаг 4 (docs/PLAN-FOREIGNERS.md). Языковое требование —
поле правила 6 CLAUDE.md, поэтому скрипт пишет ТОЛЬКО ЧЕРНОВИКИ: verified_at
проставляет владелец в Studio. Уже подтверждённые строки не трогаются.
Храним IELTS и TOEFL iBT; остальные тесты — по ссылке на страницу вуза.

Источники (2026-11-14):
- РТУ: одно требование на бакалавриат и магистратуру,
  rtu.lv/en/studies/admission-1 («General admission requirements»);
- RSU: приложение 12 к правилам приёма на английские программы 2026/2027 (PDF);
- ЛУ: у каждой программы своё — страница программы на lu.lv ссылается на
  страницу приёма apply.lu.lv, там список тестов. Скрипт читает обе (через
  polite: robots.txt, задержка; у apply.lu.lv Crawl-delay 15 секунд —
  прогон по ЛУ идёт около 15 минут). Программа с несколькими страницами
  приёма и разными цифрами пропускается: какая цифра к какой подпрограмме,
  решает человек.
- RISEBA цифр на страницах программ не называет («English language skills»)
  — строк нет. Turība, TSI, ViA — вручную (robots.txt).

  python src/seed_english_requirements.py              # показать, что будет записано
  python src/seed_english_requirements.py --apply      # записать черновики
  python src/seed_english_requirements.py --only rtu   # один вуз (rtu, rsu, lu)
  python src/seed_english_requirements.py --only lu --lu-slugs philology-en,...  # только эти программы ЛУ
  python src/seed_english_requirements.py --selftest   # разбор ЛУ на образце, без сети и базы
"""

from __future__ import annotations

import html
import re
import sys

RTU_ADMISSION = "https://www.rtu.lv/en/studies/admission-1"
RSU_PROCEDURE = "https://www.rsu.lv/sites/default/files/imce/SSD/admissions_procedure_2026_2027_eng.pdf"

# Требования на весь уровень вуза (programme_id пустой). Цитаты — дословно.
UNIVERSITY_ROWS: list[dict] = [
    *(
        {
            "university": "rtu",
            "degree_level": level,
            "ielts_min": 5.5,
            "toefl_ibt_min": 72,
            "toefl_ibt_band": None,
            "note": "Or a letter that English was the medium of instruction for your whole previous study level.",
            "source_url": RTU_ADMISSION,
            "source_excerpt": "IELTS minimum overall grade of 5.5 TOEFL iBT* minimum 72",
        }
        for level in ("bachelor", "master")
    ),
    *(
        {
            "university": "rsu",
            "degree_level": level,
            "ielts_min": 6.0,
            "toefl_ibt_min": 80,
            "toefl_ibt_band": None,
            "note": "Test taken within the last 5 years.",
            "source_url": RSU_PROCEDURE,
            "source_excerpt": "1 IELTS 6.0 2 TOEFL iBT 80",
        }
        for level in ("bachelor", "master")
    ),
]


def page_lines(page: str) -> list[str]:
    """HTML → строки текста: так на странице ЛУ каждый тест — своя строка."""
    page = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"(?i)<(br|/p|/li|/h\d|/tr|/div)[^>]*>", "\n", page)
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    lines = [re.sub(r"[ \t\xa0]+", " ", line).strip() for line in text.split("\n")]
    return [line for line in lines if line]


IELTS = re.compile(r"^IELTS\s*[–:\-]+\s*at least(?: score)?\s*(\d(?:[.,]\d+)?)", re.I)
TOEFL = re.compile(r"^TOEFL\s*iBT\s*[–:\-]+\s*at least(?: score)?\s*(\d{2,3})\b", re.I)
TOEFL_BAND = re.compile(r"minimum score of (\d(?:[.,]\d)?) for tests taken after 21 January 2026", re.I)


def parse_lu_course(page: str) -> dict | None:
    """IELTS и TOEFL iBT со страницы apply.lu.lv; None, если нет ни одного."""
    ielts = toefl = band = None
    excerpt: list[str] = []
    for line in page_lines(page):
        if ielts is None and (match := IELTS.search(line)):
            ielts = float(match.group(1).replace(",", "."))
            excerpt.append(line)
        elif toefl is None and (match := TOEFL.search(line)):
            toefl = int(match.group(1))
            if band_match := TOEFL_BAND.search(line):
                band = float(band_match.group(1).replace(",", "."))
            excerpt.append(line)
    if ielts is None and toefl is None:
        return None
    return {"ielts_min": ielts, "toefl_ibt_min": toefl, "toefl_ibt_band": band, "source_excerpt": " … ".join(excerpt)}


def lu_course_links(page: str) -> list[str]:
    return sorted(set(re.findall(r"https://apply\.lu\.lv/courses/course/[\w\-]+", page)))


# Страницы приёма, на которые страница программы на lu.lv не ссылается
# (найдены по карте apply.lu.lv 2026-11-14). Добавляются к ссылкам со
# страницы программы; у English Studies вторая подпрограмма называет другой
# TOEFL (72 против 100) — программа уходит в «решает человек».
LU_EXTRA_COURSES: dict[str, list[str]] = {
    "philology-en": ["22", "28", "114"],
    "linguistics-literature-and-regional-culture-studies-en-master": ["39", "43", "115"],
    "european-studies-and-economic-diplomacy-en-1-year-master": ["141"],
    "industrial-engineering-and-management-en": ["110"],
    "english-studies-master": ["156"],
}


def lu_rows(fetch, programmes: list[dict], only_slugs: set[str] | None = None) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    skipped: list[str] = []
    for programme in programmes:
        url = programme["source_url"] or ""
        if programme["language_of_instruction"] != "en" or not url.startswith("https://www.lu.lv/en/"):
            continue
        if only_slugs is not None and programme["slug"] not in only_slugs:
            continue
        extra = [f"https://apply.lu.lv/courses/course/{course}" for course in LU_EXTRA_COURSES.get(programme["slug"], [])]
        try:
            links = sorted(set(lu_course_links(fetch(url)) + extra))
        except Exception as exc:  # noqa: BLE001 — страница пропала: в журнал, не падаем
            if not extra:
                skipped.append(f"{programme['slug']}: страница не открылась ({type(exc).__name__})")
                continue
            links = extra
        if not links:
            skipped.append(f"{programme['slug']}: нет ссылки на apply.lu.lv")
            continue
        parsed: list[tuple[str, dict]] = []
        for link in links:
            try:
                found = parse_lu_course(fetch(link))
            except Exception as exc:  # noqa: BLE001
                skipped.append(f"{programme['slug']}: {link} не открылась ({type(exc).__name__})")
                continue
            if found:
                parsed.append((link, found))
        values = {(p["ielts_min"], p["toefl_ibt_min"], p["toefl_ibt_band"]) for _, p in parsed}
        if not parsed:
            skipped.append(f"{programme['slug']}: на странице приёма нет IELTS и TOEFL iBT")
            continue
        if len(values) > 1:
            skipped.append(f"{programme['slug']}: у подпрограмм разные цифры {sorted(values, key=str)} — решает человек")
            continue
        link, found = parsed[0]
        rows.append({
            "university": "lu",
            "degree_level": programme["degree_level"],
            "programme_id": programme["id"],
            "programme_slug": programme["slug"],
            "note": None,
            "source_url": link,
            **found,
        })
    return rows, skipped


SAMPLE_LU = """<ul><li>LanguageCert International ESOL at least Level Communicator C1 (Written and Spoken exams);</li>
<li>TOEFL IBT &ndash; at least 100 is required for tests taken on or before 21 January 2026, or a minimum score of 5 for
tests taken after 21 January 2026.</li><li>TOEFL Essential &ndash; at least 10 points</li>
<li>IELTS &ndash; at least score 7.00</li></ul>"""


def selftest() -> None:
    parsed = parse_lu_course(SAMPLE_LU.replace("\n", " "))
    assert parsed and parsed["ielts_min"] == 7.0 and parsed["toefl_ibt_min"] == 100 and parsed["toefl_ibt_band"] == 5.0, parsed
    assert "TOEFL Essential" not in parsed["source_excerpt"], parsed
    old = parse_lu_course("<li>TOEFL IBT : at least 80 for tests taken on or before 21 January 2026, or a minimum score of 4 "
                          "for tests taken after 21 January 2026.</li><li>IELTS &ndash; at least score 6.00</li>")
    assert old and (old["ielts_min"], old["toefl_ibt_min"], old["toefl_ibt_band"]) == (6.0, 80, 4.0), old
    plain = parse_lu_course("<li>TOEFL IBT &ndash; at least score 80</li><li>IELTS &ndash; at least score 6.00</li>")
    assert plain and plain["toefl_ibt_band"] is None and plain["toefl_ibt_min"] == 80, plain
    assert parse_lu_course("<p>English language skills</p>") is None
    assert lu_course_links('<a href="https://apply.lu.lv/courses/course/37-master-x">a</a><a href="https://apply.lu.lv/courses/course/37-master-x">') == [
        "https://apply.lu.lv/courses/course/37-master-x"
    ]
    for row in UNIVERSITY_ROWS:
        assert row["ielts_min"] is not None or row["toefl_ibt_min"] is not None, row
        # обе цифры — из цитаты: опечатка в одном из двух мест
        excerpt = row["source_excerpt"]
        assert f"IELTS {row['ielts_min']:g}" in excerpt or f"grade of {row['ielts_min']:g}" in excerpt, row
        assert str(row["toefl_ibt_min"]) in excerpt, row
    print("selftest ok")


def main(apply: bool, only: str | None, only_slugs: set[str] | None = None) -> None:
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute
    from polite import fetch_text

    load_dotenv()
    client = get_service_client()
    universities = {row["slug"]: row["id"] for row in execute(client.table("university").select("id, slug")).data}
    try:
        existing = {
            (row["university_id"], row["degree_level"], row["programme_id"]): row
            for row in execute(
                client.table("english_requirement").select("university_id, degree_level, programme_id, verified_at")
            ).data
        }
    except Exception as exc:  # noqa: BLE001
        if apply:
            raise SystemExit(f"english_requirement не читается ({exc}) — сначала примените миграцию в Studio") from exc
        print("english_requirement ещё нет в базе (миграция не применена) — показываю черновики без сверки\n")
        existing = {}

    drafts: list[dict] = [dict(row, programme_id=None) for row in UNIVERSITY_ROWS if not only or row["university"] == only]
    skipped: list[str] = []
    if not only or only == "lu":
        programmes = execute(
            client.table("programme")
            .select("id, slug, source_url, degree_level, language_of_instruction")
            .eq("university_id", universities["lu"])
        ).data
        lu, skipped = lu_rows(fetch_text, programmes, only_slugs)
        drafts += lu

    written = kept = 0
    for draft in drafts:
        row = {k: v for k, v in draft.items() if k not in ("university", "programme_slug")}
        row["university_id"] = universities[draft["university"]]
        prior = existing.get((row["university_id"], row["degree_level"], row["programme_id"]))
        if prior and prior["verified_at"]:
            kept += 1
            continue
        target = draft.get("programme_slug") or "весь уровень"
        print(
            f"{draft['university']:4} {row['degree_level']:9} {target:55} IELTS {row['ielts_min']}  "
            f"TOEFL iBT {row['toefl_ibt_min']}" + (f" / {row['toefl_ibt_band']}" if row["toefl_ibt_band"] else "")
        )
        if apply:
            # verified_at/verified_by в записи нет — их ставит только человек
            execute(client.table("english_requirement").upsert(row, on_conflict="university_id,degree_level,programme_id"))
            written += 1
    if skipped:
        print(f"\nпропущено {len(skipped)}:")
        for line in skipped:
            print(f"  {line}")
    print(f"\nчерновиков: {len(drafts)}; уже подтверждено (не трогаю): {kept}; записано: {written}"
          + ("" if apply else " (сухой прогон — запись только с --apply)"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
        if only is not None and only not in ("rtu", "rsu", "lu"):
            raise SystemExit("--only: rtu, rsu или lu")
        # --lu-slugs a,b — только эти программы ЛУ (дозапись без 15-минутного прогона)
        slugs = set(sys.argv[sys.argv.index("--lu-slugs") + 1].split(",")) if "--lu-slugs" in sys.argv else None
        main("--apply" in sys.argv, only, slugs)
