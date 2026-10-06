import type { InterestKey } from "./fields";

// Литовские направления программ и категории интересов анкеты.
//
// Направление берётся из официального списка общего приёма LAMA BPO: буква
// — группа направлений (17 штук), буква с двумя цифрами — направление (102).
// В базе оно лежит в lt_programme_field. Здесь — только то, в какую из
// десяти категорий интересов анкеты попадает направление. Категории те же,
// что у Латвии (src/lib/fields.ts), и делятся по тому же смыслу: экономика —
// к бизнесу, социальная работа — к здоровью и социальной помощи, архитектура
// — к инженерии и строительству, туризм и спорт — к услугам.

// Группа целиком.
const INTEREST_BY_GROUP: Record<string, InterestKey> = {
  A: "science", // математика
  B: "it", // информатика
  C: "science", // физические науки
  D: "science", // науки о жизни
  E: "engineering", // инженерия
  F: "engineering", // технологии
  G: "health", // здоровье
  H: "science", // ветеринария
  I: "science", // сельское хозяйство
  J: "society", // социальные науки — с исключениями ниже
  K: "law", // право
  L: "business", // бизнес и публичное управление
  M: "society", // педагогика
  N: "humanities", // гуманитарные науки
  P: "arts", // искусство
  R: "services", // спорт
  S: "law", // общественная безопасность
};

// Направления, которые по смыслу относятся не к категории своей группы.
const INTEREST_BY_FIELD: Record<string, InterestKey> = {
  J01: "business", // экономика
  J04: "health", // социальная работа
  J09: "humanities", // информационные услуги
  J10: "humanities", // коммуникация
  J11: "humanities", // издательское дело
  J12: "humanities", // журналистика
  L08: "services", // туризм и отдых
  P09: "engineering", // архитектура
  P10: "engineering", // ландшафтная архитектура
};

/** Категория интересов для направления («E14» -> engineering); null — код не похож на направление. */
export function ltInterestOf(fieldCode: string): InterestKey | null {
  if (!/^[A-Z][0-9]{2}$/.test(fieldCode)) return null;
  return INTEREST_BY_FIELD[fieldCode] ?? INTEREST_BY_GROUP[fieldCode[0]] ?? null;
}

// Сколько направлений бывает в одной группе — с запасом (сейчас самое
// большое число — E14, N15).
const MAX_FIELDS_IN_GROUP = 30;

/**
 * Все коды направлений, входящие в выбранные категории, — для фильтра
 * `field_code in (...)`. Коды перечисляются по правилу, а не по списку из
 * базы: так новое направление в существующей группе попадает в фильтр само.
 */
export function ltFieldCodesForInterests(keys: InterestKey[]): string[] {
  const wanted = new Set<InterestKey>(keys);
  const codes: string[] = [];
  for (const group of Object.keys(INTEREST_BY_GROUP)) {
    for (let number = 1; number <= MAX_FIELDS_IN_GROUP; number += 1) {
      const code = `${group}${String(number).padStart(2, "0")}`;
      const interest = ltInterestOf(code);
      if (interest && wanted.has(interest)) codes.push(code);
    }
  }
  return codes;
}
