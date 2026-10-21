"""Требования к экзаменам РТУ — план 2026-09-21, пункт 02 (порция 2 начата
досрочно, 2026-10-21).

Формулы РТУ почти не разобраны: в п. 31.1 правил приёма слагаемое «CE
fizikā un/vai ķīmijā» не говорит, брать ли лучший или сумму, а каталог не
знает направление программы (memory/formula-extraction-status). Для
ТРЕБОВАНИЙ эти вопросы не важны: что нужно сдать, правила говорят одной
фразой для всех программ РТУ, в разделе 3 «Uzņemšanas pamatprincipi»:

  «Lai pretendētu studijām RTU, ir jābūt nokārtotiem obligātajiem CE –
  matemātikā, latviešu valodā un svešvalodā.»

Физика и химия в п. 31.1 — только вес в конкурсном балле, не условие
допуска; в требования не попадают. Иностранный язык — «svešvalodā», любой:
группа «английский | немецкий» (formula_drafts.FOREIGN_LANGUAGE_CHOICE).

Что не взято:
- порог по математике для бюджетных мест (28 % высший / 37,3 %
  оптимальный уровень) — условие конкурса на бюджет, не допуска; на
  платные места он не действует;
- вступительные испытания отдельных программ (п. 31.1–31.5) и оценки
  аттестата у педагогических программ RTU RA — не CE.

Правило одно на весь вуз, поэтому список программ берётся из каталога
(все программы РТУ уровня бакалавра и колледжа), а не переписывается
руками.

Источник: «Uzņemšanas noteikumi īsā cikla un pirmā cikla studiju programmās
2026./2027. akadēmiskajā gadā» (RTU Senāta 24.11.2025. sēdes
protokollēmums Nr. 697) — официальный текст опубликован только страницей
сайта, копия — docs/source-documents/rtu/uznemsanas-noteikumi-pamatstudijas-2026-27.html

Запуск:
  python src/requirements_rtu.py --selftest
  python src/requirements_rtu.py            # сухой прогон (читает каталог)
  python src/requirements_rtu.py --apply
"""

from __future__ import annotations

from datetime import date

from formula_drafts import FOREIGN_LANGUAGE_CHOICE, DocumentMeta, RequirementDraft, write_requirement_drafts

SOURCE_DOC = (
    "Uzņemšanas noteikumi īsā cikla un pirmā cikla studiju programmās 2026./2027. akadēmiskajā gadā, "
    "3. sadaļa «Uzņemšanas pamatprincipi» (RTU Senāta 24.11.2025. sēdes protokollēmums Nr. 697)"
)
VALID_FROM = date(2025, 11, 24)
EXCERPT = (
    "3. Uzņemšanas pamatprincipi. Reflektantu uzņemšana Programmās notiek pēc visu nokārtoto centralizēto "
    "eksāmenu (CE) rezultātiem, gada atzīmēm atsevišķos priekšmetos vidējās izglītības dokumentā un pēc "
    "papildu kritēriju rezultātiem, iestājpārbaudījumiem, papildu uzņemšanas kritērijiem, ja tādi ir noteikti. "
    "Lai pretendētu studijām RTU, ir jābūt nokārtotiem obligātajiem CE – matemātikā, latviešu valodā un "
    "svešvalodā."
)
GROUPS: list[list[str]] = [["mathematics"], ["latvian"], list(FOREIGN_LANGUAGE_CHOICE)]
LEVELS = ["bachelor", "college"]


def catalog_slugs() -> list[str]:
    from dotenv import load_dotenv

    from db import fetch_all, get_service_client

    load_dotenv()
    client = get_service_client()
    university_id = client.table("university").select("id").eq("slug", "rtu").single().execute().data["id"]
    rows = fetch_all(
        lambda: client.table("programme")
        .select("slug, id")
        .eq("university_id", university_id)
        .in_("degree_level", LEVELS)
        .order("id")
    )
    return sorted(row["slug"] for row in rows)


def seed(apply: bool) -> None:
    from seed_formulas import RTU_PROTOCOL, RTU_SOURCE_URL

    slugs = catalog_slugs()
    print(f"программ РТУ уровня бакалавра и колледжа: {len(slugs)}")
    draft = RequirementDraft(block="RTU 3. sadaļa (visas programmas)", slugs=slugs, groups=GROUPS, excerpt=EXCERPT)
    meta = DocumentMeta("rtu", RTU_SOURCE_URL, SOURCE_DOC, VALID_FROM, RTU_PROTOCOL if apply else {})
    write_requirement_drafts(meta, [draft], apply)


def selftest() -> None:
    from pathlib import Path

    copy = Path(__file__).resolve().parents[2] / "docs/source-documents/rtu/uznemsanas-noteikumi-pamatstudijas-2026-27.html"
    text = " ".join(copy.read_text(encoding="utf-8").split())
    # фраза-основание есть в копии документа дословно — при новой редакции
    # правил самопроверка напомнит перечитать
    assert "obligātajiem CE – matemātikā, latviešu valodā un svešvalodā" in text
    assert "fizikā un/vai ķīmijā reizina ar koeficientu" in text, "физика/химия — вес, а не требование"
    assert ["physics"] not in GROUPS and ["chemistry"] not in GROUPS
    assert FOREIGN_LANGUAGE_CHOICE in GROUPS
    print("самотест пройден")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        seed(apply="--apply" in sys.argv)
