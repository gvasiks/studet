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
    # программа (адрес в каталоге) -> свой набор, если правила делают для неё
    # исключение (RBK: «Restaurācija» без математики)
    overrides: dict[str, list[list[str]]] = field(default_factory=dict)
    # когда скачана копия документа
    fetched_on: date = date(2026, 10, 22)
    # только эти программы (адреса в каталоге), если у учреждения разные
    # документы для разных направлений (JVLMA: «Mākslas» и «Izglītība un
    # pedagoģija»); None — все программы бакалавра и колледжа
    only: list[str] | None = None


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
        fetched_on=date(2026, 10, 23),
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
        fetched_on=date(2026, 10, 23),
    ),
    Institution(
        slug="bvk",
        source_url="https://www.bvk.lv/wp-content/uploads/2025/11/uznemsanas-noteikumi-2026-2027-studiju-gads.pdf",
        source_doc="SIA «Biznesa vadības koledža» uzņemšanas noteikumi 2026./2027. studiju gadam, 4.1.–4.2. punkts",
        doc_number="VAD 4-02/06.10.2025",
        doc_date=date(2025, 10, 6),
        valid_from=date(2025, 10, 6),
        copy_path="docs/source-documents/bvk/uznemsanas-noteikumi-2026-27.pdf",
        # минимум 20 % по каждому ЦЭ (сданным с 2025 года) модель требований
        # не хранит — он остаётся в выдержке
        excerpt=(
            "4.1. Uzņemšanai studiju programmā Koledža rīko atklātu un vienlīdzīgu konkursu, pamatojoties uz "
            "centralizēto eksāmenu rezultātiem … 4.2. Koledžas konkursa atlases kritērijs ir centralizēto eksāmenu "
            "latviešu valodā, svešvalodā un matemātikā vērtējums. Minimālajam vērtējumam … No 2025. gada 20%"
        ),
        anchor="konkursa atlases kritērijs ir centralizēto eksāmenu latviešu val",
        fetched_on=date(2026, 10, 25),
    ),
    Institution(
        slug="rbk",
        source_url="https://www.rck.lv/wp-content/uploads/2025/05/2024_01-13-13.1_RBK.pdf",
        source_doc=(
            "Uzņemšanas noteikumi un imatrikulācija Rīgas Būvniecības koledžā (iekšējie noteikumi Nr. 2024_01-13/13.1), "
            "4.2. punkts"
        ),
        doc_number="2024_01-13/13.1",
        doc_date=date(2024, 10, 15),
        valid_from=date(2024, 10, 15),
        copy_path="docs/source-documents/rbk/uznemsanas-noteikumi.pdf",
        excerpt=(
            "4.2. Konkursa atlases kritērijs ir matemātikas (izņemot studiju programmu Restaurācija), latviešu valodas "
            "un svešvalodas CE rezultāti vienā no mācību satura apguves līmeņiem"
        ),
        anchor="matemātikas (izņemot studiju programmu Restaurācija), latviešu valodas un svešvalodas CE rezultāti",
        overrides={"529": [["latvian"], list(FOREIGN_LANGUAGE_CHOICE)]},
        fetched_on=date(2026, 10, 25),
    ),
    Institution(
        slug="r1mk",
        source_url="https://www.rmk1.lv/lv/studiju-iespejas/ieraksts/pirma-limena-profesionalas-augstakas-izglitibas-uznemsanas-noteikumi/",
        source_doc=(
            "Uzņemšanas noteikumi Latvijas Universitātes Rīgas 1. medicīnas koledžas īsā cikla profesionālās augstākās "
            "izglītības programmās 2026./2027., 12. punkts"
        ),
        doc_number="40",
        doc_date=date(2025, 11, 6),
        valid_from=date(2025, 11, 6),
        copy_path="docs/source-documents/r1mk/uznemsanas-noteikumi-2026-27.html",
        # 12.3: математика — у тех, кто получил среднее образование с 2008
        # года, то есть у всех нынешних выпускников
        excerpt=(
            "12. Uzņemšana pilna laika studiju programmās notiek atklāta un vienlīdzīga konkursa kārtībā, pamatojoties uz "
            "… centralizēto eksāmenu rezultātiem: 12.1. centralizētā eksāmena latviešu valodā; 12.2. centralizētā eksāmena "
            "svešvalodā …; 12.3. centralizētā eksāmena matemātikā (personas, kuras vidējo izglītību ieguvušas, sākot ar "
            "2008.gadu)"
        ),
        anchor="12.1. centralizētā eksāmena latviešu valodā",
        fetched_on=date(2026, 10, 25),
    ),
    Institution(
        slug="vpk",
        source_url="https://www.policijas.koledza.gov.lv/lv/media/6830/download?attachment",
        source_doc="Uzņemšanas noteikumi Valsts policijas koledžā 2026./2027. studiju (mācību) gadam (iekšējie noteikumi Nr. 1.4-19)",
        doc_number="1.4-19 (grozījumi: 1.4-4, 02.06.2026)",
        doc_date=date(2026, 6, 2),
        valid_from=date(2025, 11, 28),
        copy_path="docs/source-documents/vpk/uznemsanas-noteikumi-2026-27.docx",
        # математику правила не называют; конкурс — ЦЭ латышский и
        # иностранный + проверка физподготовки (+ тест памяти и латышского)
        excerpt=(
            "Koledžā neuzņem reflektantu, kuram centralizētajos eksāmenos latviešu valodā un svešvalodā vērtējums ir "
            "zemāks par šo iekšējo noteikumu 27. punktā norādītajiem vērtējumiem atbilstoši absolvēšanas gadam."
        ),
        anchor="centralizētajos eksāmenos latviešu valodā un svešvalodā vērtējums ir zemāks",
        groups=[["latvian"], list(FOREIGN_LANGUAGE_CHOICE)],
        fetched_on=date(2026, 10, 25),
    ),
    Institution(
        slug="jvlma",
        source_url="https://www.jvlma.lv/data/doc_uznemsanas_process/muzikas-un-makslas-uznemsanas-noteikumi-28052026.docx",
        source_doc=(
            "JVLMA Uzņemšanas noteikumi studiju virziena «Mākslas» studiju programmās 2026./2027., II daļa "
            "(iepriekš iegūtā izglītība)"
        ),
        doc_number="8 (grozījumi: 9, 17.06.2026)",
        doc_date=date(2026, 6, 17),
        valid_from=date(2025, 11, 5),
        copy_path="docs/source-documents/jvlma/uznemsanas-noteikumi-makslas-2026-27.docx",
        # конкурс — по вступительным испытаниям (тип отбора entrance_exam),
        # но сданные ЦЭ — условие допуска
        excerpt=(
            "Uzņemšanai profesionālajā bakalaura studiju programmā ir nepieciešama vispārējā vidējā vai profesionālā "
            "vidējā izglītība, tostarp nokārtoti centralizētie eksāmeni mācību priekšmetos Latviešu valoda, Matemātika "
            "un Svešvaloda."
        ),
        anchor="nokārtoti centralizētie eksāmeni mācību priekšmetos Latviešu valoda, Matemātika un Svešvaloda",
        fetched_on=date(2026, 10, 25),
        only=["music-and-performing-arts-bachelor"],
    ),
    Institution(
        slug="jvlma",
        source_url="https://www.jvlma.lv/data/doc_uznemsanas_process/izglitibas-virziens-uznemsana-noteikumi-28052026.docx",
        source_doc=(
            "JVLMA Uzņemšanas noteikumi studiju virziena «Izglītība un pedagoģija» īsā cikla un profesionālajā bakalaura "
            "studiju programmā 2026./2027. (iepriekš iegūtā izglītība)"
        ),
        doc_number="8 (grozījumi: 9, 17.06.2026)",
        doc_date=date(2026, 6, 17),
        valid_from=date(2025, 11, 5),
        copy_path="docs/source-documents/jvlma/uznemsanas-noteikumi-izglitiba-2026-27.docx",
        excerpt=(
            "Uzņemšanai īsā cikla profesionālās augstākās izglītības studiju programmā un profesionālajā bakalaura "
            "studiju programmā ir nepieciešama vispārējā vidējā vai profesionālā vidējā izglītība, tostarp nokārtoti "
            "centralizētie eksāmeni mācību priekšmetos Latviešu valoda, Matemātika un Svešvaloda."
        ),
        anchor="nokārtoti centralizētie eksāmeni mācību priekšmetos Latviešu valoda, Matemātika un Svešvaloda",
        fetched_on=date(2026, 10, 25),
        only=[
            "music-dance-arts-vocationally-oriented-and-interest-related-education-teacher-college",
            "music-theatre-arts-dance-visual-arts-teacher-bachelor",
        ],
    ),
]


def document_text(institution: Institution) -> str:
    """Текст копии документа одной строкой (для самопроверки фразы)."""
    import html
    import re

    path = REPO_ROOT / institution.copy_path
    if path.suffix == ".docx":
        import zipfile

        xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
        raw = html.unescape(re.sub(r"<[^>]+>", " ", xml))
    elif path.suffix == ".pdf":
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
        if institution.only is not None:
            absent = sorted(set(institution.only) - set(slugs))
            if absent:
                raise SystemExit(f"{institution.slug}: программ {absent} нет в каталоге")
            slugs = list(institution.only)
        print(f"{institution.slug}: программ бакалавра и колледжа — {len(slugs)}")
        protocol = (
            source_protocol(
                number=institution.doc_number,
                doc_date=institution.doc_date,
                copy_path=institution.copy_path,
                fetched_on=institution.fetched_on,
            )
            if apply
            else {}
        )
        missing = sorted(set(institution.overrides) - set(slugs))
        if missing:
            raise SystemExit(f"{institution.slug}: программ {missing} из исключений нет в каталоге")
        common = [slug for slug in slugs if slug not in institution.overrides]
        drafts = [
            RequirementDraft(
                block=f"{institution.slug} (visas programmas)", slugs=common, groups=institution.groups, excerpt=institution.excerpt
            )
        ] + [
            RequirementDraft(block=f"{institution.slug} ({slug})", slugs=[slug], groups=groups, excerpt=institution.excerpt)
            for slug, groups in institution.overrides.items()
        ]
        meta = DocumentMeta(institution.slug, institution.source_url, institution.source_doc, institution.valid_from, protocol)
        write_requirement_drafts(meta, drafts, apply)


def selftest() -> None:
    for institution in INSTITUTIONS:
        text = document_text(institution)
        # фраза-основание есть в копии документа — при новой редакции правил
        # самопроверка напомнит перечитать
        assert institution.anchor in text, f"{institution.slug}: фразы-основания нет в копии документа"
    assert FOREIGN_LANGUAGE_CHOICE in GROUPS and ["latvian"] in GROUPS and ["mathematics"] in GROUPS
    riseba = next(institution for institution in INSTITUTIONS if institution.slug == "riseba")
    assert ["english"] in riseba.groups and FOREIGN_LANGUAGE_CHOICE not in riseba.groups, "у RISEBA — именно английский"
    rbk = next(institution for institution in INSTITUTIONS if institution.slug == "rbk")
    assert all(["mathematics"] not in groups for groups in rbk.overrides.values()), "Restaurācija — без математики"
    print("самотест пройден")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        seed(apply="--apply" in sys.argv)
