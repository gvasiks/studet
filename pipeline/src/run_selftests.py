"""Все самопроверки конвейера одним запуском — для CI (.github/workflows/ci.yml).

Самопроверки (--selftest) работают без базы и без сети: проверяют разбор
документов и страниц на сохранённых образцах. Раньше их запускали только
руками, и поломка разборщика становилась видна в ночь сбора. Теперь — при
каждой отправке кода.

Скрипт находит в src/ и src/sources/ все файлы, где есть самопроверка, и
запускает каждый отдельным процессом. Адрес базы и ключ подменяются на
заведомо неверные: самопроверка, которая тайком ходит в базу, упадёт и
здесь, а не только в CI без секретов.

  python src/run_selftests.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
# запускаются без флага: сам файл и есть самопроверка
PLAIN = {"main_selftest.py", "run_report.py"}
SKIP = {"run_selftests.py"}
TIMEOUT_SECONDS = 180


def selftest_files() -> list[Path]:
    files = sorted(SRC.glob("*.py")) + sorted((SRC / "sources").glob("*.py"))
    return [path for path in files if path.name not in SKIP and "selftest" in path.read_text(encoding="utf-8")]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    env = {
        **os.environ,
        "SUPABASE_URL": "http://selftest.invalid",
        "SUPABASE_SERVICE_ROLE_KEY": "selftest-invalid",
        "PYTHONIOENCODING": "utf-8",
        # модули из src/ импортируются по имени (from db import …)
        "PYTHONPATH": str(SRC),
    }
    failed: list[str] = []
    files = selftest_files()
    for path in files:
        command = [sys.executable, str(path)] + ([] if path.name in PLAIN else ["--selftest"])
        try:
            result = subprocess.run(
                command, cwd=SRC.parent, env=env, capture_output=True, text=True, encoding="utf-8", timeout=TIMEOUT_SECONDS
            )
            ok = result.returncode == 0
            output = (result.stdout + result.stderr).strip()
        except subprocess.TimeoutExpired:
            ok, output = False, f"не уложилась в {TIMEOUT_SECONDS} с"
        name = path.relative_to(SRC).as_posix()
        print(f"{'OK  ' if ok else 'FAIL'} {name}")
        if not ok:
            failed.append(name)
            print("     " + output[-1500:].replace("\n", "\n     "))
    print(f"\nсамопроверок: {len(files)}, упало: {len(failed)}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
