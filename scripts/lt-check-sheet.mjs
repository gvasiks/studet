// Лист для ручной сверки литовского балла с официальным калькулятором.
//
// Читает docs/checks/lt-calculator-cases-<год>.json (его готовит
// pipeline/src/lt_check_calculator.py), считает наш балл тем же
// вычислителем, что и сайт (src/lib/lt-score.ts), и пишет
// docs/checks/LT-CALCULATOR-CHECK-SHEET.md: что ввести на странице
// официального калькулятора и какое число мы ожидаем.
//
// Сервису расчёта LAMA BPO ничего не отправляется: его robots.txt
// запрещает автоматических клиентов, поэтому сверку делает человек.
//
// Запуск: node scripts/lt-check-sheet.mjs
// Нужен Node 23.6 или новее: скрипт импортирует .ts напрямую.

import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { ltScore } from "../src/lib/lt-score.ts";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const YEAR = 2026;
const CASES_FILE = path.join(ROOT, "docs", "checks", `lt-calculator-cases-${YEAR}.json`);
const SHEET_FILE = path.join(ROOT, "docs", "checks", "LT-CALCULATOR-CHECK-SHEET.md");

const data = JSON.parse(readFileSync(CASES_FILE, "utf-8"));
const comma = (value) => value.toFixed(2).replace(".", ",");

// Уровень на странице калькулятора: у литовского и математики — VA
// (расширенный курс) или VB (общий), у остальных — V.
function level(subject, exam) {
  if (subject === "lithuanian" || subject === "mathematics") return exam.course === "B" ? "VB" : "VA";
  return "V";
}

const rows = data.cases.map((item) => {
  const score = ltScore(item.formula, item.exams);
  const inputs = Object.entries(item.exams)
    .map(([subject, exam]) => `${exam.page_name} — ${level(subject, exam)} **${exam.score}**`)
    .join("<br>");
  const official = item.official === null ? "" : comma(item.official);
  const verdict = item.official === null ? "" : item.official === score.total ? "совпало" : "**РАСХОЖДЕНИЕ**";
  return (
    `| ${item.id} | ${item.institution_name}<br>**${item.program_name}**<br>${item.program_city}, ${item.program_form} ` +
    `| ${inputs} | ${item.note} | **${comma(score.total)}** | ${official} | ${verdict} |`
  );
});

const filled = data.cases.filter((item) => item.official !== null).length;
const sheet = `# Литва: лист сверки с официальным калькулятором (${YEAR})

Этот файл собирается скриптом \`scripts/lt-check-sheet.mjs\` — руками не править.
Ответы вписываются в \`docs/checks/lt-calculator-cases-${YEAR}.json\`, поле \`official\`.

Вписано ответов: **${filled} из ${data.cases.length}**.

## Зачем это нужно

Литовские формулы не подтверждает человек. Взамен наш расчёт обязан совпасть
с официальным калькулятором LAMA BPO не меньше чем на 30 наборах оценок —
иначе он не выпускается (\`docs/PLAN-LITHUANIA-2027.md\`, раздел 4).

Автоматически отправить эти случаи нельзя: сервис расчёта запрещает
автоматических клиентов в своём \`robots.txt\`. Поэтому их вводит человек —
на той же странице, которой пользуются абитуриенты.

## Как вводить

1. Откройте <${data.calculator_page}>.
2. Год окончания школы — **${YEAR}**. Где учились — **Bendrojo ugdymo mokykloje**.
3. Выберите вуз и программу из строки таблицы. Если программ с таким
   названием несколько — ту, у которой совпадают город и форма.
4. Для каждого предмета из столбца «Что ввести» выберите вид оценки —
   государственный экзамен указанного уровня (**VA**, **VB** или **V**) — и
   впишите число. Остальные предметы оставьте пустыми.
5. Дополнительные достижения (олимпиады, служба и прочее) не отмечайте.
6. Нажмите расчёт и сравните итоговый балл с числом в столбце «Наш балл».

Оценки выдуманы; персональных данных на странице вводить не нужно.

## Что записать

Проще всего — написать в чат номера случаев, где число **не совпало**, и
что показал официальный калькулятор (например: «5 — 7,06; 16 — 7,22;
остальные совпали»). Если калькулятор не дал ввести оценку или показал
предупреждение — это тоже результат, запишите его словами.

Первые семь случаев и случаи 9, 14–17, 25, 27–28 проверяют допущения,
в которых я не уверен (общий курс, нижняя граница оценок, два иностранных
языка, пропущенный предмет, среднее двух предметов). Если времени мало —
начните с них.

## Случаи

| № | Вуз и программа | Что ввести | Что проверяет | Наш балл | Официальный | Итог |
|---|---|---|---|---|---|---|
${rows.join("\n")}
`;

writeFileSync(SHEET_FILE, sheet, "utf-8");
console.log(`лист записан: ${path.relative(ROOT, SHEET_FILE)} (случаев ${data.cases.length}, ответов вписано ${filled})`);
