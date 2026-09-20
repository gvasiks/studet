// Проверка формулы на настоящих результатах человека (план работ, неделя 3,
// позиция 01 второй ревизии): личный опыт поступления — не источник формулы,
// но им можно ПРОВЕРИТЬ понимание. Скрипт считает балл по формуле из базы
// (включая ещё не подтверждённую — поэтому нужен сервисный ключ, только
// локально) и раскладывает по слагаемым, чтобы сравнить с тем, что вышло
// в жизни.
//
//   npm run check:formula -- rtu ibx-02c60 docs/checks/rtu-personal-check.example.json
//
// Ключ читается из pipeline/.env (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) и
// никуда не печатается. Скрипт ничего не пишет в базу.

import { readFileSync } from "node:fs";
import { createClient } from "@supabase/supabase-js";

const [universitySlug, programmeSlug, inputPath] = process.argv.slice(2);
if (!universitySlug || !programmeSlug || !inputPath) {
  console.error("Использование: npm run check:formula -- <вуз> <программа> <файл-с-результатами.json>");
  process.exit(1);
}

process.loadEnvFile("pipeline/.env");
const { SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY } = process.env;
if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error("В pipeline/.env нет SUPABASE_URL или SUPABASE_SERVICE_ROLE_KEY");
  process.exit(1);
}
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, { auth: { persistSession: false } });

// Тот же вычислитель, что и на сайте — не копия его логики.
const { calculateScore, extraKey } = await import("../src/lib/formula.ts");

const input = JSON.parse(readFileSync(inputPath, "utf-8"));

const { data: university } = await supabase.from("university").select("id, name_lv").eq("slug", universitySlug).single();
const { data: programme } = await supabase
  .from("programme")
  .select("id, name_lv, name_en")
  .eq("university_id", university.id)
  .eq("slug", programmeSlug)
  .single();

const { data: formula } = await supabase
  .from("formula")
  .select(
    "id, variant, valid_from, source_url, source_doc, source_doc_number, source_doc_date, source_copy_path, verified_at",
  )
  .eq("programme_id", programme.id)
  .is("valid_to", null)
  .order("valid_from", { ascending: false })
  .limit(1)
  .maybeSingle();

if (!formula) {
  console.error(`У программы ${programmeSlug} нет формулы в базе.`);
  process.exit(1);
}

const [{ data: terms }, { data: gates }, { data: levelRows }] = await Promise.all([
  supabase.from("formula_term").select("kind, subject, coefficient").eq("formula_id", formula.id),
  supabase.from("formula_gate").select("subject, min_percent").eq("formula_id", formula.id),
  supabase.from("level_coefficient").select("level, coefficient, valid_from").order("valid_from", { ascending: false }),
]);

const levels = {};
for (const row of levelRows) if (!(row.level in levels)) levels[row.level] = Number(row.coefficient);

const result = calculateScore(
  terms.map((t) => ({ kind: t.kind, subject: t.subject, coefficient: Number(t.coefficient) })),
  gates.map((g) => ({ subject: g.subject, minPercent: Number(g.min_percent) })),
  input.exams ?? [],
  levels,
  input.extras ?? {},
);

console.log(`\n${university.name_lv} — ${programme.name_lv ?? programme.name_en} (${programmeSlug})`);
console.log(`Формула: вариант ${formula.variant}, действует с ${formula.valid_from}`);
console.log(`Документ: ${formula.source_doc}`);
console.log(`Номер: ${formula.source_doc_number ?? "—"}, дата версии: ${formula.source_doc_date ?? "—"}`);
console.log(`Копия: ${formula.source_copy_path ?? "—"}`);
console.log(`Подтверждена человеком: ${formula.verified_at ? formula.verified_at : "НЕТ"}\n`);

console.log("Слагаемые:");
for (const line of result.lines) {
  const label = line.term.subject ? `${line.term.kind}:${line.term.subject}` : line.term.kind;
  const shown = line.input === null ? "нет данных" : `вход ${line.input.toFixed(2)}`;
  console.log(`  ${label.padEnd(28)} коэфф. ${String(line.term.coefficient).padEnd(6)} ${shown.padEnd(18)} -> ${line.points.toFixed(2)}`);
}
if (result.failedGates.length > 0) {
  console.log("\nНе пройден порог:");
  for (const gate of result.failedGates) console.log(`  ${gate.subject}: нужно не меньше ${gate.minPercent}%`);
}
console.log(`\nИтого по формуле из базы: ${result.total.toFixed(2)}`);

if (typeof input.actualScore === "number") {
  const difference = result.total - input.actualScore;
  console.log(`Балл, который вышел у вас в жизни: ${input.actualScore}`);
  console.log(`Разница: ${difference > 0 ? "+" : ""}${difference.toFixed(2)}`);
  console.log(
    Math.abs(difference) < 0.5
      ? "Совпало (в пределах округления). Формула и ваше понимание её сходятся."
      : "РАСХОЖДЕНИЕ. Причины по вероятности: правила вашего года другие (сравнивайте с документом того года, а не 2026/27); не тот уровень экзамена; ошибка в коэффициенте формулы. Запишите расхождение и покажите его мне.",
  );
}
if (input.note) console.log(`\nВаша заметка: ${input.note}`);
