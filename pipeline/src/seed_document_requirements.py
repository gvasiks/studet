"""Черновики чек-листа документов для иностранцев — таблица foreign_document_requirement.

Продукт для иностранцев, шаг 3 (docs/PLAN-FOREIGNERS.md): «что собрать» на
карточке английской программы. Решение владельца 2026-11-14: строки видны на
сайте только подтверждёнными, поэтому скрипт пишет ТОЛЬКО ЧЕРНОВИКИ —
verified_at проставляет владелец в Studio. Уже подтверждённые строки не
трогаются.

Строки выписаны вручную 2026-11-14 со страниц вузов; у каждой дословная
цитата (source_excerpt), по которой проверяющий сверяет строку:
- РТУ: rtu.lv/en/studies/admission-1 (что загрузить при подаче), три страницы
  «Immigration regulations» (что подготовить до приезда) и apply.rtu.lv
  (справка для выпускников, страница от 26.03.2026);
- ЛУ: lu.lv/en/admissions/degree-studies/;
- RISEBA: правила приёма 2026/2027 (riseba.lv/en/come-study/terms-of-enrolment/),
  список общий для всех поступающих; справку AIC о признании образования
  абитуриент прикладывает сам (у ЛУ и RSU её запрашивает вуз);
- RSU: правила приёма на английские программы 2026/2027 (PDF, глава V).
  У RSU у каждой программы своё приложение к правилам (медицина, стоматология
  и др. просят больше) — здесь только общий список главы V.
BA с ноября 2026 перенаправляет на LU FinTech Business School (ftbs.lu.lv) и
пропущена решением владельца 2026-11-09. Turība, TSI и ViA запрещают обход агентам Anthropic в robots.txt — их списки
вносятся вручную. Докторантура не заполнена: у РТУ и ЛУ для неё отдельный
порядок.

Сумм здесь нет намеренно (подтверждение средств, взнос за заявление): это
поля правила 6, они живут в блоке стоимости.

  python src/seed_document_requirements.py            # показать, что будет записано
  python src/seed_document_requirements.py --apply    # записать черновики
  python src/seed_document_requirements.py --selftest # проверка самой таблицы, без сети и базы
"""

from __future__ import annotations

import sys

# Совпадает с check в миграциях 20261114120000 и 20261114130000 и с src/lib/foreign-documents.ts.
DOCUMENTS = {
    "passport", "photo", "secondary_diploma", "bachelor_diploma", "transcript",
    "enrolment_letter", "english_translation", "legalisation", "aic_statement", "english_certificate",
    "motivation_letter", "cv", "recommendation_letters", "criminal_record",
    "minor_documents", "proof_of_funds", "application_fee_receipt",
}
APPLIES_TO = {"all", "docs_issued_outside_eu", "non_eu_citizens", "visa_required", "under_18", "final_year"}
STAGES = {"application", "before_arrival"}
LEVELS = {"college", "bachelor", "master", "doctoral"}

RTU_ADMISSION = "https://www.rtu.lv/en/studies/admission-1"
RTU_VISA = "https://www.rtu.lv/en/studies/immigration-regulations/entry-with-a-visa"
RTU_VISA_FREE = "https://www.rtu.lv/en/studies/immigration-regulations/visa-free-entry"
RTU_EU = "https://www.rtu.lv/en/studies/immigration-regulations/eu-member-states-the-european-economic-area-switzerland"
RTU_BACHELOR_DOCS = "https://apply.rtu.lv/news/new/35-required-education-documents-bachelors-students"
LU_ADMISSION = "https://www.lu.lv/en/admissions/degree-studies/"
RISEBA_TERMS = "https://riseba.lv/en/come-study/terms-of-enrolment/"
RSU_PROCEDURE = "https://www.rsu.lv/sites/default/files/imce/SSD/admissions_procedure_2026_2027_eng.pdf"

BM = ["bachelor", "master"]

# (вуз, уровни, документ, кому, этап, note, источник, цитата)
ROWS: list[tuple] = [
    # --- РТУ: при подаче (Admission/How to Apply, Step 1) ---
    ("rtu", ["bachelor"], "secondary_diploma", "all", "application", "With a transcript, in the original language.",
     RTU_ADMISSION, "Bachelor's applicants - your secondary education certificate with a transcript in the original language and an official translation in English;"),
    ("rtu", ["master"], "bachelor_diploma", "all", "application", "With a transcript, in the original language.",
     RTU_ADMISSION, "Master's applicants - your Bachelor’s degree certificate with a transcript in the original language and an official translation in English;"),
    ("rtu", BM, "transcript", "all", "application", None,
     RTU_ADMISSION, "your secondary education certificate with a transcript in the original language and an official translation in English;"),
    ("rtu", BM, "english_translation", "all", "application", "Official translation of the diploma and transcript.",
     RTU_ADMISSION, "with a transcript in the original language and an official translation in English;"),
    ("rtu", BM, "english_certificate", "all", "application",
     "Or a letter from your school/university that English was the medium of instruction.",
     RTU_ADMISSION, "An internationally recognised English language certificate (please see the accepted certificate list below), or a report from your school/university stating that English was the medium of instruction for the entirety of your previous study level."),
    ("rtu", BM, "motivation_letter", "all", "application", None,
     RTU_ADMISSION, "A cover/motivation letter highlighting why you would like to study in this programme and what your future academic and career aspirations are;"),
    ("rtu", BM, "cv", "all", "application", "Especially important for master's applicants and after a study break.",
     RTU_ADMISSION, "Your Curriculum Vitae (especially important for Master's students and applicants who have had a study break);"),
    ("rtu", BM, "passport", "all", "application", None, RTU_ADMISSION, "Your passport."),
    ("rtu", ["bachelor"], "enrolment_letter", "final_year", "application",
     "Current grade transcripts and a letter confirming enrolment and expected graduation date.",
     RTU_BACHELOR_DOCS, "You should upload your current grade transcripts and an official letter from your university that confirms your enrollment and expected graduation date."),
    # --- РТУ: до приезда (Immigration regulations) ---
    ("rtu", BM, "legalisation", "docs_issued_outside_eu", "before_arrival",
     "Not needed for documents issued in the EU, EEA, Switzerland or the United Kingdom.",
     RTU_EU, "If you obtained your previous level of education in a non-member state, you must legalise your final diplomas in the country the documents were issued. … If the document was issued in the EU, the member states of the European Economic Zone, the Swiss Confederation and in the United Kingdom of Great Britain and Northern Ireland (except overseas territories), legalisation is not necessary."),
    ("rtu", BM, "criminal_record", "visa_required", "before_arrival",
     "From your citizenship country (or the country where you lived over 12 months); legalised, with a notarised English translation.",
     RTU_VISA, "A criminal record statement issued by a competent institution of the citizenship country (or the host country, if a foreigner has resided in that country longer than 12 months);"),
    ("rtu", BM, "minor_documents", "under_18", "before_arrival", "Legalised.",
     RTU_VISA_FREE, "Students under the age of 18 must additionally legalise their original birth certificate and their guardianship letter."),
    ("rtu", BM, "proof_of_funds", "non_eu_citizens", "before_arrival",
     "A Living Expenses letter from RTU or an original bank statement.",
     RTU_VISA_FREE, "Evidence of sufficient financial means (9400 EUR) - This can be in the form of a Living Expenses letter issued by RTU or a bank statement original obtained from your bank."),
    # --- ЛУ: при подаче (Step 2) и легализация (Step 3) ---
    ("lu", ["bachelor"], "secondary_diploma", "all", "application", "In the original language, with a notarised English copy.",
     LU_ADMISSION, "General secondary school diploma/certificate in the original language and a notarised copy in English (for Bachelor's degree applicants);"),
    ("lu", ["master"], "bachelor_diploma", "all", "application", "In the original language, with a notarised English copy.",
     LU_ADMISSION, "Bachelor’s degree diploma in the original language and a notarised copy in English (for Master's degree applicants);"),
    ("lu", BM, "transcript", "all", "application", "Or final examination results; diploma supplement too.",
     LU_ADMISSION, "Transcript of grades or final examination results in the original language and a notarised copy in English;"),
    ("lu", BM, "english_translation", "all", "application", "Notarised; documents are accepted only as PDF.",
     LU_ADMISSION, "Depending on the level of the chosen study programme, applicants must provide the original final diploma and transcript of records, or final examination results in the original language, along with a notarised translation into English."),
    ("lu", BM, "motivation_letter", "all", "application", "If the programme requires it.", LU_ADMISSION, "Motivation letter (if required);"),
    ("lu", BM, "cv", "all", "application", "If the programme requires it.", LU_ADMISSION, "CV (if required);"),
    ("lu", BM, "english_certificate", "all", "application",
     "Not needed if your previous education was in English in Australia, the Bahamas, Canada, Ireland, New Zealand, St Vincent and the Grenadines, the UK or the USA.",
     LU_ADMISSION, "English language proficiency document. This is not required if previous education was obtained in English in one of the below-listed countries:"),
    ("lu", BM, "passport", "all", "application", "A copy.", LU_ADMISSION, "Passport copy;"),
    ("lu", BM, "photo", "all", "application", None, LU_ADMISSION, "One photograph;"),
    ("lu", BM, "application_fee_receipt", "all", "application", None,
     LU_ADMISSION, "A payment confirmation document must be uploaded to the admission portal together with all other required admission documents."),
    ("lu", BM, "legalisation", "docs_issued_outside_eu", "before_arrival",
     "Under the Hague Convention. Best done before applying; must be done before the visa or residence permit application.",
     LU_ADMISSION, "Step 3: Legalisation of documents (documents issued in non-EU/EEA countries) … NB! Applicants are advised to complete the legalisation of their documents before applying for studies, and this step must be fully completed before applying for a visa or residence permit."),
    # --- RISEBA: правила приёма 2026/2027 ---
    ("riseba", ["bachelor"], "secondary_diploma", "all", "application",
     "A copy; show the original when signing the study agreement. Can be added after you graduate.",
     RISEBA_TERMS, "a copy of the proof of previous education (original) / proof can be provided upon receipt of the document after graduation;"),
    ("riseba", ["master"], "bachelor_diploma", "all", "application", "A copy; show the original when signing the study agreement.",
     RISEBA_TERMS, "a copy of the proof of previous education (original) / proof can be provided upon receipt of the document after graduation;"),
    ("riseba", BM, "aic_statement", "all", "application",
     "For education obtained abroad: which Latvian degree or diploma it corresponds to (aic.lv).",
     RISEBA_TERMS, "If the applicant has acquired previous education or degrees abroad, the educational documents must be accompanied by a statement from the Academic Information Center on the recognition of education and equalization with the level of education in Latvia;"),
    ("riseba", BM, "photo", "all", "application", "A portrait photo.",
     RISEBA_TERMS, "a portrait photo in a size appropriate to the document format;"),
    ("riseba", ["master"], "cv", "all", "application", None,
     RISEBA_TERMS, "a curriculum vitae (CV) – only for the candidates for the master’s programme;"),
    ("riseba", BM, "passport", "all", "application", "A copy of the passport or ID card; show the original.",
     RISEBA_TERMS, "a copy of your passport or ID card (original)."),
    ("riseba", BM, "application_fee_receipt", "all", "application", "A payment order from the online bank.",
     RISEBA_TERMS, "registration fee (payment order from the online bank):"),
    # --- RSU: правила приёма 2026/2027, глава V ---
    ("rsu", ["bachelor"], "secondary_diploma", "all", "application", "Original language and English.",
     RSU_PROCEDURE, "educational documents (Secondary school leaving diploma and the official transcript, Bachelor's diploma and the official transcript, Master’s diploma and the official transcript, etc.) both in original language and in English"),
    ("rsu", ["master"], "bachelor_diploma", "all", "application", "Original language and English.",
     RSU_PROCEDURE, "educational documents (Secondary school leaving diploma and the official transcript, Bachelor's diploma and the official transcript, Master’s diploma and the official transcript, etc.) both in original language and in English"),
    ("rsu", BM, "transcript", "all", "application", "The official transcript.",
     RSU_PROCEDURE, "educational documents (Secondary school leaving diploma and the official transcript, Bachelor's diploma and the official transcript, Master’s diploma and the official transcript, etc.) both in original language and in English"),
    ("rsu", BM, "english_translation", "all", "application",
     "For documents not in Latvian or English: by the issuing authority, a notary or a registered translator.",
     RSU_PROCEDURE, "If the documents are in a language other than Latvian or English, the applicant shall upload them in the original language together with a translation of the documents into English."),
    ("rsu", BM, "legalisation", "docs_issued_outside_eu", "application", "Apostille or legalisation, before uploading.",
     RSU_PROCEDURE, "Where relevant (usually for documents issued in non-EU/EEA countries), prior to the uploading of the documents, the applicant shall ensure the certification of documents with an Apostille or their legalisation in the country of document origin"),
    ("rsu", BM, "recommendation_letters", "all", "application", "On the RSU form, not older than 2 years.",
     RSU_PROCEDURE, "RSU will only accept letters of recommendation for the Admission Competition if they are prepared using the designated RSU form."),
    ("rsu", BM, "motivation_letter", "all", "application", "On the RSU form, not older than 2 years.",
     RSU_PROCEDURE, "RSU will only accept letters of motivation for the Admission Competition if they are prepared using the designated RSU form."),
    ("rsu", BM, "english_certificate", "all", "application", None,
     RSU_PROCEDURE, "results of the internationally recognised English proficiency test"),
    ("rsu", BM, "passport", "all", "application", "Data page, or an ID card.",
     RSU_PROCEDURE, "a passport (data page) or a personal identity card (ID card)"),
    ("rsu", BM, "photo", "all", "application", "Taken in the last 6 months, plain light background.",
     RSU_PROCEDURE, "Photo – to be uploaded onto the section “Personal Information” of the eA Portal."),
    ("rsu", BM, "application_fee_receipt", "all", "application", None,
     RSU_PROCEDURE, "application fee payment confirmation (such as payment slip, bank reference, bank statement, bank transfer printout etc.)"),
]


def expanded() -> list[dict]:
    rows = []
    for order, (university, levels, document, applies_to, stage, note, source_url, excerpt) in enumerate(ROWS):
        for level in levels:
            rows.append({
                "university": university,
                "degree_level": level,
                "document": document,
                "applies_to": applies_to,
                "stage": stage,
                "note": note,
                "sort_order": order,
                "source_url": source_url,
                "source_excerpt": excerpt,
            })
    return rows


def selftest() -> None:
    seen: set[tuple] = set()
    for row in expanded():
        assert row["document"] in DOCUMENTS, row
        assert row["applies_to"] in APPLIES_TO, row
        assert row["stage"] in STAGES, row
        assert row["degree_level"] in LEVELS, row
        assert row["source_url"].startswith("https://"), row
        assert row["source_excerpt"].strip(), row
        # сумм в чек-листе нет: они — поля правила 6 и живут в блоке стоимости
        assert "EUR" not in (row["note"] or "") and "€" not in (row["note"] or ""), row
        key = (row["university"], row["degree_level"], row["document"], row["applies_to"])
        assert key not in seen, key
        seen.add(key)
    print(f"selftest ok: {len(ROWS)} записей, {len(seen)} строк")


def main(apply: bool) -> None:
    from dotenv import load_dotenv

    from db import get_service_client
    from db_retry import execute

    load_dotenv()
    client = get_service_client()
    universities = {row["slug"]: row["id"] for row in execute(client.table("university").select("id, slug")).data}
    try:
        existing = {
            (row["university_id"], row["degree_level"], row["document"], row["applies_to"]): row
            for row in execute(
                client.table("foreign_document_requirement").select("university_id, degree_level, document, applies_to, verified_at")
            ).data
        }
    except Exception as exc:  # noqa: BLE001
        if apply:
            raise SystemExit(f"foreign_document_requirement не читается ({exc}) — сначала примените миграцию в Studio") from exc
        print("foreign_document_requirement ещё нет в базе (миграция не применена) — показываю черновики без сверки\n")
        existing = {}

    written = skipped = 0
    for source in expanded():
        if source["university"] not in universities:
            raise SystemExit(f"вуза {source['university']!r} нет в таблице university")
        row = {key: value for key, value in source.items() if key != "university"}
        row["university_id"] = universities[source["university"]]
        prior = existing.get((row["university_id"], row["degree_level"], row["document"], row["applies_to"]))
        if prior and prior["verified_at"]:
            skipped += 1
            continue
        print(f"{source['university']:4} {row['degree_level']:9} {row['stage']:15} {row['document']:24} {row['applies_to']}")
        if apply:
            # verified_at/verified_by в записи нет — их ставит только человек
            execute(client.table("foreign_document_requirement").upsert(
                row, on_conflict="university_id,degree_level,document,applies_to"
            ))
            written += 1
    print(f"\nуже подтверждено (не трогаю): {skipped}")
    print(f"записано: {written}" + ("" if apply else " (сухой прогон — запись только с --apply)"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv:
        selftest()
    else:
        main("--apply" in sys.argv)
