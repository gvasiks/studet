"""Требования к экзаменам Ventspils Augstskola — план 2026-09-21, пункт 02,
порция 1.

Как и requirements_du.py, это НЕ парсер: таблица приложения 1 в PDF
разбита на колонки, строки прочитаны глазами (2026-10-21); текст
столбца «Centralizētie eksāmeni/starptautiskie testi un
iestājpārbaudījumi» (строки ячейки сведены в одну) — в excerpt каждого блока.

Источник — тот же документ, что у формул Ventspils (seed_formulas.py,
VENTA_*): «Uzņemšanas noteikumi un imatrikulācijas kārtība Ventspils
Augstskolā 2026./2027. akadēmiskajā gadā», 1. pielikums (VeA Senāta lēmums
Nr. 25-39, 27.11.2025., ar grozījumiem Nr. 26-3 un Nr. 26-28) —
docs/source-documents/venta/uznemsanas-noteikumi-2026-27-pielikums-2-grozits-06-2026.pdf

Что взято: P1–P3 — обязательные CE. Иностранный язык здесь — именно
английский («CE vai STIP angļu valodā»: CE или международный тест по
английскому), поэтому ['english'], а не группа «английский | немецкий».
Международный тест (STIP) анкета не спрашивает — человек с ним без CE по
английскому увидит «не хватает»; это то же упрощение, что у формулы.

Что не взято:
- «P4 – CE fizikā (ja ir kārtots)» у Elektronikas inženierija — «если
  сдан», то есть не обязателен;
- «P3 – VeA iestājpārbaudījums» у Jaunuzņēmumu vadība — вступительное
  испытание вуза, не CE (как и у ЛУ, в требования не попадает);
- «angļu valodas zināšanas vismaz B2 līmenī» у английских потоков — уровень
  языка, а не экзамен;
- английский поток «Valodas, saziņa un kultūrvide»
  (valodas-sazina-un-kulturvide-en): в документе у программы одна строка без
  пометки «ENG», английского потока в нём нет;
- магистерские программы — конкурс по VSA (средняя оценка диплома).

Строка «Datorzinātnes (ENG un LV)» — одна на оба потока, поэтому требования
у datorzinatnes-bakalaurs и datorzinatnes-bakalaurs-en одинаковые.

Запуск:
  python src/requirements_venta.py --selftest
  python src/requirements_venta.py            # сухой прогон
  python src/requirements_venta.py --apply
"""

from __future__ import annotations

from dataclasses import dataclass

from formula_drafts import DocumentMeta, RequirementDraft, write_requirement_drafts

CE_ENGLISH_LATVIAN_MATHS: list[list[str]] = [["mathematics"], ["english"], ["latvian"]]
CE_MATHS_ENGLISH: list[list[str]] = [["mathematics"], ["english"]]


@dataclass
class VentaBlock:
    name: str
    slugs: list[str]
    groups: list[list[str]]
    excerpt: str


_STANDARD = "P1 - CE matemātikā; P2 - CE vai STIP angļu valodā; P3 – CE latviešu valodā"

BLOCKS: list[VentaBlock] = [
    VentaBlock(
        "Programmēšanas speciālists (īsā cikla)",
        ["programmesanas-specialists"],
        CE_ENGLISH_LATVIAN_MATHS,
        f"“Programmēšanas speciālists”, PLK, 2 gadi. Vidējā izglītība. {_STANDARD}.",
    ),
    VentaBlock(
        "Datorzinātnes (ENG un LV)",
        ["datorzinatnes-bakalaurs", "datorzinatnes-bakalaurs-en"],
        CE_ENGLISH_LATVIAN_MATHS,
        "“Datorzinātnes” (ENG un LV), PLK, 3 gadi. Vidējā izglītība; programmas angļu valodas variantam "
        f"papildu angļu valodas zināšanu līmenis vismaz B2 līmenī. {_STANDARD}.",
    ),
    VentaBlock(
        "Elektronikas inženierija",
        ["elektronika-bakalaurs"],
        CE_ENGLISH_LATVIAN_MATHS,
        f"“Elektronikas inženierija”, PLK, 4 gadi. Vidējā izglītība. {_STANDARD}; "
        "P4 – CE fizikā (ja ir kārtots).",
    ),
    VentaBlock(
        "Biznesa vadība",
        ["biznesa-vadiba-bakalaurs"],
        CE_ENGLISH_LATVIAN_MATHS,
        "“Biznesa vadība”, PLK, 4 gadi. Vidējā izglītība. P1 – CE matemātikā; P2 – CE vai STIP angļu "
        "valodā; P3 – CE latviešu valodā.",
    ),
    VentaBlock(
        "Jaunuzņēmumu vadība (ENG)",
        ["jaunuznemumu-vadiba"],
        CE_MATHS_ENGLISH,
        "“Jaunuzņēmumu vadība” (ENG), PLK, 4 gadi. Vidējā izglītība un angļu valodas zināšanas vismaz B2 "
        "līmenī. P1 – CE matemātikā; P2 – CE vai STIP angļu valodā; P3 – VeA iestājpārbaudījums.",
    ),
    VentaBlock(
        "Vadībzinātne (LV, NLN)",
        ["vadibzinatne-lv-distance"],
        CE_ENGLISH_LATVIAN_MATHS,
        "“Vadībzinātne” (LV), NLN, 4 gadi. Vidējā izglītība. P1 – CE matemātikā; P2 – CE vai STIP angļu "
        "valodā; P3 – CE latviešu valodā.",
    ),
    VentaBlock(
        "Vadībzinātne (PLK)",
        ["vadibzinatne-en-full_time"],
        CE_ENGLISH_LATVIAN_MATHS,
        "“Vadībzinātne”, PLK, 3 gadi. Vidējā izglītība un angļu valodas zināšanas vismaz B2 līmenī. "
        "P1 – CE matemātikā; P2 – CE vai STIP angļu valodā; P3 – CE latviešu valodā.",
    ),
    VentaBlock(
        "Valodas, saziņa un kultūrvide",
        ["valodas-sazina-un-kulturvide"],
        CE_ENGLISH_LATVIAN_MATHS,
        "“Valodas, saziņa un kultūrvide”, PLK, 3 gadi. Vidējā izglītība. P1- CE vai STIP angļu valodā; "
        "P2 - CE latviešu valodā; P3 - CE matemātikā.",
    ),
]

NOT_TAKEN = [
    ("valodas-sazina-un-kulturvide-en", "в документе нет английского потока этой программы"),
]


def report() -> None:
    print(f"блоков: {len(BLOCKS)}; программ: {sum(len(b.slugs) for b in BLOCKS)}")
    for slug, why in NOT_TAKEN:
        print(f"  не взято {slug}: {why}")


def seed(apply: bool) -> None:
    from seed_formulas import VENTA_PROTOCOL, VENTA_SOURCE_DOC, VENTA_SOURCE_URL, VENTA_VALID_FROM

    drafts = [RequirementDraft(block=f"VeA {b.name}", slugs=b.slugs, groups=b.groups, excerpt=b.excerpt) for b in BLOCKS]
    meta = DocumentMeta("venta", VENTA_SOURCE_URL, VENTA_SOURCE_DOC, VENTA_VALID_FROM, VENTA_PROTOCOL if apply else {})
    write_requirement_drafts(meta, drafts, apply)


def selftest() -> None:
    all_slugs = [slug for b in BLOCKS for slug in b.slugs]
    assert len(all_slugs) == len(set(all_slugs)), "один слаг в двух блоках"
    assert len(all_slugs) == 9, len(all_slugs)
    assert not set(all_slugs) & {slug for slug, _ in NOT_TAKEN}
    # иностранный язык у Ventspils — именно английский, не группа
    assert all(["english"] in b.groups for b in BLOCKS)
    assert not any("german" in group for b in BLOCKS for group in b.groups)
    # необязательная физика и вступительное испытание — не требования
    assert all(["physics"] not in b.groups for b in BLOCKS)
    print("самотест пройден")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        report()
        seed(apply="--apply" in sys.argv)
