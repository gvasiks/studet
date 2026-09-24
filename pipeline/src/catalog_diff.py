"""Дифф каталога между прогонами конвейера (план 2026-09-21, пункт 07).

Апсерт programme (main.py) раньше был слепым: новый прогон переписывал
поля программы (стоимость, бюджетные места, ...) поверх старых значений,
но НЕ трогал verified_at/verified_by — значит, если человек когда-нибудь
подтвердит программу через Studio, а вуз на сайте поменяет цену, бейдж
«Verified DD.MM.YYYY» на карточке молча остался бы висеть поверх уже
неверных данных (badge читает programme.verified_at — см.
src/app/[locale]/(site)/programmes/[university]/[programme]/page.tsx).
Сейчас (2026-09-24) подтверждённых программ 0 — баг ещё никого не подвёл,
чинится до того, как подведёт.

Чистая часть (без обращения к базе — тестируется --selftest): по каждому
слагу сравнивает поля, которые РЕАЛЬНО попадут в апсерт (exclude_none в
main.py убирает из payload отсутствующие у источника поля — их в диффе
тоже нет, апсерт их и не тронет), и решает, сбрасывать ли подтверждение.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Поля программы, которые подтверждает человек (правило 6 CLAUDE.md:
# стоимость и бюджетные места — прямо названы; остальные — тот же уровень
# факта, что показывается тем же бейджем verified_at на карточке).
# НЕ включены: id, university_id, slug (ключ, не факт), verified_at/by
# (сама пометка), created_at/updated_at/extracted_at/source_key/missed_runs
# (служебные, конвейер трогает их каждый прогон намеренно).
CONTENT_FIELDS = (
    "name_lv",
    "name_en",
    "degree_level",
    "language_of_instruction",
    "study_mode",
    "city",
    "funding_type",
    "tuition_fee_amount",
    "tuition_fee_currency",
    "budget_places",
    "duration_years",
    "accreditation_valid_until",
    "description_lv",
    "description_en",
    "source_url",
)


def _values_equal(a: object, b: object) -> bool:
    """Числа сравниваются с допуском на представление (float из pydantic
    против numeric из Postgres) — иначе 1500.0 vs "1500.00" ложно считались
    бы разными значениями и сбрасывали бы настоящее подтверждение зря."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 0.01
    if a is None or b is None:
        return a == b
    try:
        return abs(float(a) - float(b)) < 0.01  # оба похожи на числа, но разных типов ("1500" vs 1500)
    except (TypeError, ValueError):
        return a == b


@dataclass
class ProgrammeChange:
    slug: str
    name: str
    diffs: dict[str, tuple[object, object]] = field(default_factory=dict)  # поле -> (было, стало)
    reset_verification: bool = False


@dataclass
class CatalogDiff:
    added: list[str] = field(default_factory=list)
    changed: list[ProgrammeChange] = field(default_factory=list)
    reset_count: int = 0

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.changed)


def compute_diff(
    existing_by_slug: dict[str, dict],
    programme_rows: list[dict],
) -> CatalogDiff:
    """existing_by_slug — срез из базы ДО апсерта: slug -> {verified_at,
    verified_by, + CONTENT_FIELDS}. programme_rows — то, что main.py вот-вот
    передаст в client.table("programme").upsert(...) (уже с university_id/
    extracted_at/source_key/missed_runs, они здесь не участвуют).

    Мутирует programme_rows на месте: программам, у которых изменилось
    подтверждённое поле, ставит verified_at=None, verified_by=None — так
    апсерт main.py сразу пишет сброс, а не только сообщает о нём."""
    result = CatalogDiff()
    for row in programme_rows:
        slug = row["slug"]
        prior = existing_by_slug.get(slug)
        if prior is None:
            result.added.append(slug)
            continue

        diffs = {
            f: (prior.get(f), row[f])
            for f in CONTENT_FIELDS
            if f in row and not _values_equal(prior.get(f), row[f])
        }
        if not diffs:
            continue

        was_verified = prior.get("verified_at") is not None
        change = ProgrammeChange(
            slug=slug,
            name=row.get("name_en") or row.get("name_lv") or slug,
            diffs=diffs,
            reset_verification=was_verified,
        )
        result.changed.append(change)
        if was_verified:
            row["verified_at"] = None
            row["verified_by"] = None
            result.reset_count += 1
    return result


def format_report(diff: CatalogDiff, university_slug: str) -> str:
    lines = []
    if diff.added:
        lines.append(f"  {university_slug}: добавлено {len(diff.added)} — {', '.join(diff.added[:5])}" + (" …" if len(diff.added) > 5 else ""))
    for change in diff.changed:
        field_notes = "; ".join(f"{f}: {old!r} → {new!r}" for f, (old, new) in change.diffs.items())
        reset_note = " — СНЯТО ПОДТВЕРЖДЕНИЕ" if change.reset_verification else ""
        lines.append(f"  {university_slug}/{change.slug} ({change.name}): {field_notes}{reset_note}")
    return "\n".join(lines)


def selftest() -> None:
    # добавленная программа — просто в список added, не трогаем verified_at
    added_row = {"slug": "new-programme", "name_en": "New", "tuition_fee_amount": 1500.0}
    diff = compute_diff({}, [added_row])
    assert diff.added == ["new-programme"]
    assert not diff.changed
    assert "verified_at" not in added_row

    # изменилось подтверждённое поле — сброс
    existing = {
        "verified-me": {
            "verified_at": "2026-09-20T00:00:00Z",
            "verified_by": "owner",
            "name_en": "X",
            "tuition_fee_amount": 1500.0,
            "budget_places": 20,
        }
    }
    changed_row = {"slug": "verified-me", "name_en": "X", "tuition_fee_amount": 1800.0, "budget_places": 20}
    diff2 = compute_diff(existing, [changed_row])
    assert len(diff2.changed) == 1
    assert diff2.changed[0].reset_verification is True
    assert diff2.reset_count == 1
    assert changed_row["verified_at"] is None
    assert changed_row["verified_by"] is None
    assert diff2.changed[0].diffs == {"tuition_fee_amount": (1500.0, 1800.0)}

    # изменилось поле у НЕподтверждённой программы — учтено в changed, но не в reset_count
    existing3 = {"draft": {"verified_at": None, "verified_by": None, "name_en": "Y", "budget_places": 10}}
    row3 = {"slug": "draft", "name_en": "Y", "budget_places": 15}
    diff3 = compute_diff(existing3, [row3])
    assert len(diff3.changed) == 1
    assert diff3.changed[0].reset_verification is False
    assert diff3.reset_count == 0
    assert "verified_at" not in row3  # не трогаем то, что не сбрасывали

    # числовое представление разное, значение то же — не диф (1500.0 vs "1500.00")
    existing4 = {"same": {"verified_at": "2026-09-20T00:00:00Z", "name_en": "Z", "tuition_fee_amount": "1500.00"}}
    row4 = {"slug": "same", "name_en": "Z", "tuition_fee_amount": 1500.0}
    diff4 = compute_diff(existing4, [row4])
    assert not diff4.changed
    assert "verified_at" not in row4

    # поле отсутствует у источника в этом прогоне (exclude_none выкинул) —
    # апсерт его не тронет, поэтому и в дифф оно не попадает, даже если в
    # базе значение отличается от того, что БЫЛО у источника раньше
    existing5 = {"partial": {"verified_at": "2026-09-20T00:00:00Z", "name_en": "P", "description_en": "old text"}}
    row5 = {"slug": "partial", "name_en": "P"}  # description_en отсутствует
    diff5 = compute_diff(existing5, [row5])
    assert not diff5.changed

    print("самотест пройден")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        print("Библиотечный модуль — сборки не имеет, кроме --selftest.")
