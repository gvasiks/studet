"""Восстановление подтверждённых фактов из docs/backups/verified-facts.json
(план 2026-09-21, пункт 06 — продолжение backup_verified.py). Читает тот же
снимок, что кладёт backup_verified.py, и накатывает его поверх базы:
university/programme ищутся заново по устойчивым слагам, а не по UUID —
он не переживает пересоздание базы или повторный прогон конвейера.

Restore пишет verified_at/verified_by ИЗ СНИМКА — это не новое решение
(правило 6 CLAUDE.md запрещает автоприём), а восстановление уже принятого
человеком факта после потери данных: тот же verified_at, тот же
verified_by, что человек проставил в первый раз через Supabase Studio,
ничего не придумывается и не подтверждается заново.

Критерий пункта 06 — "снимок восстанавливает подтверждения на пустой
базе" раз в квартал. Полноценная проверка этого требует отдельного
одноразового Supabase-проекта (или локального `supabase start`, для
которого нужен Docker) — в этом окружении нет ни того, ни другого
(проверено: `supabase`/`docker` не установлены), поэтому сама проверка
"восстановить в пустую" — дело владельца, не автоматизируется отсюда.

Что можно и нужно проверять без пустого проекта, и что делает этот
скрипт по умолчанию (без --apply): сухой прогон по ЖИВОЙ базе — находит
programme_id/university_id по слагам из снимка и сообщает, что не
нашлось. Это ловит реальный риск — слаг из снимка мог исчезнуть или
поменяться при повторном сборе каталога, и тогда восстановление
"находит программу, а её больше нет" молча бы промолчало. --apply
делает реальную запись (upsert по тем же ключам, что и seed-скрипты) —
на непустой базе это безопасный no-op, если ничего не терялось (те же
значения перезаписываются теми же), но НЕ заменяет квартальную проверку
на пустом проекте.

Второй риск, найденный ревью 2026-09-24: слаг мог не пропасть, а
ПЕРЕСЛАГОВАТЬСЯ — при повторном сборе каталога та же пара (вуз, слаг)
из снимка вполне может теперь указывать на ДРУГУЮ программу (слаги
генерируются из названия). Без проверки это выглядело бы как "нашёл
программу" и молча приписало бы восстановленную формулу не той записи.
Снимок (backup_verified.py) теперь хранит name_lv на момент
подтверждения; `_resolve_programme` сравнивает его с текущим именем той
же пары (вуз, слаг) и не восстанавливает при расхождении — ни в сухом
прогоне, ни с --apply — а отдельно сообщает об этом как о вероятном
переслаговании. Снимки без name_lv (сделанные до этой проверки)
сравнивать не с чем — восстанавливаются как раньше.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from db import PAGE_ROWS, fetch_all, get_service_client

REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = REPO_ROOT / "docs" / "backups" / "verified-facts.json"


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _university_ids(client) -> dict[str, str]:  # type: ignore[no-untyped-def]
    rows = client.table("university").select("id, slug").execute().data
    return {row["slug"]: row["id"] for row in rows}


def _programme_lookup(client, university_ids: dict[str, str]) -> dict[tuple[str, str], dict]:  # type: ignore[no-untyped-def]
    slug_by_uid = {v: k for k, v in university_ids.items()}
    # Страницами: программ в каталоге больше тысячи (с Литвой — 1919), а
    # одним запросом база отдаёт только первую тысячу. Без этого часть
    # подтверждённых фактов числилась «программы нет в каталоге», хотя
    # программа на месте (замечено 2026-10-10 на четырёх формулах).
    rows = fetch_all(lambda: client.table("programme").select("id, slug, name_lv, university_id").order("id"))
    out: dict[tuple[str, str], dict] = {}
    for row in rows:
        uni_slug = slug_by_uid.get(row["university_id"])
        if uni_slug:
            out[(uni_slug, row["slug"])] = {"id": row["id"], "name_lv": row.get("name_lv")}
    return out


def _resolve_programme(
    lookup: dict[tuple[str, str], dict], key: tuple[str, str], snapshot_name: str | None
) -> tuple[str | None, str | None]:
    """(programme_id, collision_note) — второе не None, если слаг нашёлся, но
    похоже указывает уже на ДРУГУЮ программу (каталог мог переслаговать
    записи при повторном сборе между снимком и восстановлением). Сравниваем
    имя на момент подтверждения (снимок) с текущим именем той же пары
    (вуз, слаг); снимков без programme_name (сделанных до этой проверки) не
    касается — сравнивать не с чем, восстанавливаем как раньше."""
    found = lookup.get(key)
    if found is None:
        return None, None
    current_name = found.get("name_lv")
    if snapshot_name and current_name and snapshot_name != current_name:
        return None, (
            f"{key[0]}/{key[1]}: в снимке подтверждена «{snapshot_name}», сейчас по этому "
            f"слагу «{current_name}» — похоже на переслагование каталога, не восстанавливаю "
            "автоматически, сверьте вручную"
        )
    return found["id"], None


def restore_formulas(
    client, rows: list[dict], programme_lookup: dict[tuple[str, str], dict], apply: bool  # type: ignore[no-untyped-def]
) -> tuple[int, list[str], list[str]]:
    restored = 0
    missing = []
    collisions = []
    for row in rows:
        key = (row["university_slug"], row["programme_slug"])
        programme_id, collision = _resolve_programme(programme_lookup, key, row.get("programme_name"))
        if collision:
            collisions.append(f"formula {collision}")
            continue
        if programme_id is None:
            missing.append(f"formula {key[0]}/{key[1]} ({row['variant']}): программы нет в текущем каталоге")
            continue
        restored += 1
        if not apply:
            continue
        payload = {
            "programme_id": programme_id,
            "variant": row["variant"],
            "valid_from": row["valid_from"],
            "valid_to": row["valid_to"],
            "source_url": row["source_url"],
            "source_doc": row["source_doc"],
            "source_doc_number": row["source_doc_number"],
            "source_doc_date": row["source_doc_date"],
            "source_copy_path": row["source_copy_path"],
            "source_copy_sha256": row["source_copy_sha256"],
            "source_excerpt": row["source_excerpt"],
            "verified_at": row["verified_at"],
            "verified_by": row["verified_by"],
        }
        # Снимки до 2026-10-10 этой даты не хранили: ключа нет — не пишем
        # вовсе, чтобы на живой базе не стереть уже стоящее значение.
        if "source_copy_fetched_on" in row:
            payload["source_copy_fetched_on"] = row["source_copy_fetched_on"]
        formula_id = (
            client.table("formula").upsert(payload, on_conflict="programme_id,variant,valid_from").execute().data[0]["id"]
        )
        client.table("formula_term").delete().eq("formula_id", formula_id).execute()
        if row["terms"]:
            client.table("formula_term").insert(
                [{**t, "formula_id": formula_id} for t in row["terms"]]
            ).execute()
        client.table("formula_gate").delete().eq("formula_id", formula_id).execute()
        if row["gates"]:
            client.table("formula_gate").insert(
                [{**g, "formula_id": formula_id} for g in row["gates"]]
            ).execute()
    return restored, missing, collisions


def restore_application_rounds(
    client, rows: list[dict], university_ids: dict[str, str], apply: bool  # type: ignore[no-untyped-def]
) -> tuple[int, list[str]]:
    restored = 0
    missing = []
    for row in rows:
        university_id = university_ids.get(row["university_slug"])
        if university_id is None:
            missing.append(f"application_round {row['university_slug']}/{row['label']}: вуза нет в каталоге")
            continue
        restored += 1
        if not apply:
            continue
        payload = {"university_id": university_id, **{k: v for k, v in row.items() if k != "university_slug"}}
        client.table("application_round").upsert(payload, on_conflict="university_id,label").execute()
    return restored, missing


def restore_admission_types(
    client, rows: list[dict], university_ids: dict[str, str], apply: bool  # type: ignore[no-untyped-def]
) -> tuple[int, list[str]]:
    restored = 0
    missing = []
    for row in rows:
        university_id = university_ids.get(row["university_slug"])
        if university_id is None:
            missing.append(f"admission_type {row['university_slug']}: вуза нет в каталоге")
            continue
        restored += 1
        if not apply:
            continue
        payload = {"university_id": university_id, **{k: v for k, v in row.items() if k != "university_slug"}}
        client.table("university_admission_type").upsert(payload, on_conflict="university_id").execute()
    return restored, missing


def restore_programme_fields(
    client, rows: list[dict], programme_lookup: dict[tuple[str, str], dict], apply: bool  # type: ignore[no-untyped-def]
) -> tuple[int, list[str], list[str], int]:
    """Последнее число — сколько записей нельзя восстановить, потому что в
    снимке нет способа подтверждения (verification_method). База без него
    подтверждённую запись не принимает, а придумывать его нельзя: «по
    правилу» и «вручную» — разные решения человека. Такие записи
    пропускаются и в сухом прогоне, и с --apply."""
    restored = 0
    missing = []
    collisions = []
    without_method = 0
    for row in rows:
        if not row.get("verification_method"):
            without_method += 1
            continue
        key = (row["university_slug"], row["programme_slug"])
        programme_id, collision = _resolve_programme(programme_lookup, key, row.get("programme_name"))
        if collision:
            collisions.append(f"programme_field {collision}")
            continue
        if programme_id is None:
            missing.append(f"programme_field {key[0]}/{key[1]}: программы нет в текущем каталоге")
            continue
        restored += 1
        if not apply:
            continue
        payload = {
            "programme_id": programme_id,
            "field_code": row["field_code"],
            "source": row["source"],
            "verified_at": row["verified_at"],
            "verified_by": row["verified_by"],
            "verification_method": row["verification_method"],
        }
        client.table("programme_field").upsert(payload, on_conflict="programme_id").execute()
    return restored, missing, collisions, without_method


def restore_requirement_sets(
    client, rows: list[dict], programme_lookup: dict[tuple[str, str], dict], apply: bool  # type: ignore[no-untyped-def]
) -> tuple[int, list[str], list[str]]:
    restored = 0
    missing = []
    collisions = []
    for row in rows:
        key = (row["university_slug"], row["programme_slug"])
        programme_id, collision = _resolve_programme(programme_lookup, key, row.get("programme_name"))
        if collision:
            collisions.append(f"requirement_set {collision}")
            continue
        if programme_id is None:
            missing.append(f"requirement_set {key[0]}/{key[1]}: программы нет в текущем каталоге")
            continue
        restored += 1
        if not apply:
            continue
        skip = {"university_slug", "programme_slug", "programme_name", "requirements"}
        payload = {"programme_id": programme_id, **{k: v for k, v in row.items() if k not in skip}}
        set_id = client.table("programme_requirement_set").upsert(payload, on_conflict="programme_id").execute().data[0]["id"]
        # У строк требований нет своего естественного ключа — как у слагаемых
        # формулы: сносим и вставляем заново.
        client.table("programme_requirement").delete().eq("requirement_set_id", set_id).execute()
        if row["requirements"]:
            client.table("programme_requirement").insert(
                [{**item, "requirement_set_id": set_id} for item in row["requirements"]]
            ).execute()
    return restored, missing, collisions


def restore_application_channels(
    client, rows: list[dict], university_ids: dict[str, str], apply: bool  # type: ignore[no-untyped-def]
) -> tuple[int, list[str]]:
    restored = 0
    missing = []
    for row in rows:
        university_id = university_ids.get(row["university_slug"])
        if university_id is None:
            missing.append(
                f"application_channel {row['university_slug']}/{row['degree_level'] or 'все уровни'}: вуза нет в каталоге"
            )
            continue
        restored += 1
        if not apply:
            continue
        payload = {"university_id": university_id, **{k: v for k, v in row.items() if k != "university_slug"}}
        client.table("application_channel").upsert(payload, on_conflict="university_id,degree_level").execute()
    return restored, missing


def main(apply: bool) -> None:
    load_dotenv()
    client = get_service_client()
    snapshot = load_snapshot()

    university_ids = _university_ids(client)
    programme_lookup = _programme_lookup(client, university_ids)

    f_restored, f_missing, f_collisions = restore_formulas(client, snapshot["formulas"], programme_lookup, apply)
    ar_restored, ar_missing = restore_application_rounds(client, snapshot["application_rounds"], university_ids, apply)
    at_restored, at_missing = restore_admission_types(client, snapshot["admission_types"], university_ids, apply)
    pf_restored, pf_missing, pf_collisions, pf_without_method = restore_programme_fields(
        client, snapshot["programme_fields"], programme_lookup, apply
    )
    # .get: в снимках до 2026-10-10 этих двух разделов нет.
    requirement_sets = snapshot.get("requirement_sets", [])
    application_channels = snapshot.get("application_channels", [])
    rs_restored, rs_missing, rs_collisions = restore_requirement_sets(client, requirement_sets, programme_lookup, apply)
    ac_restored, ac_missing = restore_application_channels(client, application_channels, university_ids, apply)

    verb = "восстановлено" if apply else "было бы восстановлено (сухой прогон, для записи запустите с --apply)"
    print(f"формулы: {verb} {f_restored} из {len(snapshot['formulas'])}")
    print(f"сроки подачи: {verb} {ar_restored} из {len(snapshot['application_rounds'])}")
    print(f"типы отбора: {verb} {at_restored} из {len(snapshot['admission_types'])}")
    print(f"направления программ: {verb} {pf_restored} из {len(snapshot['programme_fields'])}")
    print(f"требования к поступающим: {verb} {rs_restored} из {len(requirement_sets)}")
    print(f"каналы подачи: {verb} {ac_restored} из {len(application_channels)}")

    if pf_without_method:
        print(
            f"\nНЕ ВОССТАНОВЛЕНО: у {pf_without_method} направлений в снимке нет способа подтверждения "
            "(снимок сделан до 2026-10-10).\nБаза такую запись не примет. Если база цела — пересоздайте снимок: "
            "python src/backup_verified.py.\nЕсли базы уже нет — способ придётся вписать в снимок вручную "
            "(verification_method: \"rule\" или \"manual\"), см. поле verified_by каждой записи."
        )

    missing = f_missing + ar_missing + at_missing + pf_missing + rs_missing + ac_missing
    if missing:
        print(f"\nне нашлось в текущем каталоге ({len(missing)}):")
        for line in missing:
            print(f"  {line}")

    collisions = f_collisions + pf_collisions + rs_collisions
    if collisions:
        print(f"\nПОХОЖЕ НА ПЕРЕСЛАГОВАНИЕ, НЕ ВОССТАНОВЛЕНО АВТОМАТИЧЕСКИ ({len(collisions)}):")
        for line in collisions:
            print(f"  {line}")


def selftest() -> None:
    """Логика сопоставления слагов/полезной нагрузки — без обращения к
    настоящей базе (поддельный client, фиксирует форму upsert-вызовов)."""

    class FakeTable:
        def __init__(self, name: str, store: dict) -> None:
            self.name = name
            self.store = store
            self._payload = None

        def upsert(self, payload, on_conflict=None):  # type: ignore[no-untyped-def]
            self._payload = payload
            self.store.setdefault(self.name, []).append(payload)
            return self

        def select(self, *_a, **_k):  # type: ignore[no-untyped-def]
            return self

        def eq(self, *_a, **_k):  # type: ignore[no-untyped-def]
            return self

        def delete(self):  # type: ignore[no-untyped-def]
            return self

        def insert(self, rows):  # type: ignore[no-untyped-def]
            self.store.setdefault(self.name + "_children", []).extend(rows)
            return self

        def execute(self):  # type: ignore[no-untyped-def]
            data = [{"id": "fake-id"}] if self._payload is not None else []
            return type("Result", (), {"data": data})()

    class FakeClient:
        def __init__(self) -> None:
            self.store: dict = {}

        def table(self, name):  # type: ignore[no-untyped-def]
            return FakeTable(name, self.store)

    client = FakeClient()
    programme_lookup = {
        ("lu", "sociology"): {"id": "prog-1", "name_lv": "Socioloģija"},
        ("lu", "renamed-slug"): {"id": "prog-2", "name_lv": "Совсем другая программа"},
    }
    university_ids = {"lu": "uni-1"}

    restored, missing, collisions = restore_formulas(
        client,
        [
            {
                "university_slug": "lu",
                "programme_slug": "sociology",
                "programme_name": "Socioloģija",
                "variant": "ce",
                "valid_from": "2026-01-01",
                "valid_to": None,
                "source_url": "https://example.com",
                "source_doc": "doc",
                "source_doc_number": "1",
                "source_doc_date": "2026-01-01",
                "source_copy_path": "p",
                "source_copy_sha256": "a" * 64,
                "source_excerpt": "excerpt",
                "verified_at": "2026-09-20T00:00:00Z",
                "verified_by": "owner",
                "terms": [{"kind": "ce", "subject": "latvian", "coefficient": 1.0, "optional": False}],
                "gates": [],
            },
            {
                "university_slug": "lu",
                "programme_slug": "does-not-exist",
                "programme_name": "Что угодно",
                "variant": "ce",
                "valid_from": "2026-01-01",
                "valid_to": None,
                "source_url": None,
                "source_doc": None,
                "source_doc_number": None,
                "source_doc_date": None,
                "source_copy_path": None,
                "source_copy_sha256": None,
                "source_excerpt": None,
                "verified_at": "2026-09-20T00:00:00Z",
                "verified_by": "owner",
                "terms": [],
                "gates": [],
            },
            {
                # слаг нашёлся, но по нему сейчас СОВСЕМ ДРУГАЯ программа —
                # переслагование каталога между снимком и восстановлением;
                # не восстанавливаем молча, даже с --apply
                "university_slug": "lu",
                "programme_slug": "renamed-slug",
                "programme_name": "Старая программа с этим именем",
                "variant": "ce",
                "valid_from": "2026-01-01",
                "valid_to": None,
                "source_url": None,
                "source_doc": None,
                "source_doc_number": None,
                "source_doc_date": None,
                "source_copy_path": None,
                "source_copy_sha256": None,
                "source_excerpt": None,
                "verified_at": "2026-09-20T00:00:00Z",
                "verified_by": "owner",
                "terms": [],
                "gates": [],
            },
        ],
        programme_lookup,
        apply=True,
    )
    assert restored == 1, restored
    assert len(missing) == 1 and "does-not-exist" in missing[0], missing
    assert len(collisions) == 1 and "renamed-slug" in collisions[0], collisions
    assert "prog-2" not in [call.get("programme_id") for call in client.store.get("formula", [])]
    assert client.store["formula"][0]["programme_id"] == "prog-1"
    assert client.store["formula"][0]["verified_at"] == "2026-09-20T00:00:00Z"
    assert client.store["formula_term_children"][0]["subject"] == "latvian"

    restored_ar, missing_ar = restore_application_rounds(
        client,
        [{"university_slug": "lu", "label": "1. kārta", "degree_level": None, "language_of_instruction": None,
          "opens_on": "2027-01-05", "closes_on": None, "note": None, "source_url": None,
          "verified_at": "2026-09-20T00:00:00Z", "verified_by": "owner"}],
        university_ids,
        apply=True,
    )
    assert restored_ar == 1
    assert client.store["application_round"][0]["university_id"] == "uni-1"
    assert "university_slug" not in client.store["application_round"][0]

    # Формула: дата снятия копии пишется, только если снимок её хранит.
    assert "source_copy_fetched_on" not in client.store["formula"][0]

    # Направление: способ подтверждения доходит до базы; запись без него
    # (старый снимок) не пишется вовсе и считается отдельно.
    field = {
        "university_slug": "lu", "programme_slug": "sociology", "programme_name": "Socioloģija",
        "field_code": "0314", "source": "name_rule",
        "verified_at": "2026-10-01T00:00:00Z", "verified_by": "owner",
    }
    restored_pf, missing_pf, collisions_pf, without_method = restore_programme_fields(
        client, [{**field, "verification_method": "rule"}, field], programme_lookup, apply=True
    )
    assert (restored_pf, missing_pf, collisions_pf, without_method) == (1, [], [], 1)
    assert len(client.store["programme_field"]) == 1
    assert client.store["programme_field"][0]["verification_method"] == "rule"

    # Требования: заголовок набора и его строки; служебные ключи снимка в
    # базу не уходят.
    restored_rs, missing_rs, collisions_rs = restore_requirement_sets(
        client,
        [
            {
                "university_slug": "lu", "programme_slug": "sociology", "programme_name": "Socioloģija",
                "source_url": "https://example.com", "source_doc": "doc", "source_doc_number": "1",
                "source_doc_date": "2026-01-01", "source_copy_path": "p", "source_copy_sha256": "a" * 64,
                "source_copy_fetched_on": "2026-09-20", "source_excerpt": "excerpt",
                "verified_at": "2026-10-25T00:00:00Z", "verified_by": "owner",
                "requirements": [
                    {"subject": "physics", "min_level": None, "alternative_group": "A", "note": None},
                    {"subject": "chemistry", "min_level": None, "alternative_group": "A", "note": None},
                ],
            },
            {"university_slug": "lu", "programme_slug": "does-not-exist", "programme_name": "X", "requirements": []},
        ],
        programme_lookup,
        apply=True,
    )
    assert (restored_rs, collisions_rs) == (1, []) and len(missing_rs) == 1, (restored_rs, missing_rs, collisions_rs)
    saved_set = client.store["programme_requirement_set"][0]
    assert saved_set["programme_id"] == "prog-1" and saved_set["verified_at"] == "2026-10-25T00:00:00Z"
    assert not {"university_slug", "programme_slug", "programme_name", "requirements"} & set(saved_set)
    saved_rows = client.store["programme_requirement_children"]
    assert [r["subject"] for r in saved_rows] == ["physics", "chemistry"]
    assert all(r["requirement_set_id"] == "fake-id" for r in saved_rows)

    # Канал подачи: запись на все уровни вуза (degree_level пустой) доходит как есть.
    restored_ac, missing_ac = restore_application_channels(
        client,
        [
            {"university_slug": "lu", "degree_level": None, "channel_type": "unified_portal",
             "url": "https://example.com/apply", "source_url": "https://example.com", "source_excerpt": None,
             "verified_at": "2026-12-01T00:00:00Z", "verified_by": "owner"},
            {"university_slug": "nope", "degree_level": "master", "channel_type": "university",
             "url": "https://example.com", "source_url": "https://example.com", "source_excerpt": None,
             "verified_at": "2026-12-01T00:00:00Z", "verified_by": "owner"},
        ],
        university_ids,
        apply=True,
    )
    assert restored_ac == 1 and len(missing_ac) == 1 and "nope/master" in missing_ac[0], missing_ac
    saved_channel = client.store["application_channel"][0]
    assert saved_channel["university_id"] == "uni-1" and saved_channel["degree_level"] is None
    assert "university_slug" not in saved_channel

    # Чтение страницами: 1005 строк приходят двумя запросами и все доходят.
    class FakeQuery:
        calls: list[tuple[int, int]] = []

        def range(self, start, end):  # type: ignore[no-untyped-def]
            FakeQuery.calls.append((start, end))
            self._slice = list(range(1005))[start : end + 1]
            return self

        def execute(self):  # type: ignore[no-untyped-def]
            return type("Result", (), {"data": [{"id": n} for n in self._slice]})()

    fetched = fetch_all(FakeQuery)
    assert [row["id"] for row in fetched] == list(range(1005))
    assert FakeQuery.calls == [(0, PAGE_ROWS - 1), (PAGE_ROWS, 2 * PAGE_ROWS - 1)], FakeQuery.calls

    print("самотест пройден")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        main(apply="--apply" in sys.argv)
