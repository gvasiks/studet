"""Vidzemes Augstskola (ViA) — НЕ со своего сайта.

Собственный сайт ViA (va.lv) нерабочий для наших целей: английский
раздел прямо пишет "программы для иностранцев в разработке", а
латышская страница бакалавриата структурно пуста (118 КБ разметки без
единого слова контента — проверено дважды вручную в браузере). Вместо
этого — независимая государственная база NIID.lv (Nacionālā izglītības
iespēju datubāze, гособразовательный портал; PLAN.md уже называл её как
источник для сверки полноты категорий интересов). Там все 16 программ
ViA лежат со структурированными фактами напрямую на странице списка —
заходить на отдельные страницы программ не нужно.

Структура найдена вручную в браузере 2026-09-13: одна `<table
class="results_list">`, программы разделены строками `tr.title`
(название + ссылка), дальше идут `<tr><td>` со связками
"Label:значение" (Grāds, Programmas veids, Valoda, Studiju veids,
Ilgums, Mācību/studiju maksa) вплоть до разделителя `tr.lo_spacing`.
2 страницы (`?page=2`), 16 программ.

"Valoda: latviešu/angļu (LV/EN)" — комбинированные программы (обычно
докторантура) — делим на два языковых варианта, как и у прошлых
источников. Все 16 программ — в Валмиерā (ATRAŠANĀS VIETA в фильтрах
подтверждает единогласно).
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from playwright.sync_api import Page, sync_playwright

from models import ProgrammeDraft, UniversityDraft

BASE_URL = "https://www.niid.lv"
LISTING_URLS = [
    "https://www.niid.lv/niid_search/provider/Vidzemes%20Augstskola?qy&tg=",
    "https://www.niid.lv/niid_search/provider/Vidzemes%20Augstskola?qy&tg=&page=2",
]

UNIVERSITY = UniversityDraft(
    slug="via",
    name_lv="Vidzemes Augstskola",
    name_en="Vidzeme University of Applied Sciences",
    kind="public",
    city="valmiera",
    website_url="https://va.lv",
    source_url=LISTING_URLS[0],
)

_EXTRACT_JS = """
() => {
  const LABELS = ['Grāds', 'Profesionālā kvalifikācija', 'Programmas veids', 'Valoda', 'Studiju veids', 'Izglītības ieguves forma', 'Ilgums', 'Mācību/studiju maksa'];
  function extractFields(text) {
    const positions = [];
    for (const label of LABELS) {
      const marker = label + ':';
      let idx = 0;
      while (true) {
        idx = text.indexOf(marker, idx);
        if (idx === -1) break;
        positions.push([idx, label]);
        idx += marker.length;
      }
    }
    positions.sort((a, b) => a[0] - b[0]);
    const fields = {};
    for (let i = 0; i < positions.length; i++) {
      const [idx, label] = positions[i];
      const start = idx + label.length + 1;
      const end = i + 1 < positions.length ? positions[i + 1][0] : text.length;
      fields[label] = text.slice(start, end).trim();
    }
    return fields;
  }

  const titleRows = Array.from(document.querySelectorAll('tr.title'));
  const results = [];
  for (const tr of titleRows) {
    const link = tr.querySelector('a');
    if (!link) continue;
    let text = '';
    let sib = tr.nextElementSibling;
    while (sib && !sib.classList.contains('lo_spacing') && !sib.classList.contains('title')) {
      text += sib.innerText + '\\n';
      sib = sib.nextElementSibling;
    }
    results.push({ name: link.textContent.trim(), href: link.getAttribute('href'), fields: extractFields(text) });
  }
  return results;
}
"""


def _map_level(programme_type: str) -> str:
    lowered = programme_type.lower()
    if "doktora" in lowered or "trešā cikla" in lowered:
        return "doctoral"
    if "maģistra" in lowered or "otrā cikla" in lowered:
        return "master"
    return "bachelor"


def _extract_languages(value: str) -> list[str]:
    lowered = value.lower()
    languages = [lang for lang, key in (("lv", "latvie"), ("en", "angļu")) if key in lowered]
    return languages or ["lv"]


def _parse_years(value: str) -> float | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)", value)
    return float(match.group(1).replace(",", ".")) if match else None


def _parse_price(value: str) -> float | None:
    match = re.search(r"([\d]+(?:[.,]\d+)?)\s*EUR", value)
    return float(match.group(1).replace(",", ".")) if match else None


def _funding_type(fee_text: str) -> str:
    return "both" if "budžet" in fee_text.lower() else "paid"


def _programme_id(href: str) -> str:
    match = re.search(r"/program/(\d+)", href)
    return match.group(1) if match else href


def scrape() -> tuple[UniversityDraft, list[ProgrammeDraft]]:
    programmes: list[ProgrammeDraft] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        entries = []
        for listing_url in LISTING_URLS:
            page.goto(listing_url, wait_until="domcontentloaded")
            entries.extend(page.evaluate(_EXTRACT_JS))

        browser.close()

    for entry in entries:
        fields = entry["fields"]
        fee_text = fields.get("Mācību/studiju maksa", "")
        languages = _extract_languages(fields.get("Valoda", ""))
        multiple = len(languages) > 1
        programme_id = _programme_id(entry["href"])
        source_url = urljoin(BASE_URL, entry["href"])

        for language in languages:
            programmes.append(
                ProgrammeDraft(
                    slug=f"{programme_id}-{language}" if multiple else programme_id,
                    name_lv=entry["name"],
                    degree_level=_map_level(fields.get("Programmas veids", "")),
                    language_of_instruction=language,
                    study_mode="full_time",
                    city=UNIVERSITY.city,
                    funding_type=_funding_type(fee_text),
                    tuition_fee_amount=_parse_price(fee_text),
                    duration_years=_parse_years(fields.get("Ilgums", "")),
                    source_url=source_url,
                )
            )

    return UNIVERSITY, programmes
