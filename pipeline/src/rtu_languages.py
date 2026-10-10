"""Язык обучения на латышской карточке программы РТУ.

Поле «Īstenošanas valoda» бывает трёх видов (подсчёт 2026-10-10 по 150
карточкам): «Latviešu» — 63, «Latviešu, Angļu» — 78, «Angļu» — 9.

Правило: если в поле есть латышский, запись латышская; только английский —
английская; ничего знакомого — язык пустой (main.py оставит у программы
прежний, а новую программу без языка не запишет).

Как к нему пришли — чтобы не повторять:

1. До 2026-10-10 двуязычная карточка писалась английской. В фильтре
   «латышский» не было больше половины программ РТУ.
2. 2026-10-10 утром двуязычная карточка стала двумя записями — латышской и
   английской («…-en»). Оказалось, что пометка «Angļu» на латышской
   карточке не значит, что на программу набирают на английском: таких
   записей получилось 83, а в английском реестре РТУ, по которому
   поступают, программ 55 (бакалавриата по химии, например, там нет).
3. В тот же день владелец решил: английские программы — из английского
   реестра (sources/rtu_english.py), латышский реестр даёт латышские записи.

Девять программ латышский реестр помечает как только-английские — они
пишутся отсюда, как и раньше, со старыми слагами (на двух подтверждённые
формулы).

Модуль без обращения к сайту и базе:

  python src/rtu_languages.py --selftest
"""

from __future__ import annotations

import sys


def extract_languages(text: str) -> list[str]:
    """Языки из поля «Īstenošanas valoda»: ['lv'], ['en'] или ['lv', 'en'].

    Пустой список — поля нет или в нём незнакомое значение.
    """
    lowered = text.lower()
    return [code for code, word in (("lv", "latvie"), ("en", "angļu")) if word in lowered]


def card_language(languages: list[str]) -> str | None:
    """Язык записи каталога для латышской карточки (правило — в шапке модуля)."""
    if "lv" in languages:
        return "lv"
    return languages[0] if languages else None


def selftest() -> None:
    assert extract_languages("Latviešu") == ["lv"]
    assert extract_languages("Angļu") == ["en"]
    assert extract_languages("Latviešu, Angļu") == ["lv", "en"]
    assert extract_languages("Angļu, Latviešu") == ["lv", "en"], "порядок на сайте не важен"
    assert extract_languages("") == [] and extract_languages("Vācu") == []

    assert card_language(["lv"]) == "lv"
    assert card_language(["lv", "en"]) == "lv", "двуязычная карточка — латышская запись"
    assert card_language(["en"]) == "en"
    assert card_language([]) is None, "непрочитанный язык не подставляется"
    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        print("Библиотечный модуль — запускается только с --selftest.")
