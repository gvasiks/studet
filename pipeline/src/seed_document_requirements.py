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

# Совпадает с check в миграциях 20261114120000, 20261114130000, 20261120120000 и 20261123120000 и с src/lib/foreign-documents.ts.
DOCUMENTS = {
    "passport", "photo", "secondary_diploma", "bachelor_diploma", "transcript",
    "enrolment_letter", "english_translation", "legalisation", "aic_statement", "english_certificate",
    "motivation_letter", "cv", "recommendation_letters", "criminal_record",
    "minor_documents", "proof_of_funds", "application_fee_receipt",
    "recognition",  # миграция 20261120120000
    "test_score",  # миграция 20261123120000
}
APPLIES_TO = {"all", "docs_issued_outside_eu", "non_eu_citizens", "visa_required", "under_18", "final_year"}
STAGES = {"application", "before_arrival", "by_university"}  # by_university — миграция 20261114140000
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
    ("lu", BM, "aic_statement", "all", "by_university", "After the application fee is paid; takes about 4–6 weeks.",
     LU_ADMISSION, "After completing the payment, the applicant will receive a notification from the UL coordinator, who will submit the applicant’s documents to the Academic Information Centre (AIC) for diploma recognition (the estimated duration of this process is 4 to 6 weeks)"),
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
    ("rsu", BM, "aic_statement", "all", "by_university",
     "You can also get it yourself. Not needed for documents issued in Estonia and Lithuania after 07.01.2019.",
     RSU_PROCEDURE, "If the applicant has obtained the educational document or academic degree abroad (not in Latvia), ID responsible employees shall take the necessary actions in the State Education Information System (hereinafter – SEIS) to obtain a reference from the Academic Information Centre"),
    ("rsu", BM, "photo", "all", "application", "Taken in the last 6 months, plain light background.",
     RSU_PROCEDURE, "Photo – to be uploaded onto the section “Personal Information” of the eA Portal."),
    ("rsu", BM, "application_fee_receipt", "all", "application", None,
     RSU_PROCEDURE, "application fee payment confirmation (such as payment slip, bank reference, bank statement, bank transfer printout etc.)"),
]


# --- Литва (решение владельца 2026-11-19): строки выписаны 2026-11-20 со страниц
# вузов для английских программ. Факты Литвы показываются без подтверждения
# человеком, с пометкой «извлечено автоматически» (миграция 20261120120000).
# Не вошли: VU (английской страницы нет, PDF — общий приём LAMA BPO), EHU
# (страница приёма — 404), ILK (сайт отдаёт текст только с JavaScript), KSU
# (robots.txt запрещает обход агентам Anthropic) — их списки вручную. У KTU нет
# легализации и справки о несудимости: они названы только на страницах программ
# apply.ktu.edu, а там robots.txt тоже запрещает обход агентам Anthropic.
VDU_DEGREE = "https://www.vdu.lt/en/studies/degree-studies/"
VDU_DOCS = "https://www.vdu.lt/en/studies/qualification-recognition/requirements-for-documents/"
KU_PROCEDURE = "https://www.ku.lt/en/studies-admission/admission/application-procedure/application-procedure-for-degree-students-and-recognition-of-previous-education"
MRU_ADMISSION = "https://www.mruni.eu/en/admission/"
KTU_RECOGNITION = "https://admissions.ktu.edu/academic-recognition/"
VT_REQUIREMENTS = "https://vilniustech.lt/en/international-students/admission-requirements/"
VT_PROCEDURE = "https://vilniustech.lt/en/international-students/full-time-students/application-procedure/"
ISM_ADMISSION = "https://www.ism.lt/en/admission"
LCC_ADMISSIONS = "https://lcc.lt/admissions"
LMTA_APPLICATION = "https://old.lmta.lt/en/english-lmta-welcomes-foreign-students/english-studies/bachelor-application/"
VIKO_APPLY = "https://en.viko.lt/for-students/how-to-apply/"
VIKO_REQUIREMENTS = "https://en.viko.lt/for-students/admission-requirements/"
VVK_STEPS = "https://www.kolegija.lt/en/application-steps-for-international-students/"
LTVK_RECOGNITION = "https://ltvk.lt/en/for-applicants/enrolment/recognition-of-education-and-qualifications-acquired-abroad/"
LTVK_RULES = "https://ltvk.lt/wp-content/uploads/2026/01/Enrolment-Rules-for-International-Students-2026.pdf"

B = ["bachelor"]
C = ["college"]

ROWS += [
    # --- VDU (Vytautas Magnus University) ---
    ("vdu", B, "secondary_diploma", "all", "application", "With its supplement; average grade at least 60%.",
     VDU_DEGREE, "Copy of High School / Bachelor / Master's degree diploma and its supplement"),
    ("vdu", B, "transcript", "all", "application", None,
     VDU_DEGREE, "Mark sheet / Transcript of Records / Diploma Supplement"),
    ("vdu", B, "english_translation", "all", "application", "For documents not issued in English.",
     VDU_DOCS, "All documents issued in languages other than English should be supplemented with an"),
    ("vdu", B, "legalisation", "docs_issued_outside_eu", "application",
     "Apostille or consular legalisation; not needed for documents from the EU, UK, USA, Canada, Ukraine or Moldova.",
     VDU_DOCS, "Certified with an Apostille – if they were issued in a country that is part of"),
    ("vdu", B, "english_certificate", "all", "application", "B2 level.", VDU_DEGREE, "Proof of English proficiency"),
    ("vdu", B, "motivation_letter", "all", "application", "1200–3000 characters.",
     VDU_DEGREE, "Self written Motivational Letter (1200-3000 characters)."),
    ("vdu", B, "cv", "all", "application", "In English.", VDU_DEGREE, "Curriculum Vitae (Resume) in English."),
    ("vdu", B, "passport", "all", "application", "Both name and surname must be in the passport.",
     VDU_DEGREE, "Copy of passport."),
    ("vdu", B, "photo", "all", "application", "3×4 cm.", VDU_DEGREE, "1 recent photo (3×4 cm)."),
    ("vdu", B, "enrolment_letter", "final_year", "application", "A recent transcript and a certificate in English.",
     VDU_DEGREE, "If the applicant is currently studying in the final year"),
    ("vdu", B, "recognition", "all", "by_university", "VMU assesses the documents itself.",
     VDU_DEGREE, "educational documents will be processed for academic assessment and recognition"),

    # --- KU (Klaipėda University) ---
    ("ku", B, "secondary_diploma", "all", "application", "Only final diplomas; average grade above 60%.",
     KU_PROCEDURE, "Higher school certificate for bachelors degree"),
    ("ku", B, "legalisation", "all", "application", "Apostille.", KU_PROCEDURE, "Document of approval certification (Apostille)"),
    ("ku", B, "english_certificate", "all", "application", "Not required for native English speakers.",
     KU_PROCEDURE, "Proof of English Language proficiency"),
    ("ku", B, "passport", "all", "application", None, KU_PROCEDURE, "Passport copy"),
    ("ku", B, "photo", "all", "application", None, KU_PROCEDURE, "Passport type photo"),
    ("ku", B, "english_translation", "non_eu_citizens", "before_arrival",
     "Originals with official translations into English or Lithuanian, for the residence permit appointment.",
     KU_PROCEDURE, "Official translations in English or Lithuanian"),

    # --- MRU (Mykolas Romeris University) ---
    ("mru", B, "secondary_diploma", "all", "application", "With final grades; at least 60% of the maximum.",
     MRU_ADMISSION, "Secondary education diploma or equivalent including final grades"),
    ("mru", B, "english_certificate", "all", "application",
     "B2; not needed for native speakers; the university's free online test is an alternative.",
     MRU_ADMISSION, "Document proving English language level"),
    ("mru", B, "motivation_letter", "all", "application", "Written without AI assistance; checked with software.",
     MRU_ADMISSION, "Motivational letter"),
    ("mru", B, "passport", "all", "application", "Must show both given name and surname.", MRU_ADMISSION, "Passport copy"),
    ("mru", B, "recognition", "all", "by_university", "Some countries need extra documents — see the country list.",
     MRU_ADMISSION, "while processing the academic verification"),

    # --- KTU (Kaunas University of Technology) ---
    ("ktu", B, "secondary_diploma", "all", "application", "A provisional certificate if the final diploma is not issued yet.",
     KTU_RECOGNITION, "Diploma or degree certificate, if the final diploma is yet to be issued, please include a provisional certification"),
    ("ktu", B, "transcript", "all", "application",
     "In the original language; for some countries the school must send it directly.",
     KTU_RECOGNITION, "The academic transcript, records of grades, or a similar document has to be in the original language."),
    ("ktu", B, "english_translation", "all", "application", "For documents not in English or Lithuanian.",
     KTU_RECOGNITION, "All documents issued in languages other than English or Lithuanian should be supplemented with an official translation."),
    ("ktu", B, "english_certificate", "all", "application", "KTU may organise an online test instead.",
     KTU_RECOGNITION, "a certificate of the knowledge of the English language"),
    ("ktu", B, "recognition", "all", "by_university", "Free of charge.",
     KTU_RECOGNITION, "The procedure of the recognition of foreign qualifications at the University is performed"),

    # --- VILNIUS TECH ---
    ("vilnius-tech", B, "secondary_diploma", "all", "application", "Average grade at least 60%.",
     VT_REQUIREMENTS, "A High school graduation certificate with a minimum accumulated grade point average (CGPA) of 60%."),
    ("vilnius-tech", B, "english_translation", "all", "application", "Legalised; for documents not in English.",
     VT_REQUIREMENTS, "All applications must include official, legalized English translations of academic transcripts if they are not issued in English."),
    ("vilnius-tech", B, "legalisation", "all", "application",
     "Apostille, or consular legalisation for countries outside the 1961 Hague Convention.",
     VT_REQUIREMENTS, "Certified with an Apostille – if they were issued in a country that is part of the 1961 Hague Convention"),
    ("vilnius-tech", B, "english_certificate", "all", "application", "Not needed if previous studies were fully in English.",
     VT_PROCEDURE, "English proficiency certificate"),
    ("vilnius-tech", B, "cv", "all", "application", None, VT_PROCEDURE, "Curriculum Vitae"),
    ("vilnius-tech", B, "passport", "all", "application",
     "Valid for at least two years; the admission requirements page says one year from first entry — check with the university.",
     VT_PROCEDURE, "A Copy of Passport valid for at least two years"),
    ("vilnius-tech", B, "recognition", "all", "by_university", "Done by the International Studies Centre.",
     VT_PROCEDURE, "The International Studies Centre reviews your education documents for qualification recognition purposes"),
    ("vilnius-tech", B, "proof_of_funds", "non_eu_citizens", "before_arrival",
     "A bank certificate and a notarised letter of guarantee from parents or sponsors, for the residence permit.",
     VT_PROCEDURE, "Certificate from a foreign bank and notarized letter of guarantee from parents / sponsors"),
    ("vilnius-tech", B, "criminal_record", "non_eu_citizens", "before_arrival",
     "From countries of residence in the last two years; legalised or apostilled.",
     VT_PROCEDURE, "Non conviction / Police Clearance certificate from countries of residence in last two years (needed for TRP application)"),
    ("vilnius-tech", B, "minor_documents", "under_18", "before_arrival", "A notarised letter of authorisation from parents.",
     VT_PROCEDURE, "Minor students (under age of 18) must bring notarized Letter of Authorization"),

    # --- ISM ---
    ("ism", B, "passport", "all", "application", "Or an ID card.",
     ISM_ADMISSION, "Personal info, copy of passport or ID card and photo, contact information."),
    ("ism", B, "photo", "all", "application", None,
     ISM_ADMISSION, "Personal info, copy of passport or ID card and photo, contact information."),
    ("ism", B, "transcript", "all", "application", "Grades of the last 1.5 years, or the diploma if already graduated.",
     ISM_ADMISSION, "Mark sheet from the last 1,5 years at school (or secondary school diploma if candidate has already graduated);"),
    ("ism", B, "secondary_diploma", "final_year", "application", "By 1 August.",
     ISM_ADMISSION, "Copy of Final diploma of Secondary Education submitted by the 1st of August;"),
    ("ism", B, "english_certificate", "all", "application", "If a test was taken; ISM's own test and other proofs are accepted.",
     ISM_ADMISSION, "International English Language Exam results (if test was taken);"),
    ("ism", B, "motivation_letter", "all", "application", None, ISM_ADMISSION, "Motivation letter."),
    ("ism", B, "application_fee_receipt", "all", "application", None, ISM_ADMISSION, "Application fee ("),
    ("ism", B, "recognition", "all", "by_university", "ISM may ask for more documents.",
     ISM_ADMISSION, "ISM has the right to request additional documents necessary for making a decision on academic recognition."),

    # --- LCC International University ---
    ("lcc", B, "transcript", "all", "application", "Grades for the last 3 years.",
     LCC_ADMISSIONS, "Get your high school grades for the last 3 years from your school and an international passport."),
    ("lcc", B, "passport", "all", "application", None,
     LCC_ADMISSIONS, "Get your high school grades for the last 3 years from your school and an international passport."),
    ("lcc", B, "secondary_diploma", "final_year", "application", "After graduation.",
     LCC_ADMISSIONS, "Submit your final high school diploma upon graduation"),
    ("lcc", B, "english_certificate", "all", "application", "Not older than 2 years; may be waived in some cases.",
     LCC_ADMISSIONS, "Submit an official English proficiency test certificate."),

    # --- LMTA (страница — приём 2026 года, поддомен old.) ---
    ("lmta", B, "secondary_diploma", "all", "application", "Original or notarised copy.",
     LMTA_APPLICATION, "Certificate of secondary education (original or notarised copy)"),
    ("lmta", B, "recognition", "all", "application", "A certificate from LMTA or SKVC.",
     LMTA_APPLICATION, "Recognition of your foreign education (certificate from LMTA or SKVC"),
    ("lmta", B, "passport", "all", "application", "Or an ID card.", LMTA_APPLICATION, "Copy of your passport or ID card"),
    ("lmta", B, "english_certificate", "all", "application", "At least B1.",
     LMTA_APPLICATION, "English language certificate (minimum B1 level"),

    # --- VIKO (Vilniaus kolegija) ---
    ("vk", C, "passport", "all", "application", None, VIKO_APPLY, "Copy of an identity document"),
    ("vk", C, "secondary_diploma", "all", "application", "Certificate and its supplement; scans from originals.",
     VIKO_APPLY, "Copies of qualification (education) documents"),
    ("vk", C, "legalisation", "docs_issued_outside_eu", "application",
     "Not needed for documents from the EU, EEA, USA, Russia, Belarus, Moldova or Ukraine.",
     VIKO_APPLY, "Education documents must be legalized or certified with an Apostille"),
    ("vk", C, "english_translation", "all", "application", "Into Lithuanian or English; not needed for documents in English.",
     VIKO_APPLY, "Documents issued in other languages must be accompanied by an official translation into Lithuanian or English"),
    ("vk", C, "application_fee_receipt", "all", "application", "Non-refundable.",
     VIKO_APPLY, "Copy of the payment receipt confirming the non-refundable application fee"),
    ("vk", C, "recognition", "all", "by_university", None,
     VIKO_REQUIREMENTS, "The academic assessment and recognition of your education documents will be processed by VIKO."),

    # --- Vilniaus verslo kolegija ---
    ("vvk", C, "secondary_diploma", "all", "application", "Copy, with a translation into English or Lithuanian.",
     VVK_STEPS, "Secondary education or High School Diploma and Transcripts (copy) accompanied with their translation into English or Lithuanian."),
    ("vvk", C, "transcript", "all", "application", None,
     VVK_STEPS, "Secondary education or High School Diploma and Transcripts (copy) accompanied with their translation into English or Lithuanian."),
    ("vvk", C, "english_translation", "all", "application", "Into English or Lithuanian.",
     VVK_STEPS, "Secondary education or High School Diploma and Transcripts (copy) accompanied with their translation into English or Lithuanian."),
    ("vvk", C, "passport", "all", "application", "Or an ID card.", VVK_STEPS, "A copy of your Passport or ID card."),
    ("vvk", C, "application_fee_receipt", "all", "application", "The fee also covers legalisation for the residence permit.",
     VVK_STEPS, "payment confirmation."),
    ("vvk", C, "recognition", "all", "application", "The applicant applies to SKVC for the evaluation.",
     VVK_STEPS, "Apply to the Lithuanian Centre for Quality Assessment in Higher Education for your Secondary School Diploma and transcript evaluation"),
    ("vvk", C, "proof_of_funds", "all", "before_arrival",
     "A letter of support from parents or sponsors and a bank letter, after conditional acceptance.",
     VVK_STEPS, "A Letter of Affidavit of Support from your parents/sponsors and the Certificate/Letter from a bank"),

    # --- Lietuvos verslo kolegija (LTVK) ---
    ("ltvk", C, "secondary_diploma", "all", "application", "Original and copy, with the supplement.",
     LTVK_RULES, "Secondary education diploma and supplement (original and copy)"),
    ("ltvk", C, "legalisation", "all", "application", "Apostille.",
     LTVK_RULES, "Diploma of Education in international country must be certificated by Apostille by Consulate"),
    ("ltvk", C, "english_translation", "all", "application", "Into Lithuanian or English, certified by a notary.",
     LTVK_RECOGNITION, "official translations of the education documents and their annexes into Lithuanian or English, certified by a notary"),
    ("ltvk", C, "passport", "all", "application", "Or an ID card; original and copy of the data page.",
     LTVK_RULES, "Personal Identification Card or Passport (original and copy of page with photo and personal data)"),
    ("ltvk", C, "english_certificate", "all", "application", "B2 or higher.",
     LTVK_RULES, "English language proficiency certificate (copy);"),
    ("ltvk", C, "motivation_letter", "all", "application", None, LTVK_RECOGNITION, "Motivational letter."),
    ("ltvk", C, "criminal_record", "all", "application", "If needed; apostilled.",
     LTVK_RULES, "Police criminal report (if needed) certificated by Apostille"),
    ("ltvk", C, "application_fee_receipt", "all", "application", None,
     LTVK_RULES, "confirmation of paid document Registration fee"),
    ("ltvk", C, "recognition", "all", "by_university", "Done by the college after the first-year payment.",
     LTVK_RECOGNITION, "the College carries out the academic recognition of foreign qualifications in a centralized manner"),
]

# --- Эстония (решение владельца 2026-11-19): строки выписаны 2026-11-21 со страниц
# вузов для английских программ первой ступени (бакалавр и прикладное высшее).
# Факты Эстонии показываются без подтверждения человеком, с пометкой «извлечено
# автоматически» (миграция 20261120120000). Не вошли: EEK Mainor (robots.txt
# запрещает обход агентам Anthropic), Euroakadeemia (на её домене теперь сайт о
# кредитах), TTK (английской страницы приёма нет) — их списки вручную.
UT_PROGRAMME = "https://ut.ee/en/curriculum/science-and-technology"
UT_GENERAL = "https://ut.ee/en/content/bachelors-and-masters-studies-university-tartu"
TLU_BACHELOR = "https://www.tlu.ee/en/admission-bachelors-studies"
EBS_BACHELOR = "https://www.ebs.ee/en/university/bachelors-studies/bachelors-admission-information"
TALTECH_APPLY = "https://taltech.ee/en/apply"
EAMT_DATES = "https://eamt.ee/en/admissions/admission-dates/"
EAMT_GUIDELINE = "https://eamt.ee/en/admissions/international-students-guideline/"
EAVA_CAM = "https://lennuakadeemia.ee/admissions/cam/how-to-apply"
EMKTS_FOREIGN = "https://www.emkts.ee/index.php/en/admission/foreign-student"

ROWS += [
    # --- UT (University of Tartu) ---
    ("ut", B, "secondary_diploma", "all", "application", "Certified copy, with the grade list and grading scale, in the original language.",
     UT_PROGRAMME, "official certified copy of the secondary school certificate and grade list in the original language"),
    ("ut", B, "legalisation", "all", "application", "Copies certified by the issuing school, a notary or with an apostille.",
     UT_GENERAL, "The documents can be certified 1) by an authorized official of the issuing institution, 2) by a notary, or 3) with an Apostille attached"),
    ("ut", B, "transcript", "final_year", "application", "Most recent grades for all upper secondary years; only from some countries.",
     UT_PROGRAMME, "should electronically submit their most recent grade sheet or transcript with results for all higher secondary school years"),
    ("ut", B, "enrolment_letter", "final_year", "application", "From your school: current enrolment and expected graduation date.",
     UT_PROGRAMME, "supplemented by an official statement from the issuing school indicating current enrollment and expected graduation date"),
    ("ut", B, "english_translation", "all", "application", "Certified translation of the certificate and grade list.",
     UT_PROGRAMME, "official certified translation of the secondary school certificate and grade list into English"),
    ("ut", B, "english_certificate", "all", "application", None,
     UT_PROGRAMME, "proof of English language proficiency"),
    ("ut", B, "motivation_letter", "all", "application", "In English; the programme page lists the questions.",
     UT_PROGRAMME, "Please write a brief motivation letter"),
    ("ut", B, "passport", "all", "application", None,
     UT_PROGRAMME, "copy of valid international passport page stating the applicant's personal particulars"),
    ("ut", B, "application_fee_receipt", "all", "application", "Not needed if the previous study level was completed in Estonia.",
     UT_PROGRAMME, "confirmation/receipt of application fee payment (if applicable)"),

    # --- TLU (Tallinn University) ---
    ("tlu", B, "secondary_diploma", "all", "application", None,
     TLU_BACHELOR, "Copy of Secondary Education Certificate/Diploma"),
    ("tlu", B, "transcript", "all", "application", None,
     TLU_BACHELOR, "Transcript of Records/Academic Transcript"),
    ("tlu", B, "english_translation", "all", "application", "For the diploma and transcript, if not in English.",
     TLU_BACHELOR, "an official translation is requested if the document is not in English"),
    ("tlu", B, "english_certificate", "all", "application", None,
     TLU_BACHELOR, "Proof of English language Proficiency"),
    ("tlu", B, "passport", "all", "application", None,
     TLU_BACHELOR, "Copy of the identification page of the passport"),
    ("tlu", B, "application_fee_receipt", "all", "application", "The application is reviewed after the fee arrives.",
     TLU_BACHELOR, "the application fee has been received"),
    ("tlu", B, "minor_documents", "under_18", "application",
     "After a conditional offer: notarised copies of parents' passports, birth certificate and a letter of consent or power of attorney.",
     TLU_BACHELOR, "three sets of documents will be required at a later stage of the admission process, once the applicant has received a conditional study offer"),

    # --- EBS (Estonian Business School) ---
    ("ebs", B, "secondary_diploma", "all", "application", "Proper scans.",
     EBS_BACHELOR, "Previous education documents (certificate/diploma and grade transcript)"),
    ("ebs", B, "transcript", "all", "application", "If final documents are not ready yet, the most recent transcripts in English.",
     EBS_BACHELOR, "If your final documents are not available yet, then upload your most recent academic transcripts in English"),
    ("ebs", B, "english_translation", "all", "application", "Together with the originals.",
     EBS_BACHELOR, "Provide authorised English translations of your documents if the originals are not in English"),
    ("ebs", B, "english_certificate", "all", "application", "An internationally recognised test, valid until the start of studies.",
     EBS_BACHELOR, "The language certificate must be valid until the beginning of the academic year"),
    ("ebs", B, "passport", "all", "application", None,
     EBS_BACHELOR, "Copy of passport identification pages"),
    ("ebs", B, "recommendation_letters", "all", "application", "Contacts of two referees; EBS asks them for an assessment by email.",
     EBS_BACHELOR, "contact information of two references"),

    # --- TalTech (Tallinn University of Technology) ---
    ("taltech", B + C, "secondary_diploma", "all", "application", "Final or most recent; scans, not photos.",
     TALTECH_APPLY, "education documents of the required level (final or most recent ) and official English translations"),
    ("taltech", B + C, "english_translation", "all", "application", None,
     TALTECH_APPLY, "official English translations"),
    ("taltech", B + C, "passport", "all", "application", "Valid during the application process.",
     TALTECH_APPLY, "passport identification page (document needs to be valid during the application process)"),
    ("taltech", B + C, "english_certificate", "all", "application", None,
     TALTECH_APPLY, "proof of English language proficiency"),
    ("taltech", B + C, "motivation_letter", "all", "application", "Typed into DreamApply; most programmes ask for it.",
     TALTECH_APPLY, "most study programmes require a motivation letter to be submitted when applying"),
    ("taltech", B + C, "application_fee_receipt", "all", "application", None,
     TALTECH_APPLY, "After completing the payment, upload the application fee receipt"),
    ("taltech", B + C, "recognition", "all", "by_university", "Estonian ENIC/NARIC assesses the documents; may take up to a month.",
     TALTECH_APPLY, "All education documents will be assessed by the Estonian ENIC/NARIC"),

    # --- EMTA (Estonian Academy of Music and Theatre) ---
    ("emta", B, "photo", "all", "application", "Electronic.",
     EAMT_DATES, "1 photo (electronic form)"),
    ("emta", B, "passport", "all", "application", "Or an ID card.",
     EAMT_DATES, "copy of identity card or passport"),
    ("emta", B, "secondary_diploma", "all", "application", "With the grades.",
     EAMT_DATES, "copy of document certifying completion of the previous educational level with a certificate with grades or diploma supplement"),
    ("emta", B, "english_certificate", "all", "application", None,
     EAMT_DATES, "Proof of English language Proficiency"),
    ("emta", B, "application_fee_receipt", "all", "application", "Normally paid by bank transfer.",
     EAMT_DATES, "normally needs to be paid by bank transfer"),
    ("emta", B, "criminal_record", "non_eu_citizens", "before_arrival",
     "For the residence permit; issued within six months before arrival, from age 14.",
     EAMT_GUIDELINE, "you are required to submit a criminal record certificate (or proof of no criminal record) from a foreign country"),

    # --- EAVA (Estonian Aviation Academy), страница программы CAM ---
    ("eava", C, "passport", "all", "application", "Or an ID card.",
     EAVA_CAM, "a copy of an identity document (passport or ID card)"),
    ("eava", C, "secondary_diploma", "all", "application", None,
     EAVA_CAM, "a document certifying secondary education and a transcript of results"),
    ("eava", C, "transcript", "all", "application", None,
     EAVA_CAM, "a document certifying secondary education and a transcript of results"),
    ("eava", C, "english_certificate", "all", "application", "At least B2.",
     EAVA_CAM, "document certifying English language proficiency of at least B2 level"),
    ("eava", C, "english_translation", "all", "application", "On request, for documents not in English or Estonian; certified translation.",
     EAVA_CAM, "along with an Estonian or English translation, which must be certified by the issuer of the document, a sworn translator or a notary"),
    ("eava", C, "application_fee_receipt", "all", "application", "The invoice is sent after you submit the application.",
     EAVA_CAM, "confirmation/receipt of application fee"),

    # --- EMKTS (Baltic Methodist Theological Seminary) ---
    ("emkts", C, "secondary_diploma", "all", "application", "Show the original on arrival.",
     EMKTS_FOREIGN, "A copy of the document certifying secondary education"),
    ("emkts", C, "passport", "all", "application", None,
     EMKTS_FOREIGN, "A copy of a valid identity card (passport)."),
    ("emkts", C, "recommendation_letters", "all", "application",
     "From your pastor; the seminary sends the form. Non-EU applicants also need an agreement with a church in the EU.",
     EMKTS_FOREIGN, "Recommendation from applicant pastor"),
    ("emkts", C, "application_fee_receipt", "non_eu_citizens", "application", "Only for applicants who need a residence permit.",
     EMKTS_FOREIGN, "Pay the application fee required of those needing a living permit."),
]

# --- Эстония, магистратура (решение владельца 2026-11-23: «Да, только Эстония») ---
# Английские магистратуры Эстонии; у Литвы магистратур в каталоге нет (общий приём
# LAMA BPO и AIKOS дают только первую ступень), поэтому её строки не пишутся.
# Выписаны 2026-11-23, отчёт — docs/checks/STUDENT-DOCUMENTS-EE.md.
UT_MASTER = "https://ut.ee/en/curriculum/international-law-and-human-rights"
TLU_MASTER = "https://www.tlu.ee/en/admission-masters-studies"
M = ["master"]

ROWS += [
    # --- UT: перечень одинаков на страницах магистратур (сверено на двух) ---
    ("ut", M, "bachelor_diploma", "all", "application", "Official copy with the Diploma Supplement, in the original language, with the grading scale.",
     UT_MASTER, "bachelor's diploma or its equivalent and Diploma Supplement (transcript) in the original language (must include a description of the grading scale)"),
    ("ut", M, "transcript", "final_year", "application", "Most recent official transcript, with a statement of current enrolment and expected graduation date.",
     UT_MASTER, "should electronically submit their most recent official transcript by the application deadline"),
    ("ut", M, "english_translation", "all", "application", "Certified translation of the diploma and Diploma Supplement.",
     UT_MASTER, "official translation of the bachelor’s diploma and Diploma Supplement (transcript) into English, translation certified"),
    ("ut", M, "legalisation", "all", "application", "Certified copies; admitted students post them within 3 weeks of the offer.",
     UT_MASTER, "All copies of educational documents (diplomas and Diploma Supplements/transcripts) must be officially certified"),
    ("ut", M, "english_certificate", "all", "application", None,
     UT_MASTER, "proof of English language proficiency"),
    ("ut", M, "motivation_letter", "all", "application", "In English; the programme page sets the length and questions.",
     UT_MASTER, "Please write a brief motivation letter"),
    ("ut", M, "passport", "all", "application", None,
     UT_MASTER, "copy of the passport page stating the applicant’s personal particulars"),
    ("ut", M, "application_fee_receipt", "all", "application", "Not needed if the previous study level was completed in Estonia.",
     UT_MASTER, "confirmation/receipt of application fee payment (if applicable)"),

    # --- TalTech: страница подачи общая для бакалавриата и магистратуры ---
    ("taltech", M, "bachelor_diploma", "all", "application", "Final or most recent; scans, not photos. Country-specific requirements may ask for more.",
     TALTECH_APPLY, "education documents of the required level (final or most recent ) and official English translations"),
    ("taltech", M, "english_translation", "all", "application", None,
     TALTECH_APPLY, "official English translations"),
    ("taltech", M, "passport", "all", "application", "Valid during the application process.",
     TALTECH_APPLY, "passport identification page (document needs to be valid during the application process)"),
    ("taltech", M, "english_certificate", "all", "application", None,
     TALTECH_APPLY, "proof of English language proficiency"),
    ("taltech", M, "test_score", "all", "application",
     "GRE General Test, sent by ETS directly to TalTech. Not needed with a full degree from an EU, EFTA or OECD country; e-Governance applicants may take TalTech's own test instead.",
     TALTECH_APPLY, "In order to apply for Master’s programmes, a candidate is required to present a Test-taker Score Report of the GRE General Test"),
    ("taltech", M, "motivation_letter", "all", "application", "Typed into DreamApply; most programmes ask for it.",
     TALTECH_APPLY, "most study programmes require a motivation letter to be submitted when applying"),
    ("taltech", M, "application_fee_receipt", "all", "application", "Uploaded to DreamApply; the application can be submitted only after payment.",
     TALTECH_APPLY, "upload the application fee receipt to the \"TalTech application fee\" task in the DreamApply system"),

    # --- TLU ---
    ("tlu", M, "bachelor_diploma", "all", "application", "Or a certificate of a corresponding qualification.",
     TLU_MASTER, "Copy of a Bachelor’s degree certificate or certificate of a corresponding qualification"),
    ("tlu", M, "transcript", "all", "application", None,
     TLU_MASTER, "Copy of Bachelor's degree Transcript of Records/Academic Transcript"),
    ("tlu", M, "english_translation", "all", "application", "For the diploma and transcript, if not in English.",
     TLU_MASTER, "an official translation is requested if the document is not in English"),
    ("tlu", M, "english_certificate", "all", "application", None,
     TLU_MASTER, "Proof of English language Proficiency"),
    ("tlu", M, "passport", "all", "application", "A sworn affidavit is also needed if the name differs between documents.",
     TLU_MASTER, "Copy of the identification page of the passport"),
    ("tlu", M, "application_fee_receipt", "all", "application", "The application is reviewed after the fee arrives.",
     TLU_MASTER, "the application fee has been received"),
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
