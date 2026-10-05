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

import re

from dataclasses import dataclass, field

# Поля программы, которые подтверждает человек (правило 6 CLAUDE.md:
# стоимость и бюджетные места — прямо названы; остальные — тот же уровень
# факта, что показывается тем же бейджем verified_at на карточке).
# НЕ включены: id, university_id, slug (ключ, не факт), verified_at/by
# (сама пометка), created_at/updated_at/extracted_at/source_key/missed_runs
# (служебные, конвейер трогает их каждый прогон намеренно).
CONTENT_FIELDS = (
    "name_lv",
    "name_lt",
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
    "description_lt",
    "description_en",
    "degree_awarded_lt",
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
            name=row.get("name_en") or row.get("name_lv") or row.get("name_lt") or slug,
            diffs=diffs,
            reset_verification=was_verified,
        )
        result.changed.append(change)
        if was_verified:
            row["verified_at"] = None
            row["verified_by"] = None
            result.reset_count += 1
    return result


def fill_missing_keys(programme_rows: list[dict], existing_by_slug: dict[str, dict]) -> int:
    """Привести строки одной пачки к одному набору ключей. Возвращает, сколько значений дописано.

    Зачем. Все программы вуза уходят в базу одним upsert. Клиент supabase-py
    передаёт PostgREST список колонок — объединение ключей ВСЕХ строк пачки, —
    и ключ, которого в какой-то строке нет, записывается как NULL, затирая
    то, что было в базе. Ключи же у строк разные: main.py убирает из строки
    поля, которых сборщик не нашёл (exclude_none), а compute_diff добавляет
    verified_at/verified_by только тем, у кого снимает подтверждение.
    Последствия до исправления (2026-10-04):
      - сборщик нашёл срок аккредитации у 12 программ Turība из 17 — у
        остальных пяти значение, дописанное другим скриптом или руками в
        Studio, стиралось каждым сбором (воспроизведено на живой базе);
      - снятие подтверждения с одной программы сняло бы его со всех
        подтверждённых программ вуза в той же пачке.

    Недостающий ключ дописывается тем значением, что уже лежит в базе, —
    то есть строка его «не трогает», как и обещает README. У новой программы
    (в базе её нет) недостающее поле остаётся пустым, как и раньше.

    existing_by_slug должен содержать все колонки, которые могут оказаться
    недостающими (main.py запрашивает verified_at, verified_by и
    CONTENT_FIELDS). Если нужной колонки в нём нет — исключение: лучше
    сорвать запись вуза, чем молча обнулить поле.
    """
    all_keys: set[str] = set()
    for row in programme_rows:
        all_keys.update(row)

    filled = 0
    for row in programme_rows:
        prior = existing_by_slug.get(row["slug"])
        for key in sorted(all_keys - row.keys()):
            if prior is not None and key not in prior:
                raise KeyError(
                    f"{row['slug']}: поля «{key}» нет в строке и нет среди прочитанных из базы — "
                    "добавьте колонку в select перед upsert (main.py), иначе она обнулится"
                )
            row[key] = prior.get(key) if prior is not None else None
            filled += 1
    return filled


def format_report(diff: CatalogDiff, university_slug: str) -> str:
    lines = []
    if diff.added:
        lines.append(f"  {university_slug}: добавлено {len(diff.added)} — {', '.join(diff.added[:5])}" + (" …" if len(diff.added) > 5 else ""))
    for change in diff.changed:
        field_notes = "; ".join(f"{f}: {old!r} → {new!r}" for f, (old, new) in change.diffs.items())
        reset_note = " — СНЯТО ПОДТВЕРЖДЕНИЕ" if change.reset_verification else ""
        lines.append(f"  {university_slug}/{change.slug} ({change.name}): {field_notes}{reset_note}")
    return "\n".join(lines)


# Название программы, которое на самом деле адрес сайта: «www.rtu.lv»,
# «https://…», «rtu.lv». Так выглядит заголовок страницы-заглушки, которую
# сайт отдаёт вместо карточки программы (случай rtu_liepaja, 2026-10-03).
_WEB_ADDRESS = re.compile(r"^(?:https?://|www\.)\S*$|^[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}$", re.IGNORECASE)


def suspicious_names(programme_rows: list[dict]) -> list[str]:
    """Слаги программ, у которых название похоже на адрес сайта или пусто.

    Чистая функция; main.py отказывается записывать источник, если список
    не пуст: лучше оставить прошлонедельные данные, чем заменить название
    программы мусором.
    """
    bad: list[str] = []
    for row in programme_rows:
        names = [row.get("name_lv"), row.get("name_lt"), row.get("name_en")]
        present = [name.strip() for name in names if isinstance(name, str) and name.strip()]
        if not present or any(_WEB_ADDRESS.match(name) for name in present):
            bad.append(row.get("slug", "?"))
    return bad


def selftest() -> None:
    assert suspicious_names([{"slug": "hbe", "name_lv": "www.rtu.lv"}]) == ["hbe"]
    assert suspicious_names([{"slug": "a", "name_en": "https://example.com/x"}]) == ["a"]
    assert suspicious_names([{"slug": "b", "name_lv": "rtu.lv"}]) == ["b"]
    assert suspicious_names([{"slug": "c", "name_lv": "  "}]) == ["c"], "пустое название — тоже мусор"
    assert suspicious_names([{"slug": "d"}]) == ["d"]
    assert suspicious_names([{"slug": "e", "name_lt": "Teisė"}]) == [], "литовское название — тоже название"
    assert suspicious_names([{"slug": "f", "name_lt": "www.vu.lt"}]) == ["f"]
    assert suspicious_names(
        [
            {"slug": "ok1", "name_lv": "Logopēdija"},
            {"slug": "ok2", "name_en": "B.Sc. in Economics"},
            {"slug": "ok3", "name_en": "Ph.D"},
            {"slug": "ok4", "name_lv": "E-biznesa vadība", "name_en": "E-business Management"},
            {"slug": "ok5", "name_en": "Industry 4.0"},
        ]
    ) == [], "обычные названия с точками и дефисами не трогаем"

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

    # --- fill_missing_keys: пачка с разными ключами не обнуляет чужие поля ---
    in_db = {
        "a": {"slug": "a", "accreditation_valid_until": "2027-08-05", "tuition_fee_amount": 1500, "verified_at": "2026-09-01", "verified_by": "owner"},
        "b": {"slug": "b", "accreditation_valid_until": "2027-08-05", "tuition_fee_amount": None, "verified_at": "2026-09-02", "verified_by": "owner"},
    }
    # сборщик нашёл срок аккредитации только у «a»; «b» дописана другим скриптом
    rows = [
        {"slug": "a", "accreditation_valid_until": "2027-08-05", "missed_runs": 0},
        {"slug": "b", "missed_runs": 0},
        {"slug": "new", "missed_runs": 0},
    ]
    assert fill_missing_keys(rows, in_db) == 2
    assert rows[1]["accreditation_valid_until"] == "2027-08-05", "значение из базы сохранено, а не обнулено"
    assert rows[2]["accreditation_valid_until"] is None, "у новой программы поле пустое"
    assert {frozenset(row) for row in rows} == {frozenset({"slug", "accreditation_valid_until", "missed_runs"})}

    # снятие подтверждения с одной программы не трогает подтверждение соседней
    rows = [
        {"slug": "a", "tuition_fee_amount": 1800.0},
        {"slug": "b", "tuition_fee_amount": None},
    ]
    del rows[1]["tuition_fee_amount"]  # у «b» сборщик цену не нашёл — ключа нет
    diff6 = compute_diff(in_db, rows)
    assert diff6.reset_count == 1 and rows[0]["verified_at"] is None
    fill_missing_keys(rows, in_db)
    assert rows[1]["verified_at"] == "2026-09-02" and rows[1]["verified_by"] == "owner", "подтверждение «b» на месте"
    assert rows[0]["verified_at"] is None and rows[0]["verified_by"] is None, "у «a» снято"
    assert rows[1]["tuition_fee_amount"] is None, "в базе у «b» цены нет — её и не появилось"

    # одинаковые ключи — дописывать нечего
    rows = [{"slug": "a", "missed_runs": 0}, {"slug": "b", "missed_runs": 0}]
    assert fill_missing_keys(rows, in_db) == 0

    # колонка не была прочитана из базы — отказ, а не тихое обнуление
    rows = [{"slug": "a", "budget_places": 10}, {"slug": "b"}]
    try:
        fill_missing_keys(rows, in_db)
    except KeyError:
        pass
    else:
        raise AssertionError("поле, которого нет в прочитанной строке, нельзя молча обнулить")

    print("самотест пройден")


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        print("Библиотечный модуль — сборки не имеет, кроме --selftest.")
