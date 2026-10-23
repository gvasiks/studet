"""Требования к экзаменам частных вузов и колледжей (и ViA — у неё правило
того же вида) — план 2026-09-21, пункт 02, порция 2 (начата досрочно,
2026-10-22).

Как у РТУ (requirements_rtu.py): правила приёма каждого учреждения говорят
одной фразой, какие ЦЭ нужны для конкурса на все программы первого
уровня, поэтому список программ берётся из каталога (бакалавр и колледж).
Фраза-основание — дословно в EXCERPT, копия документа — в
docs/source-documents/<учреждение>/.

Иностранный язык — «svešvaloda», любой: группа «английский | немецкий»
(formula_drafts.FOREIGN_LANGUAGE_CHOICE).

Что не взято:
- BSA: правила (п. 10) говорят «pamatojoties uz centralizēto eksāmenu
  rezultātiem», но не называют предметы — требований нет, только тип отбора
  (seed_admission_types.py);
- RAI: правила не говорят, как отбирают в бакалавриат;
- TSI и LMA: сайты закрыты для ИИ-сборщиков в robots.txt — не читались,
  вопрос письмом.

Запуск:
  python src/requirements_private.py --selftest
  python src/requirements_private.py            # сухой прогон (читает каталог)
  python src/requirements_private.py --apply
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from formula_drafts import FOREIGN_LANGUAGE_CHOICE, DocumentMeta, RequirementDraft, write_requirement_drafts

GROUPS: list[list[str]] = [["latvian"], ["mathematics"], list(FOREIGN_LANGUAGE_CHOICE)]
LEVELS = ["bachelor", "college"]
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Institution:
    slug: str
    source_url: str
    source_doc: str
    doc_number: str
    doc_date: date
    valid_from: date
    copy_path: str
    # дословная фраза документа — по ней проверяет самопроверка
    excerpt: str
    anchor: str
    # обычно «латышский, математика, иностранный»; у RISEBA иностранный —
    # именно английский
    groups: list[list[str]] = field(default_factory=lambda: [list(group) for group in GROUPS])


INSTITUTIONS: list[Institution] = [
    Institution(
        slug="juridiska-koledza",
        source_url="https://jk.lv/uznemsana/uznemsana/uznemsanas-noteikumi/",
        source_doc="Juridiskās koledžas 2026./2027. studiju gada uzņemšanas noteikumi, 8. punkts",
        doc_number="3-01/118",
        doc_date=date(2024, 9, 19),
        valid_from=date(2024, 9, 19),
        copy_path="docs/source-documents/juridiska-koledza/uznemsanas-noteikumi-2026-27.html",
        excerpt=(
            "8. Uzņemšana īsā cikla profesionālās augstākās izglītības studiju programmās notiek konkursa kārtībā, "
            "pamatojoties uz centralizēto eksāmenu mācību priekšmetos: Matemātikā, Latviešu valoda un Svešvaloda "
            "(angļu valoda, vācu valoda, franču valoda) rezultātiem"
        ),
        anchor="pamatojoties uz centralizēto eksāmenu mācību priekšmetos: Matemātikā, Latviešu valoda un Svešvaloda",
    ),
    Institution(
        slug="psmk",
        source_url="https://psk.lu.lv/_files/ugd/4cfd02_bec1076fcdb24e46ac1b6873371b04b0.pdf",
        source_doc="LU P. Stradiņa medicīnas koledžas uzņemšanas noteikumi 2026./2027. akadēmiskam studiju gadam, 4.1.–4.2. punkts",
        doc_number="6",
        doc_date=date(2025, 11, 13),
        valid_from=date(2025, 11, 13),
        copy_path="docs/source-documents/psmk/uznemsanas-noteikumi-2026-27.pdf",
        excerpt=(
            "4.1. Uzņemšana pilna laika studijās notiek bez iestājpārbaudījumiem atklātā un vienlīdzīgā konkursa "
            "kārtībā. 4.2. Konkursa atlases kritērijs ir visu nokārtoto obligāto centralizēto eksāmenu (latviešu "
            "valoda, matemātika, svešvaloda) rezultāti"
        ),
        anchor="obligāto centralizēto eksāmenu (latviešu valoda, matemātika, svešvaloda)",
    ),
    Institution(
        slug="rnu",
        source_url="https://rnu.lv/wp-content/uploads/2026/07/RZA_Uznemsanas_noteikumi_2026_2027.pdf",
        source_doc="Rīgas Ziemeļvalstu augstskolas uzņemšanas noteikumi 2026./2027. akadēmiskajam gadam, 3.1. punkts",
        doc_number="8-25",
        doc_date=date(2025, 11, 25),
        valid_from=date(2025, 11, 25),
        copy_path="docs/source-documents/rnu/uznemsanas-noteikumi-2026-27.pdf",
        # «visu obligāto CE» — обязательные ЦЭ средней школы: латышский,
        # математика, иностранный (так же у PSK, где они перечислены)
        excerpt=(
            "3.1. Reflektantu uzņemšana pilna laika īsā cikla profesionālās augstākās izglītības programmās un pirmā "
            "cikla augstākās izglītības programmās notiek konkursa kārtībā, pamatojoties uz visu obligāto CE "
            "rezultātiem"
        ),
        anchor="pamatojoties uz visu obligāto CE rezultātiem",
    ),
    # ViA — государственный вуз, но правило того же вида: в приложении 1 у
    # каждой из 7 программ бакалавриата в колонке «Centralizētie eksāmeni» одно
    # и то же (прочитано 2026-10-23; у «Mediju studijas» и «Tūrisma
    # organizācija» текст в PDF разбит по колонкам, но тот же). Конкурс —
    # среднее всех сданных ЦЭ плюс надбавки.
    Institution(
        slug="via",
        source_url=(
            "https://va.lv/images/2024/Studiju%20grupa/Uznemsana%202026/"
            "A1UznemNot1LPamST2026-2027-APST27112025-pedgroz30042026.pdf"
        ),
        source_doc="Uzņemšanas noteikumi Vidzemes Augstskolā bakalaura un maģistra studiju programmās 2026./2027., 1. pielikums",
        doc_number="2025/8/1.1. (grozījumi 2026/2/1.1., 2026/3/1.1., 2026/5/1.1.)",
        doc_date=date(2026, 4, 30),
        valid_from=date(2025, 11, 27),
        copy_path="docs/source-documents/via/uznemsanas-noteikumi-pamatstudijas-2026-27.pdf",
        excerpt=(
            "1. pielikums «Uzņemšanas prasības bakalaura studiju programmās», kolonna «Centralizētie eksāmeni» "
            "(vienāda visām programmām): LATVIEŠU VALODA, MATEMĀTIKA, SVEŠVALODA (vienā no mācību satura apguves "
            "līmeņiem (AL, OP, VL), kā arī pārējie reflektanta kārtotie CE). Obligātā prasība: CE rezultāti - visu "
            "kārtoto CE rezultātu kopvērtējumu vidējā vērtība."
        ),
        anchor="LATVIEŠU VALODA** MATEMĀTIKA SVEŠVALODA*^",
    ),
    Institution(
        slug="riseba",
        source_url="https://riseba.lv/wp-content/uploads/2025/12/nt0002-42_-uznemsanas-noteikumi_2026_2027_galaredakcija.pdf",
        source_doc="RISEBA Uzņemšanas noteikumi 2026./2027. studiju gadam (NT0002-42), 2.5. punkts",
        doc_number="25/1.1-7/12",
        doc_date=date(2025, 11, 12),
        valid_from=date(2025, 11, 12),
        copy_path="docs/source-documents/riseba/uznemsanas-noteikumi-2026-27.pdf",
        excerpt=(
            "2.5. Vispārējās prasības reflektantu uzņemšanai studijām pirmā cikla (bakalaura) studiju programmās: "
            "2.5.1. Iegūta vidējā izglītība …; 2.5.2. Nokārtots centralizētais eksāmens latviešu valodā; 2.5.3. "
            "Nokārtots centralizētais eksāmens matemātikā; 2.5.4. Nokārtots centralizētais eksāmens angļu valodā"
        ),
        anchor="2.5.4. Nokārtots centralizētais eksāmens angļu valodā",
        groups=[["latvian"], ["mathematics"], ["english"]],
    ),
]


def document_text(institution: Institution) -> str:
    """Текст копии документа одной строкой (для самопроверки фразы)."""
    import html
    import re

    path = REPO_ROOT / institution.copy_path
    if path.suffix == ".pdf":
        from pypdf import PdfReader

        raw = " ".join(page.extract_text() or "" for page in PdfReader(path).pages)
    else:
        page = path.read_text(encoding="utf-8", errors="replace")
        page = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S)
        raw = html.unescape(re.sub(r"<[^>]+>", " ", page))
    return " ".join(raw.split())


def catalog_slugs(client, university_slug: str) -> list[str]:  # type: ignore[no-untyped-def]
    from db import fetch_all

    university_id = client.table("university").select("id").eq("slug", university_slug).single().execute().data["id"]
    rows = fetch_all(
        lambda: client.table("programme").select("slug, id").eq("university_id", university_id).in_("degree_level", LEVELS).order("id")
    )
    return sorted(row["slug"] for row in rows)


def seed(apply: bool) -> None:
    from dotenv import load_dotenv

    from db import get_service_client
    from seed_formulas import source_protocol

    load_dotenv()
    client = get_service_client()
    for institution in INSTITUTIONS:
        slugs = catalog_slugs(client, institution.slug)
        print(f"{institution.slug}: программ бакалавра и колледжа — {len(slugs)}")
        protocol = (
            source_protocol(
                number=institution.doc_number,
                doc_date=institution.doc_date,
                copy_path=institution.copy_path,
                fetched_on=date(2026, 10, 22),
            )
            if apply
            else {}
        )
        draft = RequirementDraft(
            block=f"{institution.slug} (visas programmas)", slugs=slugs, groups=institution.groups, excerpt=institution.excerpt
        )
        meta = DocumentMeta(institution.slug, institution.source_url, institution.source_doc, institution.valid_from, protocol)
        write_requirement_drafts(meta, [draft], apply)


def selftest() -> None:
    for institution in INSTITUTIONS:
        text = document_text(institution)
        # фраза-основание есть в копии документа — при новой редакции правил
        # самопроверка напомнит перечитать
        assert institution.anchor in text, f"{institution.slug}: фразы-основания нет в копии документа"
    assert FOREIGN_LANGUAGE_CHOICE in GROUPS and ["latvian"] in GROUPS and ["mathematics"] in GROUPS
    riseba = next(institution for institution in INSTITUTIONS if institution.slug == "riseba")
    assert ["english"] in riseba.groups and FOREIGN_LANGUAGE_CHOICE not in riseba.groups, "у RISEBA — именно английский"
    print("самотест пройден")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        seed(apply="--apply" in sys.argv)
