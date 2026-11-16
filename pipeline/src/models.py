"""Черновики записей каталога. Ничего отсюда не попадает в базу как
подтверждённый факт: verified_at/verified_by эти модели вообще не знают —
их проставляет только человек, отдельно (CLAUDE.md, правило 6)."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, field_validator


class UniversityDraft(BaseModel):
    slug: str
    # ISO 3166-1 alpha-2, как university.country. По умолчанию Латвия: так
    # латвийским сборщикам ничего менять не нужно.
    country: str = "LV"
    # Название на языке страны: name_lv у латвийских, name_lt у литовских,
    # name_et у эстонских.
    name_lv: str | None = None
    name_lt: str | None = None
    name_et: str | None = None
    name_en: str | None = None
    kind: str  # 'public' | 'private'
    city: str
    website_url: str | None = None
    source_url: str


class ProgrammeDraft(BaseModel):
    slug: str
    name_lv: str | None = None
    name_lt: str | None = None
    name_et: str | None = None
    name_en: str | None = None
    degree_level: str
    # 'lv' | 'en' (у Литвы ещё 'lt', 'ru'…). Пусто — сборщик не смог
    # прочитать язык: страница не открылась или значение не распознано.
    # Подставлять вместо этого «скорее всего латышский» нельзя — язык
    # обучения из тех фактов, что подтверждает человек (правило 6
    # CLAUDE.md). Что с пустым значением делает запись — см.
    # catalog_diff.drop_new_without.
    language_of_instruction: str | None = None
    # 'full_time' | 'part_time' | 'distance'. Пусто — только там, где
    # источник формы обучения не сообщает (Эстония: её нет в данных
    # государственного портала). Латвийские и литовские сборщики передают
    # значение всегда.
    study_mode: str | None = None
    city: str | None = None
    # 'budget' | 'paid' | 'both'. Пусто — только там, где источник этого не
    # сообщает (Литва: бюджетные места делятся по направлениям, не по
    # программам). Латвийские сборщики передают значение всегда.
    funding_type: str | None = None
    tuition_fee_amount: float | None = None
    tuition_fee_currency: str = "EUR"
    budget_places: int | None = None
    duration_years: float | None = None
    accreditation_valid_until: date | None = None
    description_lv: str | None = None
    description_en: str | None = None
    # Литва: степень и описание приходят тем же сбором, что и сама программа
    # (карточка государственного реестра), поэтому лежат в черновике. У
    # латвийских программ эти сведения дописывают отдельные скрипты enrich_*.
    description_lt: str | None = None
    degree_awarded_lt: str | None = None
    # Эстония: степень приходит тем же запросом, что и сама программа.
    degree_awarded_et: str | None = None
    details_source_url: str | None = None
    details_extracted_at: str | None = None
    source_url: str

    @field_validator("duration_years")
    @classmethod
    def _as_stored(cls, value: float | None) -> float | None:
        """Один знак после запятой — столько хранит programme.duration_years
        (numeric(3, 1)). Без этого «2 gadi un 1 mēnesis» = 2.0833… база
        записывала как 2.1, а следующий сбор видел «2.1 → 2.0833» — изменение
        каждую неделю (Juridiskā koledža, сентябрь–ноябрь 2026), и у
        подтверждённой программы снималось бы подтверждение.
        Половина — вверх, как у Postgres (3.25 -> 3.3); round() Python дал бы 3.2."""
        if value is None:
            return None
        return float(Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
