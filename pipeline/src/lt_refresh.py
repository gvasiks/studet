"""Литва: обновить данные одной командой — с компьютера владельца.

Зачем отдельный скрипт. Литовский реестр программ (aikos.smm.lt) серверу
GitHub отвечает ненадёжно: из пяти прогонов 9–10 октября 2026 года два
прошли, один упал на не ответившей странице, один — на тридцати неполных
карточках, один не уложился в два с половиной часа. С компьютера в Риге тот
же обход проходит без единого сбоя. Расписание на GitHub владелец оставил
(.github/workflows/scrape-lithuania.yml), так что эта команда — запасной и
надёжный путь: когда прогон на GitHub упал, а данные нужны сейчас, или
когда сторож (lithuania-health.yml) написал, что они устарели.

Скрипт запускает загрузчики по порядку и останавливается на первом сбое:
следующие шаги опираются на предыдущие.

  .venv\\Scripts\\python.exe src\\lt_refresh.py            # каталог, формулы, направления (около 25 минут)
  .venv\\Scripts\\python.exe src\\lt_refresh.py --yearly   # то же плюс цифры прошлого приёма и показатели выпускников
  .venv\\Scripts\\python.exe src\\lt_refresh.py --selftest
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent

# Название шага и аргументы для Python. Порядок важен: строки приёма
# привязываются к программам каталога, направления — к строкам приёма.
REGULAR = [
    ("каталог", ["src/main.py", "lt_lamabpo"]),
    ("строки приёма и формулы", ["src/lt_load_formulas.py", "--apply"]),
    ("направления программ", ["src/lt_load_fields.py", "--apply"]),
]
# Источники этих двух обновляются раз в год (pipeline/README.md, «Литва:
# что обновлять в течение года»), поэтому в обычный запуск они не входят.
YEARLY = [
    ("цифры прошлого приёма", ["src/lt_load_admission_stats.py", "--apply"]),
    ("показатели выпускников", ["src/lt_load_field_outcomes.py", "--apply"]),
]


def plan(args: list[str]) -> list[tuple[str, list[str]]]:
    """Какие шаги выполнять при этих аргументах."""
    return REGULAR + (YEARLY if "--yearly" in args else [])


def _selftest() -> None:
    assert [name for name, _ in plan([])] == ["каталог", "строки приёма и формулы", "направления программ"]
    assert [name for name, _ in plan(["--yearly"])][3:] == ["цифры прошлого приёма", "показатели выпускников"]
    for _, command in REGULAR + YEARLY:
        assert (PIPELINE_DIR / command[0]).is_file(), f"нет файла {command[0]}"
    print("selftest: OK")


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")
    # Каталог и формулы читают одни и те же карточки реестра: с кэшем второй
    # шаг берёт их с диска, а не обходит реестр второй раз.
    env = {**os.environ, "SCRAPE_CACHE": "1", "PYTHONIOENCODING": "utf-8"}
    steps = plan(args)
    for number, (name, command) in enumerate(steps, start=1):
        print(f"\n=== {number} из {len(steps)}: {name} ===", flush=True)
        result = subprocess.run([sys.executable, *command], cwd=PIPELINE_DIR, env=env, check=False)
        if result.returncode != 0:
            rest = ", ".join(later for later, _ in steps[number:]) or "нет"
            print(
                f"\nОСТАНОВЛЕНО на шаге «{name}» (код {result.returncode}). Причина — в строках выше.\n"
                f"Не выполнены шаги: {rest}. В базе осталось то, что было до запуска этого шага."
            )
            sys.exit(result.returncode)
    print("\nГотово: литовские данные обновлены.")


if __name__ == "__main__":
    main()
