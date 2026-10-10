"""Черновики записей каталога. Ничего отсюда не попадает в базу как
подтверждённый факт: verified_at/verified_by эти модели вообще не знают —
их проставляет только человек, отдельно (CLAUDE.md, правило 6)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class UniversityDraft(BaseModel):
    slug: str
    # ISO 3166-1 alpha-2, как university.country. По умолчанию Латвия: так
    # латвийским сборщикам ничего менять не нужно.
    country: str = "LV"
    # Название на языке страны: name_lv у латвийских, name_lt у литовских.
    name_lv: str | None = None
    name_lt: str | None = None
    name_en: str | None = None
    kind: str  # 'public' | 'private'
    city: str
    website_url: str | None = None
    source_url: str


class ProgrammeDraft(BaseModel):
    slug: str
    name_lv: str | None = None
    name_lt: str | None = None
    name_en: str | None = None
    degree_level: str
    # 'lv' | 'en' (у Литвы ещё 'lt', 'ru'…). Пусто — сборщик не смог
    # прочитать язык: страница не открылась или значение не распознано.
    # Подставлять вместо этого «скорее всего латышский» нельзя — язык
    # обучения из тех фактов, что подтверждает человек (правило 6
    # CLAUDE.md). Что с пустым значением делает запись — см.
    # catalog_diff.drop_new_without.
    language_of_instruction: str | None = None
    study_mode: str  # 'full_time' | 'part_time' | 'distance'
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
    details_source_url: str | None = None
    details_extracted_at: str | None = None
    source_url: str
