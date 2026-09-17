"""Разовая загрузка дедлайнов подачи — ревью 2026-09, пункт 04. Как и
seed_formulas.py: находит существующий university по slug и кладёт для
него application_round; verified_at везде NULL, подтверждает только
человек через Supabase Studio (правило 6 CLAUDE.md).

Живьём проверено 2026-09-17, что реально опубликовано:

- ЛУ (lu.lv/gribustudet/uznemsanas-kartiba/pamatstudijas/): "Šobrīd
  uzņemšana uz 2026./2027. akadēmiskā gada rudens semestri ir
  noslēgusies! Informācija par 2027./2028. akadēmiskā gada uzņemšanu
  tiks papildināta." — календаря на 2027/2028 нет, страница прямо это
  говорит.
- РТУ (rtu.lv/.../pieteiksanas-bakalaura-limena-studijam): "Līdz
  14. augustam turpinās uzņemšana..." без указания года — похоже на не
  до конца обновлённую страницу прошлого цикла, не факт, на который
  можно сослаться.
- Turība, латышский трек (turiba.lv/lv/uznemsana): даты даны на
  2026./2027. gadu (reģistrācija no 2026-01-05, līgumi no 2026-07-06) —
  тоже прошлый цикл, не 2027/2028.

Ни одно из трёх НЕ даёт дату, актуальную для сезона, к которому готовится
январский релиз 2027 — не потому что искали плохо, а потому что ни один
из вузов пока не опубликовал 2027./2028. gada календарь (сентябрь —
слишком рано, тот же разрыв, что и с таблицей коэффициентов ЛУ в
seed_formulas.py). Даты CLAUDE.md ("9–20 июля 2027", "Turība 5 января")
— это ориентир из бизнес-анализа, не подтверждённый источником факт;
использовать их здесь как правило 5 CLAUDE.md запрещает. Повторить
проверку ближе к делу (ноябрь-декабрь 2026) — тогда это и войдёт в
годовой цикл конвейера.

Единственное, что оказалось пригодно уже сейчас — международный (EN)
трек Turība: там расписание не привязано к учебному году, а
представляет собой два повторяющихся окна приёма (turiba.lv/en/admission/admission,
раздел INTAKES, проверено 2026-09-17). Год не указан вообще — значит
не устареет к январю 2027 само по себе.
"""

from __future__ import annotations

from datetime import date

from dotenv import load_dotenv

from db import get_service_client

TURIBA_SOURCE_URL = "https://www.turiba.lv/en/admission/admission"

# opens_on/closes_on — год условный (текущий отсчётный), поле label и
# note объясняют, что окно повторяется ежегодно на эти же даты.
TURIBA_EN_ROUNDS = [
    {
        "language_of_instruction": "en",
        "label": "Autumn intake",
        "opens_on": date(2026, 2, 1),
        "closes_on": date(2026, 8, 1),
        "note": "Studies begin at the end of September. Window repeats yearly (Feb 1 – Aug 1), not tied to a specific academic year.",
    },
    {
        "language_of_instruction": "en",
        "label": "Winter intake",
        "opens_on": date(2026, 8, 2),
        "closes_on": date(2026, 12, 1),
        "note": "Studies begin in February. Window repeats yearly (Aug 2 – Dec 1), not tied to a specific academic year.",
    },
]


def seed(university_slug: str, rounds: list[dict], source_url: str) -> None:
    client = get_service_client()

    university = (
        client.table("university").select("id").eq("slug", university_slug).single().execute()
    )
    university_id = university.data["id"]

    for entry in rounds:
        row = {
            "university_id": university_id,
            "degree_level": entry.get("degree_level"),
            "language_of_instruction": entry.get("language_of_instruction"),
            "label": entry["label"],
            "opens_on": entry["opens_on"].isoformat(),
            "closes_on": entry["closes_on"].isoformat(),
            "note": entry.get("note"),
            "source_url": source_url,
        }
        # upsert, не insert: повторный запуск не должен плодить дубли.
        # verified_at/verified_by в row нет вовсе, поэтому PostgREST не
        # трогает их при конфликте — уже подтверждённая человеком запись
        # не откатится обратно в неподтверждённую.
        client.table("application_round").upsert(row, on_conflict="university_id,label").execute()
        print(f"{university_slug}: {entry['label']}")


if __name__ == "__main__":
    load_dotenv()
    seed("turiba", TURIBA_EN_ROUNDS, TURIBA_SOURCE_URL)
