"""Эстония: правило конкурса из текста условий SAIS — пока у бакалавриата и
цельного обучения Тартуского университета и TalTech (docs/PLAN-ESTONIA.md,
раздел 9; магистратуру разборщик тоже понял бы, но формулировки её страниц
не проверялись).

Текст условий («Vastuvõtukriteeriumid») и ссылку на страницу программы
сохраняет ee_load_admission_details.py; здесь он разбирается (ee_rules.py)
и записывается в ee_admission.rule. У Тартуского университета пороги
(«для подачи не меньше 66», «место гарантирует балл выше 80») и надбавка за
широкую математику стоят не в SAIS, а на странице программы ut.ee, надбавка
за медаль — на общей странице ut.ee о подсчёте баллов; они читаются здесь же.

Страница программы ut.ee показывает условия одного года: в декабре вуз
меняет их на следующий. Поэтому правило прошедшего конкурса не
перечитывается (как и условия в ee_load_admission_details.py): иначе к
конкурсу 2026 года приписались бы пороги 2027-го. Перечитываются правила,
которые ещё не разбирались, и правила конкурсов, срок которых не прошёл.

Одна страница ut.ee бывает у нескольких конкурсов (право: дневное обучение
в Тарту и в Таллине, обучение сессиями в Таллине). Если формы обучения у
них разные, гарантирующий порог не берётся ни для одного: на странице он
относится к одной из форм, и к какой — разборщик не знает.

Правило — факт без подтверждения человеком, сайт показывает его с пометкой
«извлечено автоматически» (решение владельца 2026-10-11).

Сначала должны пройти сроки и условия конкурса:
  python src/ee_load_admissions.py --apply
  python src/ee_load_admission_details.py --apply

Колонки — миграция 20261015120000_ee_admission_rule.sql.

Запуск:
  python src/ee_load_rules.py --selftest
  python src/ee_load_rules.py            # разобрать и показать, без записи
  python src/ee_load_rules.py --apply
  python src/ee_load_rules.py --apply --all   # перечитать и прошедшие конкурсы
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

import ee_rules

UT_HOSTS = {"ut.ee", "www.ut.ee"}
UT_POINTS_URL = "https://ut.ee/et/sisu/punktisumma-ja-pingeread"
SUPPORTED = {"ut", "taltech"}
LEVELS = {"bachelor", "integrated"}


def is_ut_page(url: str | None) -> bool:
    """Читаем только страницы самого вуза: ссылка взята со страницы SAIS."""
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in UT_HOSTS


def drop_shared_guarantee(pages: dict[str, dict], forms_by_url: dict[str, set]) -> list[str]:
    """Убрать гарантирующий порог у страниц, на которые ссылаются конкурсы
    с разной формой обучения. Возвращает адреса таких страниц."""
    shared = []
    for url, page in pages.items():
        if len(forms_by_url.get(url, set())) > 1 and page["guarantee_min"] is not None:
            pages[url] = {**page, "guarantee_min": None}
            shared.append(url)
    return shared


def _selftest() -> None:
    ee_rules._selftest()
    assert is_ut_page("https://ut.ee/et/oppekavad/informaatika")
    assert is_ut_page("https://www.ut.ee/et/oppekavad/informaatika")
    assert not is_ut_page("http://ut.ee/et/oppekavad/informaatika")
    assert not is_ut_page("https://taltech.ee/informaatika") and not is_ut_page(None)
    assert not is_ut_page("https://ut.ee.example.com/x")
    pages = {
        "https://ut.ee/law": {"apply_min": 66, "guarantee_min": 93, "wide_math_bonus": 16},
        "https://ut.ee/cs": {"apply_min": 66, "guarantee_min": 80, "wide_math_bonus": 16},
    }
    shared = drop_shared_guarantee(
        pages, {"https://ut.ee/law": {"päevane õpe", "sessioonõpe"}, "https://ut.ee/cs": {"päevane õpe"}}
    )
    assert shared == ["https://ut.ee/law"]
    assert pages["https://ut.ee/law"] == {"apply_min": 66, "guarantee_min": None, "wide_math_bonus": 16}
    assert pages["https://ut.ee/cs"]["guarantee_min"] == 80
    print("ee_load_rules selftest: ok")


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

    client = get_service_client()
    stored = fetch_all(
        lambda: client.table("ee_admission")
        .select(
            "programme_id, admission_id, closes_at, study_form, criteria_text, info_url, rule, rule_extracted_at, "
            "programme!inner(degree_level, university!inner(slug))"
        )
        .not_.is_("criteria_text", "null")
        .order("programme_id")
    )
    # одна запись на конкурс: у нескольких программ бывает общий конкурс
    admissions: dict[int, dict] = {}
    for row in stored:
        slug = row["programme"]["university"]["slug"]
        if slug in SUPPORTED and row["programme"]["degree_level"] in LEVELS:
            admissions.setdefault(row["admission_id"], {**row, "slug": slug})

    now = datetime.now(timezone.utc).isoformat()
    todo = {
        admission_id: row
        for admission_id, row in admissions.items()
        if "--all" in args or row["rule_extracted_at"] is None or (row["closes_at"] or "") >= now
    }
    print(f"конкурсов бакалавриата ТÜ и TalTech с условиями: {len(admissions)} | к разбору: {len(todo)}")

    ut_urls = sorted({row["info_url"] for row in todo.values() if row["slug"] == "ut" and is_ut_page(row["info_url"])})
    forms_by_url: dict[str, set] = {}
    for row in admissions.values():
        if row["slug"] == "ut" and row["info_url"]:
            forms_by_url.setdefault(row["info_url"], set()).add(row["study_form"])

    pages: dict[str, dict] = {}
    failed_pages: list[str] = []
    medal_bonus = None
    if ut_urls:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(locale="et-EE")
            for url in [UT_POINTS_URL, *ut_urls]:
                try:
                    response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    if response is None or response.status != 200:
                        raise RuntimeError(f"ответ {response.status if response else 'пустой'}")
                    text = page.inner_text("body")
                    if url == UT_POINTS_URL:
                        medal_bonus = ee_rules.parse_ut_medal(text)
                    else:
                        pages[url] = ee_rules.parse_ut_page(text)
                except Exception as exc:  # noqa: BLE001 — одна страница не останавливает остальные
                    failed_pages.append(f"{url}: {type(exc).__name__}: {str(exc)[:120]}")
            browser.close()
    shared = drop_shared_guarantee(pages, forms_by_url)

    rules: dict[int, tuple[dict | None, str | None]] = {}
    skipped: list[int] = []
    for admission_id, row in todo.items():
        if row["slug"] == "taltech":
            rules[admission_id] = (ee_rules.taltech_rule(row["criteria_text"]), None)
            continue
        url = row["info_url"] if is_ut_page(row["info_url"]) else None
        if url is not None and url not in pages:
            # страница вуза не прочиталась — правило не трогаем до следующего запуска
            skipped.append(admission_id)
            continue
        rules[admission_id] = (ee_rules.ut_rule(row["criteria_text"], pages.get(url), medal_bonus), url)

    by_result: Counter = Counter()
    for admission_id, (rule, url) in rules.items():
        slug = todo[admission_id]["slug"]
        by_result[(slug, "разобрано" if rule else "не разобрано")] += 1
        if rule and rule["model"] == "weighted":
            by_result[("ut", "с порогом для подачи")] += rule["apply_min"] is not None
            by_result[("ut", "с гарантирующим порогом")] += rule["guarantee_min"] is not None
            by_result[("ut", "считается по одним госэкзаменам")] += any(
                all("exam" in part for part in variant) for variant in rule["variants"]
            )
    print(f"надбавка за медаль (ut.ee): {medal_bonus}")
    for (slug, what), count in sorted(by_result.items()):
        print(f"  {slug:8} {what}: {count}")
    if shared:
        print("гарантирующий порог не взят — страница общая у разных форм обучения:", *shared, sep="\n  ")
    for admission_id, (rule, _) in sorted(rules.items()):
        if rule is None:
            print(f"  не разобрано: {admission_id} ({todo[admission_id]['slug']})")
    for line in failed_pages:
        print("  страница ut.ee не прочитана —", line)

    # Раньше разобранное правило стало пустым у заметной части конкурсов —
    # похоже, изменилась вёрстка или формулировки. Ничего не записываем.
    lost = [admission_id for admission_id, (rule, _) in rules.items() if rule is None and todo[admission_id]["rule"]]
    had = [admission_id for admission_id in rules if todo[admission_id]["rule"]]
    if had and len(lost) > max(3, len(had) * 0.2):
        print(f"\nРаньше разобранных правил стало пустыми {len(lost)} из {len(had)} — в базу ничего не записано.")
        sys.exit(2)
    if not apply:
        print("\nзаписи не было (добавьте --apply)")
        return
    for admission_id, (rule, url) in rules.items():
        execute(
            client.table("ee_admission")
            .update({"rule": rule, "rule_source_url": url if rule else None, "rule_extracted_at": now})
            .eq("admission_id", admission_id)
        )
    print(f"записано конкурсов: {len(rules)} | отложено (страница ut.ee не прочитана): {len(skipped)}")
    print(polite.report_and_reset())
    if failed_pages:
        sys.exit(1)


if __name__ == "__main__":
    main()
