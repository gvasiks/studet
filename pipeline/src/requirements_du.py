"""Требования к экзаменам DU — план 2026-09-21, пункт 02, порция 1.

Как и requirements_lbtu.py, это НЕ парсер: документ смешивает в одной
таблице ДВЕ принципиально разные модели приёма, и годится только одна из
них. pypdf.extract_text() (обычный режим) читает таблицу построчно без
проблем со слитыми ячейками (в отличие от LBTU) — но сама классификация
"CE-модель или нет" требует прочитать каждую программу, автоматика тут
не поможет.

Источник: DU «Studiju iespējas» — коэффициенты по программам пилна/непилна
laika pamatstudijām (DU Senāta 21.10.2025. protokols Nr. 15, grozījumi līdz
05.08.2026. protokols Nr. 10) —
docs/source-documents/du/studiju-iespejas-pamatstudijas-2026-27-08-2026.pdf
https://du.lv/wp-content/uploads/2026/08/Stud_iesp_pil_nep_laika_pamatstudijam_08_2026.pdf

Две модели в документе:
1. **CE-модель** (большинство программ): таблица "Uzņemšanas prasības un
   noteikumi" с обязательными CE latviešu valodā / pirmajā svešvalodā /
   matemātikā (+ visu CE kopvērtējumu vidējā vērtība — не предмет, не
   берём) и отдельным "Papildu punkti tiks piešķirti par" — необязательные
   бонусные предметы, не гейтят допуск, тоже не берём.
2. **Аттестатная модель** (педагогические программы — Pirmsskolas
   skolotājs, Sākumizglītības skolotājs, Skolotājs): допуск считается по
   средней годовой оценке аттестата в профильных предметах (у "Skolotājs"
   — по одному из ~20 модулей специализации, напр. "matemātikas skolotājs"
   / "dabaszinātņu skolotājs") плюс вступительное собеседование 50%+ веса;
   CE — не главный критерий (10-20% формулы), а один из компонентов.
   Записать это как "нужен CE X" было бы неверным фактом (человек может
   пройти без данного CE), поэтому эти 3 программы не берутся вовсе — не
   "неполно", а "другая модель", их и не пытаемся втиснуть.

19 строк документа (все CE-модель, 22 слага каталога — 5 программ на
LV/EN парах) сведены к одному и тому же набору: latviešu valoda + pirmā
svešvaloda + matemātika. Ни у одной CE-программы нет дополнительного
ОБЯЗАТЕЛЬНОГО предметного CE сверх этих трёх (везде это "Papildu punkti" —
бонус, не допуск, либо доп.предмет вообще не CE — вроде "Eksāmens atestātā:
ģeogrāfijā" у Vides zinātne). Совпадение — не ошибка транскрипции, а то,
что реально написано в документе.

Каталожные слаги подобраны по (name_lv/name_en, degree_level) — у DU много
одноимённых программ разных уровней (бакалавр/магистр/докторантура),
взят только уровень, соответствующий документу (bachelor, у Elektronika/
Informācijas tehnoloģijas 2-gadu programmas/Civilā drošība — college,
т.к. это īsā cikla программы). Два слага — "Eastern European Culture and
Business Relations" (документ: «Austrumeiropas kultūras sakari un
integrācijas procesi») и "Grafikas dizains" (документ: «Dizains», но
квалификация "grafikas dizainera" совпадает) — сопоставлены по смыслу,
точного текстового совпадения названия нет; при появлении сомнений
сверить с самим университетом.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from formula_drafts import DocumentMeta, RequirementDraft, write_requirement_drafts

SOURCE_URL = (
    "https://du.lv/wp-content/uploads/2026/08/"
    "Stud_iesp_pil_nep_laika_pamatstudijam_08_2026.pdf"
)
SOURCE_DOC = (
    "DU «Studiju iespējas» pilna un nepilna laika pamatstudijām (DU Senāta "
    "21.10.2025. protokols Nr. 15, grozījumi līdz 05.08.2026. protokols Nr. 10)"
)
VALID_FROM = date(2025, 10, 21)
COPY_PATH = "docs/source-documents/du/studiju-iespejas-pamatstudijas-2026-27-08-2026.pdf"

BASE_GROUPS: list[list[str]] = [["latvian"], ["english"], ["mathematics"]]


@dataclass
class DuBlock:
    name: str
    slugs: list[str]
    excerpt: str


BLOCKS: list[DuBlock] = [
    DuBlock(
        "Bioloģija (43421, D0134)",
        ["biology"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE bioloģijā, CE ķīmijā.",
    ),
    DuBlock(
        "Ķīmija (43441, D01BN)",
        ["chemistry"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE bioloģijā, CE ķīmijā.",
    ),
    DuBlock(
        "Vides zinātne (43431, D0138)",
        ["environmental-science-lv", "environmental-science-en"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE bioloģijā, CE ķīmijā, "
        "eksāmens atestātā ģeogrāfijā.",
    ),
    DuBlock(
        "Fizioterapija (42722, D0154)",
        ["niid-85"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE bioloģijā, CE ķīmijā.",
    ),
    DuBlock(
        "Informācijas tehnoloģijas (42484, D01B9, 4 gadi)",
        ["niid-86"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE programmēšanā, "
        "eksāmens/ieskaite atestātā informātikā/lietišķajā informātikā.",
    ),
    DuBlock(
        "Informācijas tehnoloģijas (41483, D01BR, 2 gadi, īsā cikla)",
        ["niid-20027"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE fizikā, CE "
        "programmēšanā, eksāmens/ieskaite atestātā informātikā/lietišķajā informātikā.",
    ),
    DuBlock(
        "Māszinības (42723, D01BZ)",
        ["niid-26597"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE bioloģijā, "
        "eksāmens/ieskaite atestātā vai atestāta atzīme bioloģijā/dabaszinībās.",
    ),
    DuBlock(
        "Elektronika (41523, 2 gadi, īsā cikla)",
        ["niid-28602"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE fizikā, CE programmēšanā.",
    ),
    DuBlock(
        "Valodu un kultūras studijas (43226, D02DO)",
        ["language-and-culture-studies"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. (skat. DU Uzņemšanas noteikumi, "
        "punkts 4.8., 4.9. — nesatur papildu obligātus CE-priekšmetus.)",
    ),
    DuBlock(
        "Vēsture (43228, D02D4)",
        ["history"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE vēsturē, eksāmens "
        "atestātā ģeogrāfijā/politikā un tiesībās/filosofijā/kultūras vēsturē.",
    ),
    DuBlock(
        "Austrumeiropas kultūras sakari un integrācijas procesi (43227, D02DP)",
        ["eastern-european-cultural-and-business-relations"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE vēsturē, eksāmens "
        "atestātā kultūras vēsturē vai kulturoloģijā.",
    ),
    DuBlock(
        "Dizains (42214, D04A7)",
        ["niid-19888"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE programmēšanā, "
        "atestāta atzīme (kvalifikācijas darbs, informātika, kultūras vēsture).",
    ),
    DuBlock(
        "Mākslas menedžments (42345, D04A3)",
        ["niid-88"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: atestāta atzīme "
        "kultūras vēsturē vai kulturoloģijā.",
    ),
    DuBlock(
        "Stratēģiskie riski un krīžu pārvaldība (43861, D3105)",
        ["strategic-risks-and-crisis-management"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība.",
    ),
    DuBlock(
        "Mūzika (42212, D04A8)",
        ["niid-26827-lv", "niid-26827-en"],
        "Iestājpārbaudījumi: eksāmens specialitātē, kolokvijs specialitātē. "
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Kopējais vērtējums (100%) veidojas no "
        "iestājpārbaudījuma specialitātē (30%) un kolokvijā (30%), vērtējumiem "
        "centralizētajos eksāmenos latviešu valodā (10%), svešvalodā (10%) un "
        "matemātikā (10%), visu CE kopvērtējumu vidējā vērtība (10%).",
    ),
    DuBlock(
        "Biznesa un finanšu procesi (42311, D1270)",
        ["niid-25729-lv", "niid-25729-en"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: eksāmens/ieskaite "
        "atestātā ekonomikā vai biznesa ekonomiskajos pamatos.",
    ),
    DuBlock(
        "Tiesību zinātne (43380, D1267)",
        ["science-of-law"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE vēsturē.",
    ),
    DuBlock(
        "Psiholoģija (43313, D1240)",
        ["psychology"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība. Papildu punkti: CE bioloģijā.",
    ),
    DuBlock(
        "Civilā drošība un aizsardzība (41861, D1261, 2 gadi, īsā cikla)",
        ["niid-7050"],
        "Centralizētais eksāmens: latviešu valodā, pirmajā svešvalodā, matemātikā, "
        "visu CE kopvērtējumu vidējā vērtība.",
    ),
]

NOT_TAKEN = [
    ("Pirmsskolas skolotājs (41141, D139P)", "niid-25833",
     "аттестатная модель (20% средняя оценка + 50% собеседование), CE — не главный критерий"),
    ("Sākumizglītības skolotājs (42141, D139S)", "niid-26442",
     "аттестатная модель, та же формула, что у Pirmsskolas skolotājs"),
    ("Skolotājs (42141, D139T)", "niid-94",
     "аттестатная модель по модулю специализации (~20 вариантов) + 60% вступительные испытания"),
]


def report() -> None:
    print(f"блоков (групп программ): {len(BLOCKS)}; программ (слагов) всего: {sum(len(b.slugs) for b in BLOCKS)}")
    print(f"не взято (другая модель приёма, не CE): {len(NOT_TAKEN)}")
    for name, slug, why in NOT_TAKEN:
        print(f"  [{name}] {slug}: {why}")


def seed(apply: bool) -> None:
    drafts = [RequirementDraft(block=b.name, slugs=b.slugs, groups=BASE_GROUPS, excerpt=b.excerpt) for b in BLOCKS]
    protocol = {}
    if apply:
        from seed_formulas import source_protocol

        protocol = source_protocol(
            number="15 (grozījumi: protokols Nr. 10)",
            doc_date=date(2026, 8, 5),
            copy_path=COPY_PATH,
            fetched_on=date(2026, 9, 20),
        )
    write_requirement_drafts(DocumentMeta("du", SOURCE_URL, SOURCE_DOC, VALID_FROM, protocol), drafts, apply)


def selftest() -> None:
    all_slugs = [slug for b in BLOCKS for slug in b.slugs]
    assert len(all_slugs) == len(set(all_slugs)), "один слаг попал в два разных блока — ошибка сопоставления"
    assert all(b.slugs for b in BLOCKS), "у блока нет ни одной программы"
    assert len(BLOCKS) == 19, len(BLOCKS)
    assert sum(len(b.slugs) for b in BLOCKS) == 22, sum(len(b.slugs) for b in BLOCKS)
    not_taken_slugs = [slug for _, slug, _ in NOT_TAKEN]
    assert not (set(all_slugs) & set(not_taken_slugs)), "программа и взята, и исключена одновременно"
    print("самотест пройден")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        report()
        seed(apply="--apply" in sys.argv)
