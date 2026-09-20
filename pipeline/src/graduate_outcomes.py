"""Общее для импорта данных о выпускниках (ревью 2026-09, пункт 14) и
разметки направлений программ (seed_programme_fields.py).

Источник — открытый датасет ИЗМ/ЦСУ на data.gov.lv (CC0):
  https://data.gov.lv/dati/lv/dataset/2017_2023-g-latvijas-augstakas-izglitibas-iestazu-absolventi-2020-2024-monitoringa-gados
Каждый год публикуется новый файл (сейчас — данные на 2024 налоговый
год, выпуски 2017–2023) — ссылку CSV_URL надо обновлять вручную, взяв
кнопку "Lejupielādēt" у свежего ресурса на странице датасета.

Проверено 2026-09-17: методология (metodologija_atvertie_dati_2020.docx
на той же странице) — доходы считаются ТОЛЬКО по занятым, это общий
доход за год (все виды, без поправки на неполную занятость), при
меньше чем 30 занятых доходы скрыты, у докторов (код уровня 51) доходы
не публикуются; занятость определяется по состоянию на ноябрь.
"""

from __future__ import annotations

import csv
import io
import urllib.request
from dataclasses import dataclass

DATASET_URL = (
    "https://data.gov.lv/dati/lv/dataset/"
    "2017_2023-g-latvijas-augstakas-izglitibas-iestazu-absolventi-2020-2024-monitoringa-gados"
)
CSV_URL = (
    "https://data.gov.lv/dati/dataset/db8029f4-f85f-4f75-8fd7-c2b73e3a7c58/resource/"
    "a2cd227c-892f-49c8-9088-ae678bccf50e/download/2017_2023_ai_absolventi_2024_taksacijas_g.csv"
)

# Iestades_reg_numurs из датасета -> university.slug.
#
# RNU (Rīgas Ziemeļvalstu augstskola, Riga Nordic University) — это
# бывшая Informācijas sistēmu menedžmenta augstskola (ISMA): история
# на rnu.lv/par-rnu/vesture/ начинается с ISMA (основана в 1994), адрес
# и сайт те же. В датасете он поэтому записан под СТАРЫМ названием ISMA
# (3393800183). Первая версия этого файла ошибочно считала, что RNU в
# датасете нет вообще — сверка названий по одному лишь слову "Nordic"
# не могла его найти.
REG_NUMBER_TO_SLUG = {
    "2594001659": "via",
    "2793000222": "du",
    "2891101568": "lbtu",
    "3294001570": "venta",
    "3391000218": "lu",
    "3391000709": "rtu",
    "3393800213": "turiba",
    "3393801782": "tsi",
    "3393802029": "riseba",
    "3394800009": "bsa",
    "3394800214": "eka",
    "3394802425": "rgsl",
    "3394802920": "sse-riga",
    "3393800183": "rnu",
    "3391702042": "rsu",
    "3392301524": "lka",
    "3392301471": "lma",
    "3392301472": "jvlma",
    "3394801470": "rai",
    "3394400217": "lnaa",
    "3394802695": "lutera",
    "2994801398": "ekra",
    "2797002489": "dmk",
    "2997002472": "psmk",
    "3397002471": "rmk",
    "3397002593": "r1mk",
    "3097002320": "ljk",
    "4297102587": "malnavas-koledza",
    "3397001284": "rbk",
    "3397702502": "skmk",
    "3397002057": "rtk",
    "2997202532": "siva",
    "3397501387": "ucak",
    "3397502629": "vpk",
    "3197401385": "vrsk",
    "3397801552": "alberta",
    "3397801774": "gfk",
    "3397801243": "juridiska-koledza",
    "3397802338": "bvk",
    "3397802535": "rmenk",
    "3397802926": "hotel-school",
    "3397800727": "novikonta",
    "3396801789": "rti",
    "3396801788": "rarzi",
}

# Studiju_limenis -> наш degree_level. Расшифровка получена не из
# официальной легенды (её в открытых данных найти не удалось), а по
# сверке с известными программами ЛУ: Computer Science -> 43481,
# Economics -> 43314 (академический бакалавр), медицина ЛУ (одноуровневая,
# 6 лет) -> 48721. 49 добавлен после РСУ: его медицина (367 выпускников в
# 2019) и стоматология лежат именно в 49 — это одноуровневые длинные
# программы (медицина, стоматология, ветеринария; у РСУ в карточке
# "Second level study programme"). 44/46/50 (профессиональные программы
# поверх бакалавра и т.п.) по-прежнему не сопоставлены ни с одним нашим
# уровнем.
LEVEL_CODES_BY_DEGREE = {
    "college": ["41"],
    "bachelor": ["42", "43", "48", "49"],
    "master": ["45", "47"],
    "doctoral": ["51"],
}


@dataclass(frozen=True)
class OutcomeRow:
    university_slug: str
    graduation_year: int
    tax_year: int
    level_code: str
    programme_group: str
    graduates: int
    employed: int
    unemployed_or_inactive: int | None
    emigrated: int | None
    no_info: int | None
    avg_income_eur: float | None
    median_income_eur: float | None


def _decimal(value: str) -> float | None:
    value = value.strip()
    return float(value.replace(",", ".")) if value else None


def _integer(value: str) -> int | None:
    value = value.strip()
    return int(value) if value else None


def download_csv(url: str = CSV_URL) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8-sig")


def parse_outcomes(text: str) -> list[OutcomeRow]:
    """Только строки уровня "вуз + группа программ" по нашим вузам —
    итоги по вузу целиком и по одному лишь уровню обучения не берём:
    без направления цифра вводит в заблуждение (зарплата инженера и
    воспитателя в среднем по вузу — не про конкретную программу)."""
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    rows: list[OutcomeRow] = []
    for raw in reader:
        slug = REG_NUMBER_TO_SLUG.get(raw["Iestades_reg_numurs"])
        group = raw["Programmu_grupa"].strip()
        if slug is None or not group:
            continue
        rows.append(
            OutcomeRow(
                university_slug=slug,
                graduation_year=int(raw["Absolv_gads"]),
                tax_year=int(raw["Taks_gads"]),
                level_code=raw["Studiju_limenis"].strip(),
                programme_group=group,
                graduates=int(raw["Absolv_skaits"]),
                employed=int(raw["Absolv_nodarbin_skaits"]),
                unemployed_or_inactive=_integer(raw["Absolv_bezdarbn_ekon_neakt_skaits"]),
                emigrated=_integer(raw["Absolv_emigr_skaits"]),
                no_info=_integer(raw["Absolv_NAparnod_skaits"]),
                avg_income_eur=_decimal(raw["Vid_ienakumi_EUR_gada"]),
                median_income_eur=_decimal(raw["Ienakumu_mediana_EUR_gada"]),
            )
        )
    return rows
