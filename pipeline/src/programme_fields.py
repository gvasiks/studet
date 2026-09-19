"""Черновая разметка программ по направлениям (ревью 2026-09, пункты 14
и 16) — правила по названию программы. Это ПРЕДЛОЖЕНИЕ, не факт:
подтверждает человек (programme_field.verified_at), пока не подтверждено
— направление годится только как подсказка для фильтра по интересам в
анкете, но не как основание показывать статистику доходов.

Правило возвращает УПОРЯДОЧЕННЫЙ список кандидатов — коды групп
программ из классификатора образования, по которому ИЗМ публикует
мониторинг выпускников (3 цифры, первые две — тематическая область).
Расшифровку части латвийских расширений (например 484 или 227) в
открытых данных найти не удалось, поэтому выбор между кандидатами
делается по данным: берётся первый код, который реально встречается у
этого вуза на уровне этой программы (см. choose_field), а если ни
одного нет — первый из списка, и в отчёте это видно.

Запасные кандидаты допустимы только между РАВНОЗНАЧНЫМИ кодами (481/
483/484 — всё про ИТ), но не между разными профессиями: первая версия
правил отправила стоматологию ЛУ в 721 (медицина), а бизнес-психологию
RISEBA — в 311 (экономика), потому что "первый код с данными" молча
подставлял чужую статистику. Лучше "нет данных", чем чужие зарплаты.
"""

from __future__ import annotations

import re

from graduate_outcomes import LEVEL_CODES_BY_DEGREE, OutcomeRow

# Порядок важен: срабатывает ПЕРВОЕ подходящее правило, поэтому
# специфичные случаи (например "Medicīnas inženierija") стоят раньше
# общих ("medicīna"). Регулярки применяются к строке
# "name_en | name_lv" в нижнем регистре.
RULES: list[tuple[str, list[str]]] = [
    # --- право
    (r"pre-trial|pirmstiesas", ["380"]),
    (r"\blaw\b|tiesīb|tiesību", ["380"]),
    # --- здоровье
    (r"medicīnas inženierija|medical engineering", ["529", "522", "525"]),
    (r"biomedic", ["421", "420"]),
    (r"dental hygien|zobu higiēn", ["724"]),
    (r"health care|healthcare", ["720", "721"]),
    (r"public health|sabiedrības veselīb", ["722"]),
    (r"physician assistant|ārsta palīg", ["722"]),
    (r"nutrition|uztur", ["722"]),
    (r"orthotics|prosthetics|ortoz|protēz", ["726", "725"]),
    (r"occupational therapy|physiotherap|rehabilitation|massage|ergoterap|fizioterap|rehabilitācij|masāž", ["726"]),
    (r"physical activity", ["813"]),
    (r"dentist|zobārst", ["724"]),
    (r"nursing|māszin|midwif|vecmāt", ["723"]),
    (r"radiograph", ["725"]),
    (r"optometr", ["726"]),
    (r"pharmac|farmāc", ["727"]),
    (r"logopēd|speech therap", ["726"]),
    (r"\bmedicine\b|medicīna\b", ["721"]),
    (r"social work|sociālais darbs|sociālais rehabilit|sociālā rehabilit", ["762"]),
    (r"occupational health|darba aizsardzīb", ["862"]),
    # lookbehind: иначе "transporta" срабатывает как "sporta"
    (r"(?<![a-zāčēģīķļņšūž])sport", ["813"]),
    (r"cosmetolog|kosmetolog", ["815"]),
    # --- образование
    (r"speciālā izglītība|special education", ["141", "142"]),
    (r"izglītības zinātn|education science", ["142", "141"]),
    (r"teacher|skolotāj|pedagog|pirmsskolas", ["141"]),
    # --- туризм
    (r"tourism|tūrism|hospitality|hotel|viesnīc", ["812", "811"]),
    # --- архитектура, строительство
    (r"architect|arhitekt", ["581"]),
    (r"geoinformat", ["443"]),
    (r"geomatic|ģeomātik", ["582", "443"]),
    (r"real estate|nekustam", ["345", "582"]),
    (r"mašīnu un aparātu", ["521"]),
    (r"būvniecīb|construction|building|būvuzņēm|transportbūv|siltuma, gāzes|heating|ēku", ["582"]),
    # --- искусство и дизайн
    (r"audiovisual|film|audiovizuāl|new media|jauno mediju", ["213", "214"]),
    (r"radošās industrijas|creative industries", ["345", "214"]),
    (r"industrial design|industriālais dizains", ["214"]),
    (r"dizaina inženierija", ["521"]),
    (r"materiālu tehnoloģija un dizains|dizaina tehnoloģijas", ["542", "214"]),
    (r"interior|brand design|game design|computer game|digital visualization|dizain|\bdesign\b", ["214"]),
    (r"music|mūzik", ["212"]),
    (r"^art\b|\bart \|| māksla\b", ["211"]),
    # --- гуманитарные
    (r"theolog|teoloģ|religio", ["221"]),
    (r"philosoph|filozof", ["226", "225"]),
    (r"history|vēstur|archeolog|archaeolog", ["224", "225"]),
    (r"latvian studies|latvistik", ["223"]),
    (r"cultural and environmental heritage|kultūras un vides mantojum", ["227", "224"]),
    (r"culture management|kultūras vadīb|cultural project|kultūras projekt", ["345", "214"]),
    (r"digital humanities|digitālās humanitārās", ["222", "227"]),
    (r"digitālā kultūra", ["222", "321"]),
    (r"valodas, saziņa|language and culture|eastern european", ["227", "222", "345"]),
    (r"translat|tulkoš|terminolog|philolog|filolog|linguist|european languages|eiropas valodu|language", ["222"]),
    (r"anthropolog|asian|āzijas|cultural studies|kultūrvide", ["227", "314"]),
    # --- социальные науки
    (r"psycholog|psiholog", ["313"]),
    (r"sociolog|socioloģ", ["314"]),
    (r"political|politolog", ["312"]),
    (r"international relations|starptautisk\w* attiecīb", ["310", "312"]),
    (r"social sciences|sociālās zinātnes", ["310"]),
    (r"international economics and commercial diplomacy", ["311", "310"]),
    (r"international finance and economics", ["343", "311"]),
    (r"european business studies", ["345", "311"]),
    (r"business economics|european economics|economics and business|ekonomika un uzņēmējdarb|digital economy|circular economy", ["311", "345"]),
    # --- математика, физика, химия, биология, среда
    (r"inženiermatemāt", ["460"]),
    (r"mathematic|statistic|matemāt", ["460"]),
    (r"particle physics|daļiņu fizika|physics|fizika", ["441", "440"]),
    (r"ķīmija un ķīmijas tehnoloģija|ķīmijas tehnoloģ|chemistry, materials|ķīmija, materiālzinātne", ["524", "442"]),
    (r"biotechnolog|biotehnolo[gģ]|bioengineering|bioinženier", ["524", "421", "529"]),
    (r"chemistry|ķīmij", ["442"]),
    (r"biolog|bioloģ", ["421"]),
    (r"vides inženierija|environmental engineering", ["850", "529", "521"]),
    (r"environmental science|vides zinātn", ["850", "440"]),
    (r"geograph|ģeogrāf|geolog|ģeolog", ["443", "440"]),
    # --- финансы, учёт, маркетинг, коммуникации
    (r"financial engineering|finanšu inženier", ["343"]),
    (r"finanšu pārvaldības informācijas", ["343"]),
    (r"accounting and finance|grāmatvedīb", ["344", "343"]),
    (r"financial management|finance|finanš|banking|banku", ["343"]),
    (r"accounting|audit", ["344"]),
    (r"public relations|sabiedriskās attiecības|komunikācija un sabiedr", ["321", "342"]),
    (r"marketing|advertising|reklām", ["342"]),
    (r"library|information management|informācijas pārvald", ["322"]),
    # --- ИТ (до общего "управление" — иначе "IT project management" уйдёт в 345)
    (r"programmēšanas speciālists|programmer|programmēšana\b|programming", ["484", "481", "483"]),
    (r"programmēšanas inženieris", ["484", "481", "483"]),
    (r"artificial intelligence|intelektuālas robotizētas|intelligent robotic|e-studiju|e-learning|virtuālā realitāte|virtual reality|realitāt|gaming|spēļoš", ["481", "483", "523"]),
    (r"cyber|kiberdrošīb", ["481", "483"]),
    (r"computer engineering|smart electronic|viedās elektronisk|electronic|elektronik|telecommunication|telekomunik|adaptron|robot|mechatronic|mehatronik|telematic|telemātik", ["523", "522", "481"]),
    (r"computer science|datorzinātn|information technolog|informācijas tehnolo[gģ]|informātik|informatics|software|datorsistēm|computer systems|data analytics|viedās datortehnolo[gģ]|savstarpēji saistītu sistēmu|information systems|informācijas sistēm|it project|biznesa informātika|sociotehnisk", ["481", "483", "484"]),
    # --- энергетика, материалы, машиностроение
    (r"electric|elektroenerģ|elektrotehnolo[gģ]|energy|enerģ", ["522"]),
    (r"materiālzinātne un nanotehnolo[gģ]|nanotechn|materials science", ["524", "442", "543"]),
    (r"šķiedru|fibre|fiber|textile", ["542", "543"]),
    (r"materiālu inženierija|materials engineering", ["543", "524"]),
    (r"industrial engineering and management|industriālā inženierija un vadība", ["526", "521", "345"]),
    (r"laser|lāzer", ["521", "442"]),
    (r"ražošanas tehnoloģija|manufacturing", ["521", "526"]),
    (r"biosystems|biosistēm", ["621", "521"]),
    (r"food|pārtik", ["541"]),
    (r"aviation|aviācij|aeronaut|aerokosm|aerospace|autotransport|motor vehicle", ["525", "840"]),
    (r"machine|mašīn|mechanic|mehānika|inženiertehnika|machinery", ["521"]),
    # --- логистика и транспорт
    (r"transport and (business )?logistics|intelligent transport|telematics and logistics", ["840"]),
    (r"business logistics|uzņēmējdarbības loģistik|piegādes ķēd|supply chain", ["345", "840"]),
    (r"international trade|tirdzniec", ["341", "345", "840"]),
    (r"loģistik|logistic", ["345", "840"]),
    (r"transport", ["840"]),
    # --- безопасность
    (r"security|drošīb|border|robež|fire|ugunsdrošīb|civil protection|civilā aizsardzīb|crisis|krīz|risks", ["861", "862", "345"]),
    # --- журналистика и коммуникации (после PR и ИТ)
    (r"journalism|žurnālist|media|mediju|communicat|komunikācij|saziņ", ["321"]),
    # --- экономика
    (r"biznesa vides", ["345"]),
    # --- управление (самое общее — последним)
    (r"management|vadīb|vadīšana|vadība|administration|business|uzņēmējdarb|entrepreneur|līderīb|leadership|innovation|inovācij|quality|kvalitāt|vadībzinātn|strategic|customs|muit|regional|reģionāl|urban|pilsētu|human resource|personāl|sabiedrības pārvald", ["345"]),
    (r"economics|ekonomika|ekonomik", ["311"]),
]

_COMPILED = [(re.compile(pattern), candidates) for pattern, candidates in RULES]


def candidates_for(name_en: str | None, name_lv: str | None) -> list[str]:
    text = f"{(name_en or '').lower()} | {(name_lv or '').lower()}"
    for pattern, candidates in _COMPILED:
        if pattern.search(text):
            return candidates
    return []


def groups_with_data(outcomes: list[OutcomeRow]) -> set[tuple[str, str, str]]:
    return {(row.university_slug, row.level_code, row.programme_group) for row in outcomes}


def choose_field(
    university_slug: str,
    degree_level: str,
    candidates: list[str],
    data: set[tuple[str, str, str]],
) -> tuple[str, bool]:
    """(код, подтверждён_ли_данными). Первый кандидат, у которого есть
    строки в данных для этого вуза на уровне этой программы; если таких
    нет — первый кандидат и False (в отчёте помечается как "нет данных":
    либо у программы мало выпускников и издатель скрыл ячейку, либо
    правило промахнулось)."""
    levels = LEVEL_CODES_BY_DEGREE.get(degree_level, [])
    for code in candidates:
        if any((university_slug, level, code) in data for level in levels):
            return code, True
    return candidates[0], False
