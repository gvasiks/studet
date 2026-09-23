"""Требования к экзаменам LBTU — план 2026-09-21, пункт 02, порция 1.

В отличие от requirements_lu.py/requirements_rsu.py, это НЕ парсер: таблица
раздела 3 документа — PDF со слитыми по вертикали ячейками (несколько
программ на одной строке делят один блок требований на несколько строк
ниже), обычное построчное извлечение текста (pypdf, режим по умолчанию)
эту границу теряет и может приписать чужой блок соседней программе. Поэтому
таблица прочитана в режиме "layout" (`page.extract_text(
extraction_mode="layout")`, сохраняет расположение по колонкам как в PDF)
и сверена построчно глазами — см. source_excerpt каждого блока ниже,
дословный текст (без "layout"-отступов) левого столбца "CE" таблицы.
Каталожные слаги подобраны по (name_lv/name_en, degree_level='bachelor',
у Būvniecība дополнительно 'college', у Veterinārmedicīna — единственная
программа с этим именем и degree_level='master' в каталоге, хотя документ
называет её "2. cikla p." — тот же профессиональный второй цикл).

Источник: "Uzņemšanas noteikumi pamatstudijās, ņemot vērā centralizēto
eksāmenu rezultātus 2026./2027. studiju gadam" (LBTU Senāta 12.11.2025.
lēmums Nr. 12-62, redakcija 12.05.2026.) —
docs/source-documents/lbtu/uznemsanas-noteikumi-pamatstudijas-2026-27-arce-12052026.pdf
https://www.lbtu.lv/sites/default/files/2026-05/Uznemsanas_noteikumi_pamatstudijas_2026_2027_arCE_12052026.pdf

Что взято: только "Obligātās" (обязательные) предметы из столбца
"Personām, kuras vidējo izglītību ieguvušas, sākot no 2004. gada" (п. 2.6.1:
CE latviešu valodā, CE svešvalodā, CE matemātikā — обязательны для ВСЕХ
программ LBTU без исключения; это фактическая аудитория продукта —
нынешние школьники). Столбец для получивших образование до 2004 года или
освобождённых от CE не берётся: это другая, аттестатная модель.

Что НЕ взято и почему:
- "Papildus, ja ir: …" — необязательные предметы. Они дают надбавку к
  формуле, ЕСЛИ сданы, но их отсутствие не блокирует допуск — это не
  "нужен", а "если есть", для programme_requirement (гейт допуска) не
  годится.
- 2 обязательных слагаемых, где CE — не единственный вариант: LPTF
  "Pārtikas kvalitāte un inovācijas" / "Pārtikas produktu tehnoloģija" —
  "CE ķīmijā VAI GA ķīmijā VAI dabas zinībās"; VMF "Veterinārmedicīna" —
  "CE VAI GA bioloģijā", "CE VAI GA ķīmijā". Два из трёх (или один из двух)
  вариантов — аттестатная оценка, не CE; честно записать как "нужен CE X"
  нельзя (человек может пройти и без него), а записать частично («предмет
  нужен, но не обязательно через CE») текущая схема programme_requirement
  не различает. Поэтому оба этих обязательных слагаемых остаются
  неразобранными — см. NOT_RESOLVED ниже, они не попадают в базу.

После этого исключения ВСЕ 16 групп программ сводятся к одному и тому же
набору (latviešu valoda + svešvaloda + matemātika) — это не ошибка
транскрипции: только у этих двух программ был доп. обязательный предмет,
и оба раза это оказался как раз неразбираемый CE-или-аттестат случай.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from formula_drafts import DocumentMeta, RequirementDraft, write_requirement_drafts

SOURCE_URL = (
    "https://www.lbtu.lv/sites/default/files/2026-05/"
    "Uznemsanas_noteikumi_pamatstudijas_2026_2027_arCE_12052026.pdf"
)
SOURCE_DOC = (
    "Uzņemšanas noteikumi pamatstudijās, ņemot vērā centralizēto eksāmenu "
    "rezultātus 2026./2027. studiju gadam (LBTU Senāta 12.11.2025. lēmums "
    "Nr. 12-62, redakcija 12.05.2026.)"
)
VALID_FROM = date(2025, 11, 12)
COPY_PATH = "docs/source-documents/lbtu/uznemsanas-noteikumi-pamatstudijas-2026-27-arce-12052026.pdf"

BASE_GROUPS: list[list[str]] = [["latvian"], ["english"], ["mathematics"]]


@dataclass
class LbtuBlock:
    name: str
    slugs: list[str]
    excerpt: str
    # для программ, где обязательный CE-предмет сверх базовых трёх не
    # выражается моделью (CE-или-аттестат) — не попадает в groups, но
    # фиксируется тут для report()/аудита
    not_resolved: str | None = None


BLOCKS: list[LbtuBlock] = [
    LbtuBlock(
        "ESAF: Ekonomika, a(b) / Komercdarbība un uzņēmuma vadība, p(b)",
        ["niid-211", "niid-157"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE sociālajās zinātnēs.",
    ),
    LbtuBlock(
        "ESAF: Organizāciju un sabiedrības pārvaldes socioloģija, a(b)",
        ["sociology_of_organizations_and_public_administration"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE sociālajās zinātnēs.",
    ),
    LbtuBlock(
        "IITF: Biosistēmu mašinērija un tehnoloģijas, a(b)",
        ["biosystems_machinery_and_technologies"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE fizikā.",
    ),
    LbtuBlock(
        "IITF: Datorvadība un datorzinātne, a(b)",
        ["niid-209"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE fizikā, CE programmēšanā, CE dizainā un tehnoloģijā.",
    ),
    LbtuBlock(
        "IITF: Dizains un amatniecība, p(b)",
        ["niid-22570"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE dizainā un tehnoloģijā, CE kultūrā un mākslā.",
    ),
    LbtuBlock(
        "IITF: Informācijas tehnoloģijas ilgtspējīgai attīstībai, p(b)",
        ["information-technologies-for-sustainable-development"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE fizikā, CE programmēšanā, CE dizainā un tehnoloģijā.",
    ),
    LbtuBlock(
        "IITF: Lauksaimniecības inženierzinātne, a(b) / Lietišķā enerģētika, p(b) / "
        "Mašīnu projektēšana un ražošana, p(b)",
        ["niid-208", "niid-226", "niid-170"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE fizikā.",
    ),
    LbtuBlock(
        "LPTF: Ēdināšanas un viesnīcu vadība, p(b)",
        ["niid-155-lv", "niid-155-en"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE bioloģijā vai CE dabas zinībās.",
    ),
    LbtuBlock(
        "LPTF: Lauksaimniecība, p(b)",
        ["niid-228"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE bioloģijā.",
    ),
    LbtuBlock(
        "LPTF: Pārtikas kvalitāte un inovācijas, a(b) / Pārtikas produktu tehnoloģija, p(b)",
        ["niid-224-lv", "niid-224-en", "niid-261"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā, "
        "CE ķīmijā vai GA ķīmijā vai dabas zinībās. "
        "Papildus, ja ir: CE bioloģijā vai CE dabas zinībās.",
        not_resolved="обязательное «CE ķīmijā vai GA ķīmijā vai dabas zinībās» — два из трёх вариантов не CE",
    ),
    LbtuBlock(
        "MVZF: Būvniecība, p(b), īsā cikla p.",
        ["niid-230", "niid-20868"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE fizikā, CE programmēšanā.",
    ),
    LbtuBlock(
        "MVZF: Ģeoinformātika un tālizpēte, p(b)",
        ["niid-26833"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE fizikā.",
    ),
    LbtuBlock(
        "MVZF: Kokapstrāde, p(b)",
        ["niid-260"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE fizikā.",
    ),
    LbtuBlock(
        "MVZF: Mežinženieris, p(b) / Mežzinātne, a(b)",
        ["niid-227", "niid-220"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā.",
    ),
    LbtuBlock(
        "MVZF: Vide un ūdenssaimniecība, p(b) / Zemes ierīcība un mērniecība, p(b)",
        ["niid-262", "niid-231-lv", "niid-231-en"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā. "
        "Papildus, ja ir: CE fizikā.",
    ),
    LbtuBlock(
        "VMF: Veterinārmedicīna, 2. cikla p.",
        ["niid-186-lv", "niid-186-en"],
        "Obligātās: CE latviešu valodā, CE svešvalodā, CE matemātikā, "
        "CE vai GA bioloģijā, CE vai GA ķīmijā.",
        not_resolved="обязательные «CE vai GA bioloģijā» и «CE vai GA ķīmijā» — не CE-only",
    ),
]


def report() -> None:
    print(f"блоков (групп программ): {len(BLOCKS)}; программ (слагов) всего: {sum(len(b.slugs) for b in BLOCKS)}")
    for b in BLOCKS:
        if b.not_resolved:
            print(f"  [{b.name}] обязательный CE-предмет сверх базовых трёх не взят: {b.not_resolved}")


def seed(apply: bool) -> None:
    drafts = [RequirementDraft(block=b.name, slugs=b.slugs, groups=BASE_GROUPS, excerpt=b.excerpt) for b in BLOCKS]
    protocol = {}
    if apply:
        from seed_formulas import source_protocol

        protocol = source_protocol(
            number="12-62",
            doc_date=date(2026, 5, 12),
            copy_path=COPY_PATH,
            fetched_on=date(2026, 9, 20),
        )
    write_requirement_drafts(DocumentMeta("lbtu", SOURCE_URL, SOURCE_DOC, VALID_FROM, protocol), drafts, apply)


def selftest() -> None:
    all_slugs = [slug for b in BLOCKS for slug in b.slugs]
    assert len(all_slugs) == len(set(all_slugs)), "один слаг попал в два разных блока — ошибка сопоставления"
    assert all(b.slugs for b in BLOCKS), "у блока нет ни одной программы"
    assert len(BLOCKS) == 16, len(BLOCKS)
    assert sum(len(b.slugs) for b in BLOCKS) == 27, sum(len(b.slugs) for b in BLOCKS)
    assert sum(1 for b in BLOCKS if b.not_resolved) == 2
    print("самотест пройден")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        report()
        seed(apply="--apply" in sys.argv)
