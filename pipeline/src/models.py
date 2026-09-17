"""Черновики записей каталога. Ничего отсюда не попадает в базу как
подтверждённый факт: verified_at/verified_by эти модели вообще не знают —
их проставляет только человек, отдельно (CLAUDE.md, правило 6)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class UniversityDraft(BaseModel):
    slug: str
    name_lv: str
    name_en: str | None = None
    kind: str  # 'public' | 'private'
    city: str
    website_url: str | None = None
    source_url: str


class ProgrammeDraft(BaseModel):
    slug: str
    name_lv: str | None = None
    name_en: str | None = None
    degree_level: str
    language_of_instruction: str  # 'lv' | 'en'
    study_mode: str  # 'full_time' | 'part_time' | 'distance'
    city: str | None = None
    funding_type: str  # 'budget' | 'paid' | 'both'
    tuition_fee_amount: float | None = None
    tuition_fee_currency: str = "EUR"
    budget_places: int | None = None
    duration_years: float | None = None
    accreditation_valid_until: date | None = None
    description_lv: str | None = None
    description_en: str | None = None
    source_url: str
