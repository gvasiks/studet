"""Разовая загрузка конкурсных формул — не источник каталога (не входит
в SOURCES, не upsert-ит university/programme), а отдельный шаг: находит
уже существующие в базе программы по (university_slug, programme_slug)
и кладёт для них formula/formula_term.

Первая партия — Ventspils Augstskola, 7 из 13 программ каталога.
Источник — единственный принятый правилом 6 CLAUDE.md: утверждённый
Сенатом ВеА PDF правил приёма, не страница сайта (venta.lv/program/...
даёт ту же формулу текстом, но правило явно требует PDF):

  "Uzņemšanas noteikumi un imatrikulācijas kārtība Ventspils Augstskolā
  2026./2027. akadēmiskajā gadā", 1. pielikums
  (VeA Senāta lēmums Nr. 25-39, 27.11.2025., ar grozījumiem Nr. 26-3 un
  Nr. 26-28)
  https://irp.cdn-website.com/f6b5d556/files/uploaded/26-28_Pielikums-2_Uznemsanas_noteikumi_2026-2027_grozits_06-2026.pdf

Из 13 программ Вентспилса в каталоге сюда попали только 7 — те, где
формула однозначно строится из уже поддерживаемых formula_term.kind
('ce' / 'ce_average' / 'entrance_exam') без исключений:

- Не включены все магистерские и докторская программы — у них
  конкурс идёт по VSA (взвешенная средняя оценка диплома), это другая
  модель начисления, не сумма процентов ЦЭ; переиспользовать
  kind='certificate' для неё было бы натяжкой, а не честным
  прочтением документа.
- Не включена "Elektronikas inženierija" (bachelor): в таблице PDF
  сумма коэффициентов формулы равна 1,1 (0,6+0,2+0,1+0,1+0,1) из-за
  условного слагаемого "P4 – CE fizikā (ja ir kārtots)" — неясно,
  заменяет это одно из других слагаемых или действительно
  прибавляется сверху 100%. Класть числа, в которых сам не уверен, в
  таблицу, где формулу проверяет только человек (правило 6), хуже,
  чем не класть вовсе — оставлено на потом, дать человеку свериться
  с сайтом/деканатом напрямую.

verified_at везде NULL — этот скрипт заполняет только источник и
данные, подтверждает формулу исключительно человек через Supabase
Studio (правило 6 CLAUDE.md), включая для этой первой, казалось бы,
однозначной партии.
"""

from __future__ import annotations

from datetime import date

from dotenv import load_dotenv

from db import get_service_client

SOURCE_URL = (
    "https://irp.cdn-website.com/f6b5d556/files/uploaded/"
    "26-28_Pielikums-2_Uznemsanas_noteikumi_2026-2027_grozits_06-2026.pdf"
)
SOURCE_DOC = (
    "Uzņemšanas noteikumi un imatrikulācijas kārtība Ventspils Augstskolā "
    "2026./2027. akadēmiskajā gadā, 1. pielikums "
    "(VeA Senāta lēmums Nr. 25-39, 27.11.2025.)"
)
VALID_FROM = date(2025, 11, 27)

# subject — те же ключи, что в dict.survey.exams.subjects (lv.json/en.json),
# иначе калькулятор покажет сырой ключ вместо перевода (CalculatorForm.tsx).
FORMULA_SEEDS = [
    {
        "programme_slug": "programmesanas-specialists",
        "terms": [
            ("ce", "mathematics", 0.6),
            ("ce", "english", 0.2),
            ("ce", "latvian", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "datorzinatnes-bakalaurs",
        "terms": [
            ("ce", "mathematics", 0.6),
            ("ce", "english", 0.2),
            ("ce", "latvian", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "biznesa-vadiba-bakalaurs",
        "terms": [
            ("ce", "mathematics", 0.6),
            ("ce", "english", 0.2),
            ("ce", "latvian", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "jaunuznemumu-vadiba",
        "terms": [
            ("ce", "mathematics", 0.15),
            ("ce", "english", 0.15),
            ("entrance_exam", None, 0.6),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "vadibzinatne-lv-distance",
        "terms": [
            ("ce", "mathematics", 0.4),
            ("ce", "english", 0.4),
            ("ce", "latvian", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "vadibzinatne-en-full_time",
        "terms": [
            ("ce", "mathematics", 0.4),
            ("ce", "english", 0.4),
            ("ce", "latvian", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
    {
        "programme_slug": "valodas-sazina-un-kulturvide",
        "terms": [
            ("ce", "english", 0.4),
            ("ce", "latvian", 0.4),
            ("ce", "mathematics", 0.1),
            ("ce_average", None, 0.1),
        ],
    },
]


def seed(university_slug: str, seeds: list[dict]) -> None:
    load_dotenv()
    client = get_service_client()

    university = (
        client.table("university").select("id").eq("slug", university_slug).single().execute()
    )
    university_id = university.data["id"]

    for entry in seeds:
        programme = (
            client.table("programme")
            .select("id")
            .eq("university_id", university_id)
            .eq("slug", entry["programme_slug"])
            .single()
            .execute()
        )
        programme_id = programme.data["id"]

        formula_row = {
            "programme_id": programme_id,
            "variant": "ce",
            "valid_from": VALID_FROM.isoformat(),
            "source_url": SOURCE_URL,
            "source_doc": SOURCE_DOC,
        }
        formula = (
            client.table("formula")
            .upsert(formula_row, on_conflict="programme_id,variant,valid_from")
            .execute()
        )
        formula_id = formula.data[0]["id"]

        # formula_term не имеет собственного естественного ключа — проще
        # снести и вставить заново, чем сверять построчно при повторном
        # запуске.
        client.table("formula_term").delete().eq("formula_id", formula_id).execute()
        term_rows = [
            {"formula_id": formula_id, "kind": kind, "subject": subject, "coefficient": coefficient}
            for kind, subject, coefficient in entry["terms"]
        ]
        client.table("formula_term").insert(term_rows).execute()

        print(f"{entry['programme_slug']}: {len(term_rows)} terms")


if __name__ == "__main__":
    seed("venta", FORMULA_SEEDS)
