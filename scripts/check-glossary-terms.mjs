// План 2026-09-21, пункт 13: грубая, но безопасная защита от разъезда
// перевода — запрещённые альтернативные формулировки закреплённых
// терминов (docs/TRANSLATION-GLOSSARY.md, раздел 7 и чёрный список внизу
// файла). Решение владельца 2026-09-24: проверка автоматическая, но
// список запрещённого — короткий и явный, а не попытка угадать любую
// новую формулировку того же понятия.
//
// Проверяются только СТРОКОВЫЕ ЗНАЧЕНИЯ словарей, не ключи JSON —
// `"catalog": {...}` как имя ключа не пользовательский текст и не в счёт;
// иначе проверка ловила бы сама себя на структуре словаря.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const DICT_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "src", "i18n", "dictionaries");
const DICT_FILES = ["en.json", "lv.json"];

// [регулярное выражение, что писать вместо этого — см. docs/TRANSLATION-GLOSSARY.md]
const BANNED = [
  [/\bcatalogs?\b(?!ue)/i, "catalogue"], // \bcatalog\b (без s?) пропускал множественное число "catalogs" — \b не даёт границы между "g" и "s"
  [/\bcompetitive score\b/i, "competition score"],
  [/\branking calculator\b/i, "competition score calculator"],
];

function collectStrings(value, out) {
  if (typeof value === "string") {
    out.push(value);
  } else if (Array.isArray(value)) {
    for (const item of value) collectStrings(item, out);
  } else if (value && typeof value === "object") {
    for (const v of Object.values(value)) collectStrings(v, out);
  }
  return out;
}

let failed = false;
for (const file of DICT_FILES) {
  const dict = JSON.parse(readFileSync(path.join(DICT_DIR, file), "utf-8"));
  const strings = collectStrings(dict, []);
  for (const text of strings) {
    for (const [pattern, suggestion] of BANNED) {
      if (pattern.test(text)) {
        console.error(
          `${file}: «${text}» — запрещённая формулировка (см. docs/TRANSLATION-GLOSSARY.md, раздел 7); используйте «${suggestion}»`,
        );
        failed = true;
      }
    }
  }
}

if (failed) {
  process.exit(1);
} else {
  console.log(`check-glossary-terms: чисто (${DICT_FILES.join(", ")})`);
}
