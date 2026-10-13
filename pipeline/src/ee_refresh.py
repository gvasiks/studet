"""Эстония: обновить данные одной командой — с компьютера владельца.

У эстонских данных пока нет расписания на GitHub: источники — внутренний
интерфейс государственного портала и страницы конкурсов SAIS, и сначала
стоит убедиться, что обновление идёт ровно. Эта команда запускает
загрузчики по порядку и останавливается на первом сбое: следующие шаги
опираются на предыдущие.

  .venv\\Scripts\\python.exe src\\ee_refresh.py
  .venv\\Scripts\\python.exe src\\ee_refresh.py --selftest

Каталог, направления и сроки — меньше минуты каждый. Условия конкурса
читают только новые и открытые конкурсы: обычно минута-две, в сезон приёма
(когда на портале появляются сотни новых конкурсов) — до двадцати минут.
В сезон (март–август) запускать раз в неделю, в остальное время — раз в
месяц.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent

# Название шага и аргументы для Python. Порядок важен: направления и сроки
# привязываются к программам каталога, условия конкурса — к срокам, город
# — к условиям конкурса.
STEPS = [
    ("каталог", ["src/main.py", "ee_haridusportaal"]),
    ("направления программ", ["src/ee_load_fields.py", "--apply"]),
    ("сроки приёма", ["src/ee_load_admissions.py", "--apply"]),
    ("условия конкурса", ["src/ee_load_admission_details.py", "--apply"]),
    # Последним: сбор каталога каждый раз возвращает город из адреса
    # учреждения, а этот шаг ставит город по месту учёбы из SAIS.
    ("город по месту учёбы", ["src/ee_apply_cities.py", "--apply"]),
]


def _selftest() -> None:
    assert [name for name, _ in STEPS] == [
        "каталог",
        "направления программ",
        "сроки приёма",
        "условия конкурса",
        "город по месту учёбы",
    ]
    for _, command in STEPS:
        assert (PIPELINE_DIR / command[0]).is_file(), f"нет файла {command[0]}"
    print("selftest: OK")


def main() -> None:
    args = sys.argv[1:]
    if "--selftest" in args:
        _selftest()
        return
    sys.stdout.reconfigure(encoding="utf-8")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for number, (name, command) in enumerate(STEPS, start=1):
        print(f"\n=== {number} из {len(STEPS)}: {name} ===", flush=True)
        result = subprocess.run([sys.executable, *command], cwd=PIPELINE_DIR, env=env, check=False)
        if result.returncode != 0:
            rest = ", ".join(later for later, _ in STEPS[number:]) or "нет"
            print(
                f"\nОСТАНОВЛЕНО на шаге «{name}» (код {result.returncode}). Причина — в строках выше.\n"
                f"Не выполнены шаги: {rest}. В базе осталось то, что было до запуска этого шага."
            )
            sys.exit(result.returncode)
    print("\nГотово: эстонские данные обновлены.")


if __name__ == "__main__":
    main()
