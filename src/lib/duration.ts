// Срок обучения для показа: «1 gads», «4 gadi», «4,5 gadi», «1 year».
//
// Раньше к числу всегда приставлялось множественное число («1 gadi») и
// дробь писалась с точкой («4.5 gadi») — аудит 2026-10-04.
//
// Единственное число — только у целых чисел: в латышском у тех, что
// кончаются на 1, кроме 11 (1, 21, 31 gads); в остальных языках — у единицы.
// Литовское сокращение «m.» не склоняется — у него обе формы одинаковые.
// Дробь — с десятичным знаком языка и не длиннее одного знака: у части
// программ срок записан как 2,0833 (два года и месяц).
export function durationLabel(years: number, language: string, units: { one: string; many: string }): string {
  const number = years.toLocaleString(language, { maximumFractionDigits: 1 });
  const whole = Number.isInteger(years);
  const singular = whole && (language === "lv" ? years % 10 === 1 && years % 100 !== 11 : years === 1);
  return `${number} ${singular ? units.one : units.many}`;
}
