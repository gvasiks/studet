import type { InterestKey } from "./fields";

// Эстонские направления программ и категории интересов анкеты.
//
// Направление берётся с государственного портала haridusportaal.edu.ee: у
// программы стоят область (õppevaldkond), направление (õppesuund) и группа
// программ (õppekavarühm) по классификатору ISCED-F. В базе оно лежит в
// ee_programme_field; ключ — номер направления в справочнике портала
// (числовых кодов ISCED-F портал не отдаёт). Здесь — только то, в какую из
// десяти категорий интересов попадает направление. Категории те же, что у
// Латвии и Литвы (src/lib/fields.ts, src/lib/lt-fields.ts), и делятся по тому
// же смыслу: транспорт — к инженерии, окружающая среда — к естественным
// наукам, безопасность — к праву, педагогика — к социальным наукам.

// Все 34 направления, которые были в данных портала 2026-10-11.
const INTEREST_BY_FIELD: Record<string, InterestKey> = {
  "2388": "society", // Haridus — педагогика
  "2399": "society", // Hariduse interdistsiplinaarne õppesuund
  "2416": "humanities", // Humanitaaria
  "2432": "humanities", // Humanitaaria ja kunsti interdistsiplinaarne õppesuund
  "2425": "humanities", // Keeled — языки
  "2403": "arts", // Kunstid — искусство
  "2526": "it", // Informatsiooni- ja kommunikatsioonitehnoloogiad
  "2535": "it", // …interdistsiplinaarne õppesuund
  "2491": "science", // Bioloogia ja sellega seotud teadused
  "2505": "science", // Füüsikalised loodusteadused
  "2498": "science", // Keskkond — окружающая среда
  "2522": "science", // Loodusteadused, matemaatika ja statistika, mujal liigitamata
  "2514": "science", // Matemaatika ja statistika
  "2577": "science", // Põllumajandus — сельское хозяйство
  "2584": "science", // Metsandus — лесное хозяйство
  "2587": "science", // Kalandus — рыболовство
  "2590": "science", // Veterinaaria
  "2593": "science", // Põllumajanduse… interdistsiplinaarne õppesuund
  "2450": "humanities", // Ajakirjandus ja teave — журналистика и информация
  "2439": "society", // Sotsiaal- ja käitumisteadused — с исключением ниже
  "2457": "society", // Sotsiaalteaduste… interdistsiplinaarne õppesuund
  "2633": "services", // Isikuteenindus — туризм, спорт, гостиницы
  "2660": "engineering", // Transporditeenused
  "2653": "law", // Turvateenused — безопасность и оборона
  "2565": "engineering", // Arhitektuur ja ehitus
  "2570": "engineering", // Tehnika, tootmise ja ehituse interdistsiplinaarne õppesuund
  "2539": "engineering", // Tehnikaalad
  "2554": "engineering", // Tootmine ja töötlemine
  "2617": "health", // Heaolu — социальная работа и помощь
  "2600": "health", // Tervis — здоровье
  "2629": "health", // Tervis ja heaolu, mujal liigitamata
  "2464": "business", // Ärindus ja haldus
  "2484": "business", // Ärinduse, halduse ja õiguse interdistsiplinaarne õppesuund
  "2481": "law", // Õigus — право
};

// Группы программ, которые по смыслу относятся не к категории своего
// направления. Экономика стоит в классификаторе среди социальных наук, а у
// Латвии и Литвы она в «бизнесе» — здесь так же, чтобы в общем списке трёх
// стран интерес находил её везде.
const INTEREST_BY_GROUP: Record<string, InterestKey> = {
  Majandusteadus: "business",
};

/** Коды направлений, для которых есть категория, — для теста. */
export const EE_FIELD_CODES = Object.keys(INTEREST_BY_FIELD);

/**
 * Категория интересов эстонской программы. fieldCode — номер направления
 * («2464»), detailedName — группа программ («Majandusteadus») или null.
 * null — направление незнакомое (появилось на портале после 2026-10-11).
 */
export function eeInterestOf(fieldCode: string, detailedName: string | null): InterestKey | null {
  if (detailedName !== null && detailedName in INTEREST_BY_GROUP) return INTEREST_BY_GROUP[detailedName];
  return INTEREST_BY_FIELD[fieldCode] ?? null;
}
