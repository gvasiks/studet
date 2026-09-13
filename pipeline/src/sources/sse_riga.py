"""SSE Riga (Rīgas Ekonomikas augstskola / Stockholm School of Economics
in Riga) — единственная бакалаврская программа, без обхода листинга.

Проверено вручную в браузере 2026-09-13: sseriga.edu — не каталог, а
маркетинговый сайт с одной программой на весь бакалавриат ("Economics
and Business", 150 мест в год). Структурированного блока фактов на
странице нет (обычный текст), но фактов и так мало и они однозначны —
цена явно назван на отдельной странице (€5200/год для ЕС/ЕЕЗ, после
автоматической стипендии €2400/год — то есть 5200 это уже реальная
сумма к оплате, не список цена минус стипендия отдельно).

Один вуз — один программный модуль без discovery-логики: тут нечего
обходить.
"""

from __future__ import annotations

from models import ProgrammeDraft, UniversityDraft

UNIVERSITY = UniversityDraft(
    slug="sse-riga",
    name_lv="Rīgas Ekonomikas augstskola",
    name_en="Stockholm School of Economics in Riga",
    kind="private",
    city="riga",
    website_url="https://www.sseriga.edu",
    source_url="https://www.sseriga.edu/education/bachelor",
)

PROGRAMME = ProgrammeDraft(
    slug="economics-and-business",
    name_en="Economics and Business",
    degree_level="bachelor",
    language_of_instruction="en",
    study_mode="full_time",
    city=UNIVERSITY.city,
    funding_type="paid",
    tuition_fee_amount=5200,
    duration_years=3,
    source_url="https://www.sseriga.edu/education/bachelor",
)


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    # Нечего обходить — один вуз, одна программа, факты зафиксированы
    # выше с датой проверки в docstring. Playwright тут не нужен.
    return UNIVERSITY, [PROGRAMME]
