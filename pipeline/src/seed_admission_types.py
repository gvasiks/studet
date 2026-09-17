"""Разовая загрузка типа отбора — ревью 2026-09, пункт 06. Как и
seed_formulas.py/seed_deadlines.py: находит существующий university по
slug и кладёт для него одну строку university_admission_type;
verified_at везде NULL, подтверждает только человек через Supabase
Studio (правило 6 CLAUDE.md).

Занесено только то, что уже твёрдо установлено в проекте, не всё
четырнадцать вузов (лучше меньше, но точно):

- ЛУ, РТУ, Вентспилс — 'competitive_score'. Это не новое наблюдение,
  а сама основа калькулятора: CLAUDE.md прямо называет их вузами,
  на которых подтверждена общая модель конкурсного балла.
- Turība — 'entrance_exam' (turiba.lv/en/admission/admission,
  проверено 2026-09-17): математический или социальный тест +
  собеседование + тест английского для всех абитуриентов бакалавриата,
  не сумма процентов ЦЭ.

Остальные десять вузов (LBTU, DU, VIA — гос.; RISEBA, BSA, SSE Riga,
RGSL, EKA, RNU, TSI — частные) сюда сознательно не попали: для
государственных нет причин считать, что у них та же модель без
проверки, а для частных нужно по одному заходу на сайт каждого —
не делали вслепую.
"""

from __future__ import annotations

from dotenv import load_dotenv

from db import get_service_client

COMPETITIVE_SCORE_UNIVERSITIES = ["lu", "rtu", "venta"]

TURIBA_SOURCE_URL = "https://www.turiba.lv/en/admission/admission"


def seed(university_slug: str, selection_type: str, source_url: str | None = None) -> None:
    client = get_service_client()

    university = (
        client.table("university").select("id").eq("slug", university_slug).single().execute()
    )
    university_id = university.data["id"]

    row = {
        "university_id": university_id,
        "selection_type": selection_type,
        "source_url": source_url,
    }
    # upsert по primary key (university_id) — verified_at/verified_by в
    # row нет, поэтому повторный запуск не откатывает уже подтверждённую
    # человеком запись (тот же приём, что и в seed_deadlines.py).
    client.table("university_admission_type").upsert(row, on_conflict="university_id").execute()
    print(f"{university_slug}: {selection_type}")


if __name__ == "__main__":
    load_dotenv()
    for slug in COMPETITIVE_SCORE_UNIVERSITIES:
        seed(slug, "competitive_score")
    seed("turiba", "entrance_exam", TURIBA_SOURCE_URL)
