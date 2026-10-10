"""Язык обучения программ РТУ: одна запись каталога на каждый язык.

На карточке программы РТУ поле «Īstenošanas valoda» бывает трёх видов
(подсчёт 2026-10-10 по 150 карточкам): «Latviešu» — 63, «Latviešu, Angļu» —
78, «Angļu» — 9. До этой даты сборщик писал двуязычную программу как
английскую, и в фильтре «латышский» половины программ РТУ не было.

Решение владельца (2026-10-10): двуязычная программа — две записи каталога,
как у BSA, TSI, RISEBA и RAI.

- Латышская запись сохраняет прежний адрес (слаг) и все данные: к ней уже
  привязаны формулы, разметка направления и списки избранного.
- Английская получает слаг с окончанием «-en». Цена, бюджетные места и вид
  финансирования у неё пустые: реестр РТУ даёт одну цену и одну квоту на
  программу, не уточняя поток. Приписать их английскому потоку — значит
  выдать догадку за факт (правило 5 CLAUDE.md).

Модуль без обращения к сайту и базе:

  python src/rtu_languages.py --selftest
"""

from __future__ import annotations

import sys

from models import ProgrammeDraft


def extract_languages(text: str) -> list[str]:
    """Языки из поля «Īstenošanas valoda»: ['lv'], ['en'] или ['lv', 'en'].

    Пустой список — поля нет или в нём незнакомое значение. «Латышский» по
    умолчанию не подставляем: main.py оставит у программы прежний язык, а
    новую программу без языка не запишет.
    """
    lowered = text.lower()
    return [code for code, word in (("lv", "latvie"), ("en", "angļu")) if word in lowered]


def language_variants(draft: ProgrammeDraft, languages: list[str]) -> list[ProgrammeDraft]:
    """Записи каталога для одной программы: по одной на каждый язык.

    draft — программа со всеми данными реестра, язык в ней не важен.
    """
    if len(languages) < 2:
        return [draft.model_copy(update={"language_of_instruction": languages[0] if languages else None})]
    english = draft.model_copy(
        update={
            "slug": f"{draft.slug}-en",
            "language_of_instruction": "en",
            "funding_type": None,
            "tuition_fee_amount": None,
            "budget_places": None,
        }
    )
    return [draft.model_copy(update={"language_of_instruction": "lv"}), english]


def selftest() -> None:
    assert extract_languages("Latviešu") == ["lv"]
    assert extract_languages("Angļu") == ["en"]
    assert extract_languages("Latviešu, Angļu") == ["lv", "en"]
    assert extract_languages("Angļu, Latviešu") == ["lv", "en"], "порядок на сайте не важен: латышская запись первая"
    assert extract_languages("") == [] and extract_languages("Vācu") == []

    draft = ProgrammeDraft(
        slug="kbm-32000",
        name_lv="Ķīmija un ķīmijas tehnoloģija",
        degree_level="bachelor",
        study_mode="full_time",
        city="riga",
        funding_type="both",
        tuition_fee_amount=3340.0,
        budget_places=60,
        duration_years=4.0,
        source_url="https://www.rtu.lv/lv/studijas/visas-studiju-programmas/atvert/KBM?department=32000&type=P",
    )

    latvian, english = language_variants(draft, ["lv", "en"])
    assert (latvian.slug, latvian.language_of_instruction) == ("kbm-32000", "lv")
    assert (latvian.funding_type, latvian.tuition_fee_amount, latvian.budget_places) == ("both", 3340.0, 60)
    assert (english.slug, english.language_of_instruction) == ("kbm-32000-en", "en")
    assert (english.funding_type, english.tuition_fee_amount, english.budget_places) == (None, None, None)
    assert (english.name_lv, english.duration_years, english.city, english.source_url) == (
        draft.name_lv, 4.0, "riga", draft.source_url,
    )

    # один язык — одна запись с прежним слагом и всеми данными
    for languages in (["lv"], ["en"]):
        (only,) = language_variants(draft, languages)
        assert (only.slug, only.language_of_instruction, only.tuition_fee_amount) == ("kbm-32000", languages[0], 3340.0)

    # язык не прочитан — одна запись без языка
    (unknown,) = language_variants(draft, [])
    assert unknown.slug == "kbm-32000" and unknown.language_of_instruction is None
    assert draft.language_of_instruction is None, "исходный черновик не меняется"
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        print("Библиотечный модуль — запускается только с --selftest.")
