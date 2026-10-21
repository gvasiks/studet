"""Итог сбора каталога для владельца (план 2026-09-21, пункт 07: «после
каждого сбора — добавлено, скрыто, изменено по полям с прежним и новым
значением»).

main.py и раньше печатал изменения, но строками в общем журнале прогона —
длинном и раскрываемом по шагам, где их никто не читает, и без скрытых
программ. Здесь из тех же данных собирается один Markdown-отчёт. В GitHub
Actions он дописывается в файл $GITHUB_STEP_SUMMARY и показывается прямо на
странице запуска; при запуске на компьютере — печатается в конце.

Чистая логика (без базы) — проверяется --selftest.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from catalog_diff import CatalogDiff

# Сколько строк показывать в одном списке: отчёт читают глазами, а первый
# прогон нового вуза добавляет сотни программ.
MAX_ROWS = 30
MAX_VALUE = 80


@dataclass
class SourceReport:
    key: str
    university: str
    diff: CatalogDiff
    # строки программ, которых нет на сайте: slug, name_lv, name_en, missed_runs
    # (уже после увеличения счётчика в этом прогоне)
    missing: list[dict] = field(default_factory=list)

    @property
    def has_news(self) -> bool:
        return self.diff.has_changes or bool(self.missing)


def _cell(value: object) -> str:
    """Значение для ячейки таблицы Markdown: одна строка, без «|», не длиннее
    MAX_VALUE (описания программ — абзацы)."""
    text = "—" if value is None or value == "" else str(value)
    text = " ".join(text.split()).replace("|", "/")
    return text if len(text) <= MAX_VALUE else text[: MAX_VALUE - 1] + "…"


def _name(row: dict) -> str:
    return row.get("name_lv") or row.get("name_en") or row["slug"]


def _limited(items: list[str]) -> list[str]:
    if len(items) <= MAX_ROWS:
        return items
    return items[:MAX_ROWS] + [f"… и ещё {len(items) - MAX_ROWS}"]


def markdown_report(reports: list[SourceReport], errors: list[str], hide_after: int) -> str:
    with_news = [report for report in reports if report.has_news]
    lines = [
        "## Сбор каталога — итог",
        "",
        f"Источников записано: {len(reports)}; с изменениями: {len(with_news)}; сбоев: {len(errors)}.",
    ]
    for report in with_news:
        diff = report.diff
        lines += ["", f"### {report.key}"]
        if diff.added:
            lines += ["", f"**Добавлено ({len(diff.added)}):** " + ", ".join(_limited(diff.added))]
        if diff.changed:
            lines += ["", f"**Изменено ({len(diff.changed)}):**", "", "| Программа | Поле | Было | Стало |", "|---|---|---|---|"]
            rows = []
            for change in diff.changed:
                mark = " — **подтверждение снято**" if change.reset_verification else ""
                for name, (old, new) in change.diffs.items():
                    rows.append(f"| {_cell(change.name)} ({change.slug}){mark} | {name} | {_cell(old)} | {_cell(new)} |")
            lines += _limited(rows)
        first_time = [row for row in report.missing if row["missed_runs"] < hide_after]
        hidden_now = [row for row in report.missing if row["missed_runs"] == hide_after]
        still_hidden = [row for row in report.missing if row["missed_runs"] > hide_after]
        if first_time:
            lines += [
                "",
                f"**Не найдено на сайте ({len(first_time)})** — скроется, если не найдётся и в следующем прогоне: "
                + ", ".join(_limited([f"{_name(row)} ({row['slug']})" for row in first_time])),
            ]
        if hidden_now:
            lines += [
                "",
                f"**Скрыто от публики в этом прогоне ({len(hidden_now)})** — не найдено {hide_after} раза подряд: "
                + ", ".join(_limited([f"{_name(row)} ({row['slug']})" for row in hidden_now])),
            ]
        if still_hidden:
            lines += ["", f"Скрыто раньше и по-прежнему нет на сайте: {len(still_hidden)}."]
    if errors:
        lines += ["", "### Сбои", ""] + [f"- {_cell(error)}" for error in errors]
    if not with_news and not errors:
        lines += ["", "Изменений нет."]
    return "\n".join(lines) + "\n"


def publish(text: str) -> None:
    """В GitHub Actions — на страницу запуска; всегда — в журнал."""
    print("\n" + text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as summary:
            summary.write(text)


def selftest() -> None:
    from catalog_diff import ProgrammeChange

    diff = CatalogDiff(
        added=["new-programme"],
        changed=[
            ProgrammeChange(
                slug="economics",
                name="Economics",
                diffs={"tuition_fee_amount": (2800, 3100), "description_en": ("a | b\nc", "x" * 200)},
                reset_verification=True,
            )
        ],
    )
    missing = [
        {"slug": "gone-once", "name_lv": "Vienreiz", "name_en": None, "missed_runs": 1},
        {"slug": "gone-twice", "name_lv": None, "name_en": "Twice", "missed_runs": 2},
        {"slug": "gone-long", "name_lv": "Sen", "name_en": None, "missed_runs": 5},
    ]
    quiet = SourceReport("sources.rsu", "rsu", CatalogDiff())
    text = markdown_report([SourceReport("sources.lu", "lu", diff, missing), quiet], ["sources.du: timeout"], 2)
    assert "Источников записано: 2; с изменениями: 1; сбоев: 1." in text
    assert "### sources.lu" in text and "### sources.rsu" not in text, "источник без изменений не попадает в отчёт"
    assert "**Добавлено (1):** new-programme" in text
    assert "| Economics (economics) — **подтверждение снято** | tuition_fee_amount | 2800 | 3100 |" in text
    assert "| description_en | a / b c |" in text, "перевод строки и «|» не ломают таблицу"
    assert ("x" * (MAX_VALUE - 1) + "…") in text and ("x" * MAX_VALUE) not in text
    assert "**Не найдено на сайте (1)**" in text and "Vienreiz (gone-once)" in text
    assert "**Скрыто от публики в этом прогоне (1)**" in text and "Twice (gone-twice)" in text
    assert "Скрыто раньше и по-прежнему нет на сайте: 1." in text
    assert "- sources.du: timeout" in text
    assert "Изменений нет." in markdown_report([quiet], [], 2)
    many = markdown_report([SourceReport("s", "s", CatalogDiff(added=[f"p{i}" for i in range(40)]))], [], 2)
    assert "… и ещё 10" in many
    print("самотест пройден")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    selftest()
