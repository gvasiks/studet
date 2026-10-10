"""Черновики «где подать документы» — канал подачи вуза по уровням.

Решение владельца 2026-10-05: на карточке программы — ссылка, где подать
документы в этот вуз. Таблица application_channel (миграция
20261005120000). «Через кого подача» — поле правила 6 CLAUDE.md, поэтому
скрипт пишет ТОЛЬКО ЧЕРНОВИКИ: verified_at проставляет человек в Studio,
и до этого сайт ссылку не показывает.

Данные ниже собраны вручную 2026-10-05 со страниц приёма самих вузов и с
vienotauznemsana.lv (разведочные скрипты — в рабочей папке сессии, не в
репозитории). Каждая запись — (вуз, уровни) -> тип подачи, ссылка, страница-
источник и дословная цитата. Где цитаты нет (excerpt=None), страница приёма
найдена по ссылке «Uzņemšana» с главной страницы вуза, но фразы о порядке
подачи на ней автоматически не нашлось: такие записи проверяются глазами в
первую очередь (docs/checks/APPLICATION-CHANNELS-REVIEW.md).

levels=[None] — запись для всех уровней вуза; запись с конкретным уровнем
имеет приоритет над ней (src/lib/application-channel.ts).

Осень — межсезонье: у части вузов на страницах приёма написано, что набор
закончен, а порядок на следующий год появится позже. Вузы публикуют правила
до 30 ноября — в декабре записи надо пересмотреть, в том числе состав
участников единой подачи (он объявляется на каждый год заново).

  python src/seed_application_channels.py            # показать, что будет записано
  python src/seed_application_channels.py --apply    # записать черновики
  python src/seed_application_channels.py --review   # таблица для проверки (Markdown)
  python src/seed_application_channels.py --selftest # проверка самой таблицы, без сети и базы

Уже подтверждённые строки скрипт не трогает: иначе повторный запуск
переписал бы ссылку под сохранившейся пометкой «проверено».
"""

from __future__ import annotations

import sys
from urllib.parse import urlparse

LEVELS = ("college", "bachelor", "master", "doctoral")
CHANNEL_TYPES = ("unified_portal", "university")

# Единая подача на основные (pamatstudiju) программы: одна заявка через
# услугу на государственном портале. Состав участников — за 2026 год.
UNIFIED = {
    "type": "unified_portal",
    "url": "https://latvija.gov.lv/Services/54419",
    "source_url": "https://vienotauznemsana.lv/",
    "excerpt": (
        "Vienoto uzņemšanu rīkoja Ekonomikas un kultūras augstskola, Daugavpils Universitāte, Latvijas "
        "Biozinātņu un tehnoloģiju universitāte, Latvijas Universitāte, Rīgas Tehniskā universitāte, Rīgas "
        "Ziemeļvalstu augstskola, Ventspils Augstskola un Vidzemes Augstskola. […] Pieteikties elektroniski var "
        "[…] vienotajā valsts pārvaldes pakalpojumu portāla e-pakalpojumā “Elektroniskā pieteikšanās studijām "
        "pamatstudiju programmās”. (otrais teikums — no vienotauznemsana.lv/daliba/ka-pieteikties/)"
    ),
}


def own(url: str, source_url: str | None = None, excerpt: str | None = None, note: str | None = None) -> dict:
    """Подача в сам вуз: url — страница или система вуза, где подают документы."""
    return {"type": "university", "url": url, "source_url": source_url or url, "excerpt": excerpt, "note": note}


# (university.slug, уровни, запись). note — пометка для проверяющего, в базу не идёт.
CHANNELS: list[tuple[str, list[str | None], dict]] = [
    # ---------- участники единой подачи (бакалавриат и короткий цикл) ----------
    ("lu", ["bachelor", "college"], UNIFIED),
    ("rtu", ["bachelor", "college"], UNIFIED),
    ("lbtu", ["bachelor", "college"], UNIFIED),
    ("du", ["bachelor", "college"], UNIFIED),
    ("venta", ["bachelor", "college"], UNIFIED),
    ("via", ["bachelor"], UNIFIED),
    ("eka", ["bachelor", "college"], UNIFIED),
    (
        "rnu",
        ["bachelor", "college"],
        {**UNIFIED, "note": "У RNU есть и собственная форма apply.rnu.lv («Aizpildi RNU tiešsaistes pieteikuma formu») — проверить, что для бакалавриата верна единая подача."},
    ),
    # ---------- остальные уровни этих вузов ----------
    (
        "lu",
        ["master"],
        own(
            "https://www.lu.lv/gribustudet/uznemsanas-kartiba/magistra-limena-studijas/",
            note="На 2026-10-05 страница сообщает, что набор закончен, сведения на 2027/28 появятся позже.",
        ),
    ),
    ("lu", ["doctoral"], own("https://doktorantura.lu.lv/uznemsana/")),
    (
        "rtu",
        ["master"],
        own(
            "https://www.rtu.lv/lv/studijas/uznemsana/pieteiksanas-magistra-limena-studijam",
            excerpt=(
                "Dokumentu iesniegšana maksas studiju vietās otrā cikla augstākās izglītības (maģistra) studiju "
                "programmās norisinās elektroniski un klātienē RTU Uzņemšanas un servisa nodaļas darba laikā"
            ),
        ),
    ),
    (
        "rtu",
        ["doctoral"],
        own(
            "https://www.rtu.lv/lv/studijas/doktora-limena-studijas/uznemsana-doktora/uznemsanas-process",
            excerpt=(
                "Piesakoties doktorantūras vakancei, gan pretendenti uz budžeta vietām, gan tie, kuri plāno studēt "
                "par fizisko un juridisko personu līdzekļiem, iesniedz visus nepieciešamos dokumentus […], nosūtot "
                "tos uz e‑pastu: doktorantura@rtu.lv."
            ),
        ),
    ),
    ("lbtu", [None], own("https://www.lbtu.lv/lv/uznemsana-latvijas-biozinatnu-un-tehnologiju-universitate-lbtu", note="Общая страница приёма; для магистратуры на ней ссылка «pieteikuma anketa» (lbtu.lv/lv/pieteiksanas/magistriem).")),
    ("du", [None], own("https://du.lv/gribu-studet/uznemsana/", note="Общая страница «Uzņemšana 2026. gadā» с правилами приёма по уровням (PDF).")),
    ("via", [None], own("https://va.lv/uznemsana", note="Общая страница приёма; для иностранцев там же ссылка на va.dreamapply.com.")),
    ("eka", [None], own("https://www.augstskola.lv/?parent=96&lng=lva", note="Страница «Uzņemšanas prasības» найдена по ссылке с главной; фразы о порядке подачи не нашлось.")),
    (
        "rnu",
        [None],
        own(
            "https://rnu.lv/uznemsana/pieteiksanas-kartiba/",
            excerpt="Aizpildi RNU tiešsaistes pieteikuma formu. […] Iesniedz dokumentus elektroniski vai klātienē atbilstoši Uzņemšanas komisijas norādījumiem.",
        ),
    ),
    (
        "venta",
        ["master"],
        own(
            "https://www.venta.lv/pieteiksanas-magistra-studiju-programmam",
            excerpt=(
                "sūtot elektroniski parakstītu pieteikumu uz e-pastu studijas@venta.lv vai papīrā pašrocīgi parakstītu "
                "pa pastu uz adresi Inženieru iela 101, Ventspils, LV-3601, adresējot to Ventspils Augstskolas "
                "Uzņemšanas komisijai."
            ),
            note="Страница «Kā pieteikties maģistra studijām?»; ссылка на неё — со страниц магистерских программ.",
        ),
    ),
    # ---------- RSU: собственная система на всех уровнях ----------
    (
        "rsu",
        ["bachelor", "college"],
        own(
            "https://uznemsana.rsu.lv/",
            source_url="https://www.rsu.lv/studiju-iespejas/uznemsana-pamatstudiju-programmas",
            excerpt="RSU e-Uzņemšanā ir iespējams pieteikties tikai ar Latvija.lv autorizācijas starpniecību.",
            note="RSU нет в списке участников единой подачи 2026 года.",
        ),
    ),
    (
        "rsu",
        ["master"],
        own(
            "https://uznemsana.rsu.lv/",
            source_url="https://www.rsu.lv/uznemsana-magistra-studiju-programmas",
            excerpt="Pēc apstiprinājuma e-pasta saņemšanas tev ir jāatgriežas savā elektroniskajā pieteikumā (RSU e-Uzņemšanā) un no savas puses jāapstiprina pieteikums.",
        ),
    ),
    (
        "rsu",
        ["doctoral"],
        own(
            "https://uznemsana.rsu.lv/",
            source_url="https://www.rsu.lv/uznemsana-doktorantura",
            excerpt="Elektroniskā pieteikšanās studijām 3.08.–25.09. plkst. 16",
        ),
    ),
    # ---------- академии и частные вузы ----------
    ("lka", [None], own("https://lka.edu.lv/lv/gribu-studet-akademija/")),
    (
        "lma",
        ["master"],
        own(
            "https://apply.lma.lv/",
            excerpt=(
                "Sveicam, Latvijas Mākslas akadēmijas elektroniskās reģistrēšanās sistēmā! […] Reģistrēšanās un "
                "pieteikšanās studijām Latvijas Mākslas akadēmijas maģistra programmā 2026./2027. studiju gadā no "
                "1. aprīļa plkst.12:00 līdz 9. jūlija plkst. 23:59"
            ),
            note="В меню lma.lv раздела приёма нет; сюда ведёт кнопка «PIETEIKTIES STUDIJĀM» со страниц специальностей.",
        ),
    ),
    (
        "lma",
        ["bachelor"],
        own(
            "https://apply.lma.lv/",
            excerpt="Sveicam, Latvijas Mākslas akadēmijas elektroniskās reģistrēšanās sistēmā!",
            note="Тексты на странице говорят о магистратуре. Что бакалавриат подаётся там же — НЕ подтверждено; проверить по правилам приёма бакалавриата на lma.lv.",
        ),
    ),
    ("jvlma", [None], own("https://www.jvlma.lv/studijas/uznemsana", note="На странице — ссылки на формы заявлений (Google Forms) и документы по уровням.")),
    (
        "lnaa",
        [None],
        own(
            "https://www.klustikaravirs.lv/pieteikties",
            source_url="https://www.naa.mil.lv/lv",
            excerpt="Latvijas pilsoņi no 18 gadiem var pieteikties dažādiem dienestiem un apmācībām, aizpildot pieteikuma anketu tiešsaistē.",
            note="Ссылка «Piesakies» с главной страницы LNAA ведёт на klustikaravirs.lv; цитата — оттуда.",
        ),
    ),
    (
        "turiba",
        [None],
        own(
            "https://www.turiba.lv/lv/uznemsana",
            excerpt="Aizpildi elektronisko pieteikšanās formu. […] Sagatavo iesniedzamos dokumentus un dodies uz augstskolu vai iesniedz tos attālināti, ja tev ir drošs elektroniskais paraksts.",
        ),
    ),
    (
        "riseba",
        [None],
        own(
            "https://riseba.lv/nac-studet/ka-pieteikties-studijam/",
            excerpt="Pietiekties studijām var gan tiešsaistē, gan arī klātienē, ierodoties augstskolā.",
        ),
    ),
    (
        "tsi",
        [None],
        own(
            "https://tsi.lv/future-students/admission/",
            excerpt="Applications are made online, at the official admission portal admission.tsi.lv. Submit your documents electronically in just a few clicks!",
        ),
    ),
    (
        "bsa",
        [None],
        own(
            "https://bsa.edu.lv/index.php/lv/uznemsana/e-pieteikums-studijam.html",
            excerpt="Pieteikumu iesniegšana, aizpildot elektronisko veidlapu un augšupielādējot nepieciešamos dokumentus:",
        ),
    ),
    ("rgsl", [None], own("https://apply.rgsl.edu.lv/", source_url="https://www.rgsl.edu.lv/", note="Ссылка «Apply» в шапке сайта RGSL.")),
    (
        "sse-riga",
        ["bachelor"],
        own("https://www.sseriga.edu/education/bachelor/admission", excerpt="Step 1: Submit the Online Application by April 6, 2027"),
    ),
    (
        "rai",
        [None],
        own(
            "https://rai.lv/news/uznemsana/uznemsana-2026-2027/tiessaites-pieteikuma-forma/",
            source_url="https://rai.lv/news/uznemsana/uznemsana-2026-2027/",
            note="Адрес с годом набора (2026-2027) — в следующем сезоне сменится.",
        ),
    ),
    ("ekra", [None], own("https://kra.lv/studiju-programmas/studentu-uznemsana/", excerpt="Aizpildi elektronisko Pieteikuma veidlapu")),
    ("lutera", [None], own("https://luteraakademija.lv/?ct=uznemsana")),
    ("rarzi", [None], own("https://www.rarzi.lv/uz%C5%86em%C5%A1ana", note="На странице — анкеты бакалавра и магистра (Google Docs).")),
    ("rti", [None], own("https://garigais.lv/programma/", note="Кнопка «PIETEIKTIES» ведёт на страницу контактов; правила приёма — PDF 2023 года.")),
    # ---------- колледжи ----------
    ("alberta", [None], own("https://www.alberta-koledza.lv/?parent=19&lng=lva", note="На странице ссылка на систему pieteikumi.alberta-koledza.lv.")),
    (
        "bvk",
        [None],
        own(
            "https://www.bvk.lv/uznemsana/",
            excerpt="Uzņemšanai nepieciešamos dokumentus iesniedz elektroniski – bvk@bvk.lv vai BVK birojā Rīgas centrā, Alberta ielā 13, iepriekš saskaņajot ierašanās laiku.",
        ),
    ),
    (
        "dmk",
        [None],
        own(
            "https://dmk.lv/uznemsanas-noteikumi/",
            excerpt="Pieteikšanās studijām īsā cikla profesionālās Augstākās izglītības programmās 2026./2027. akadēmiskajam gadam notiks klātienē",
        ),
    ),
    ("gfk", [None], own("https://www.koledza.lv/index.php/lv/uznemsana", excerpt="Pieteikšanās studijām elektroniski no 2. aprīļa")),
    ("hotel-school", [None], own("https://hotelschool.lv/prasibas-reflektantiem/", note="На странице ссылка на форму hotelschool.lv/tiessaistes-pieteikuma-forma/.")),
    (
        "juridiska-koledza",
        [None],
        own(
            "https://jk.lv/uznemsana/uznemsana/iesniedzamie-dokumenti/",
            excerpt="Pieteikšanās studijām notiek elektroniski. […] Lūdzu, aizpildiet pieteikuma veidlapu elektroniski!",
        ),
    ),
    (
        "malnavas-koledza",
        [None],
        own(
            "https://malnavaskoledza.lv/lv/uznemsana-isa-cikla-profesionala-augstaka-izglitiba",
            excerpt=(
                "Dokumentus var iesniegt klātienē, ierodoties LBTU Malnavas koledžas Studiju daļā, 63. kabinetā […] "
                "vai elektroniski, parakstītus ar drošu elektronisko parakstu, nosūtot uz e-pasta adresi"
            ),
        ),
    ),
    ("psmk", [None], own("https://psk.lu.lv/uznemsanas-noteikumi")),
    ("r1mk", [None], own("https://www.rmk1.lv/lv/studiju-iespejas/uznemsana/")),
    (
        "rbk",
        [None],
        own(
            "https://www.rck.lv/augstaka-izglitiba/uznemsana/",
            excerpt="DOKUMENTU IESNIEGŠANA ELEKTRONISKI LĪDZ 2026. GADA 6.SEPTEMBRIM […] Piesakies studijām un iesniedz dokumentus šeit;",
        ),
    ),
    (
        "rmenk",
        [None],
        own(
            "https://college.lv/uznemsanas-kartiba/",
            excerpt="Lai pieteiktos studijām reflektantam ir jāaizpilda elektroniskā pieteikuma forma pievienojot visus nepieciešamos dokumentus.",
        ),
    ),
    ("rmk", [None], own("https://rmkoledza.lu.lv/lv/nac-studet/")),
    ("rtk", [None], own("https://www.rtk.lv/lv/uznemsana-koledza")),
    ("siva", [None], own("https://www.siva.gov.lv/lv/izglitibas-programmas")),
    ("skmk", [None], own("https://rcmc.lv/studiju-programmas/pieteiksanas-studijam/", note="Заголовок страницы — «Pieteikšanās studijām».")),
    ("ucak", [None], own("https://www.ucak.vugd.gov.lv/lv/uznemsana-studijam-0", note="Заголовок страницы — «Uzņemšana studijām».")),
    ("vpk", [None], own("https://www.policijas.koledza.gov.lv/lv/uznemsanas-noteikumi-0", note="На странице ссылка «elektroniskais pieteikums» (e-studijas.vp.gov.lv/uznemsana).")),
    ("ljk", [None], own("https://ljk.lv/uznemsana", note="На главной ljk.lv рядом — ссылка «UZŅEMŠANAS ANKETA» (registracija.ljk.lv). 2026-10-05 сайт сначала не отвечал (HTTP 522), потом открылся.")),
    (
        "vrsk",
        [None],
        own(
            "https://www.vrk.rs.gov.lv/lv/isa-cikla-profesionalas-augstakas-izglitibas-programma-robezapsardze",
            excerpt="Uzņemšanas noteikumi pilna un nepilna laika studijām Valsts robežsardzes koledžā 2026.gadā",
            note="Страница программы короткого цикла «Robežapsardze»; цитата — название документа с правилами приёма на ней. Порядок подачи — в самих правилах.",
        ),
    ),
]

# Для этих учреждений черновика нет — и почему. Попадает в отчёт --review.
NOT_COLLECTED = {
    "novikonta": (
        "страницы колледжа на novikontas.org отдают 404 — и адрес из базы (/college/lv), и ссылка «Novikontas "
        "Academy» с главной страницы самого сайта, и /college/lv/ka_iestaties, которую показывает поиск"
    ),
}


def rows() -> list[dict]:
    """Развернуть таблицу: по одной строке на (вуз, уровень)."""
    result = []
    for slug, levels, entry in CHANNELS:
        for level in levels:
            result.append(
                {
                    "slug": slug,
                    "degree_level": level,
                    "channel_type": entry["type"],
                    "url": entry["url"],
                    "source_url": entry["source_url"],
                    "source_excerpt": entry.get("excerpt"),
                    "note": entry.get("note"),
                }
            )
    return result


def _is_http(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def selftest() -> None:
    all_rows = rows()
    seen: set[tuple[str, str | None]] = set()
    for row in all_rows:
        key = (row["slug"], row["degree_level"])
        assert key not in seen, f"дубль записи {key}"
        seen.add(key)
        assert row["channel_type"] in CHANNEL_TYPES, row
        assert row["degree_level"] is None or row["degree_level"] in LEVELS, row
        assert _is_http(row["url"]) and _is_http(row["source_url"]), row
        assert row["source_excerpt"] is None or len(row["source_excerpt"]) >= 20, row
    unified = [row for row in all_rows if row["channel_type"] == "unified_portal"]
    assert all(row["degree_level"] in ("bachelor", "college") for row in unified), "единая подача — только основные программы"
    assert {row["url"] for row in unified} == {UNIFIED["url"]}
    assert len({row["slug"] for row in unified}) == 8, "в единой подаче 2026 года восемь вузов"
    assert not _is_http("javascript:alert(1)") and not _is_http("www.example.lv")
    print(f"самотест пройден: {len(all_rows)} строк, {len({row['slug'] for row in all_rows})} учреждений")


def review() -> None:
    """Таблица для проверки человеком — в docs/checks/APPLICATION-CHANNELS-REVIEW.md."""
    level_names = {None: "все уровни", "college": "колледж", "bachelor": "бакалавриат", "master": "магистратура", "doctoral": "докторантура"}
    type_names = {"unified_portal": "единая подача", "university": "в сам вуз"}
    print("| Вуз | Уровень | Тип | Куда ведёт ссылка | Источник | Цитата из источника | Заметка |")
    print("|---|---|---|---|---|---|---|")
    for row in rows():
        quote = f"«{row['source_excerpt']}»" if row["source_excerpt"] else "**нет цитаты — проверить глазами**"
        print(
            f"| `{row['slug']}` | {level_names[row['degree_level']]} | {type_names[row['channel_type']]} | "
            f"{row['url']} | {row['source_url']} | {quote} | {row['note'] or ''} |"
        )


def main(apply: bool) -> None:
    from dotenv import load_dotenv

    from db import fetch_all, get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()

    universities = {row["slug"]: row["id"] for row in execute(client.table("university").select("id, slug")).data}
    # Страницами: программ в каталоге больше тысячи (1976 на 2026-10-10), а
    # .limit(2000) не помогал — предел в 1000 строк стоит на сервере. Скрипт
    # видел только часть программ и мог счесть, что у вуза нет программ
    # нужного уровня.
    # Только Латвия: в Литве подача идёт через общий приём LAMA BPO
    # (country.ts, generalAdmission), записей application_channel у неё нет,
    # и её вузы попадали бы в отчёт «без черновика».
    programmes = fetch_all(
        lambda: client.table("programme")
        .select("id, university_id, degree_level, university:university_id!inner(country)")
        .eq("university.country", "LV")
        .order("id")
    )
    offered = {(row["university_id"], row["degree_level"]) for row in programmes}
    existing = {
        (row["university_id"], row["degree_level"]): row
        for row in execute(client.table("application_channel").select("university_id, degree_level, verified_at")).data
    }

    written = skipped_verified = 0
    covered: set[tuple[str, str]] = set()
    for row in rows():
        university_id = universities.get(row["slug"])
        if university_id is None:
            print(f"ПРОПУСК {row['slug']}: такого вуза нет в базе")
            continue
        level = row["degree_level"]
        # какие пары (вуз, уровень) из каталога эта запись закрывает
        levels = [level] if level else [lvl for lvl in LEVELS if (university_id, lvl) in offered]
        if level and (university_id, level) not in offered:
            print(f"ПРОПУСК {row['slug']} [{level}]: у вуза нет программ этого уровня в каталоге")
            continue
        covered.update((university_id, lvl) for lvl in levels)

        prior = existing.get((university_id, level))
        if prior and prior["verified_at"]:
            skipped_verified += 1
            print(f"{row['slug']} [{level or 'все уровни'}]: уже подтверждено — не трогаю")
            continue
        print(f"{row['slug']} [{level or 'все уровни'}]: {row['channel_type']} -> {row['url']}")
        if apply:
            payload = {
                "university_id": university_id,
                "degree_level": level,
                "channel_type": row["channel_type"],
                "url": row["url"],
                "source_url": row["source_url"],
                "source_excerpt": row["source_excerpt"],
            }
            # verified_at/verified_by в записи нет вовсе — их ставит только человек
            execute(client.table("application_channel").upsert(payload, on_conflict="university_id,degree_level"))
            written += 1

    uncovered = sorted(offered - covered)
    by_id = {value: key for key, value in universities.items()}
    print(
        f"\nчерновиков к записи: {len(rows())}; записано: {written}; подтверждённых не тронуто: {skipped_verified}"
        + ("" if apply else " (сухой прогон — запись только с --apply)")
    )
    print(f"пар «вуз, уровень» в каталоге: {len(offered)}; закрыто черновиками: {len(offered & covered)}")
    if uncovered:
        print("без черновика: " + ", ".join(f"{by_id.get(uid, uid)} [{level}]" for uid, level in uncovered))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    elif "--review" in sys.argv:
        review()
    else:
        main("--apply" in sys.argv)
