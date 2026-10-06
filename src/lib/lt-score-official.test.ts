import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { ltScore, type LtExams, type LtFormula } from "./lt-score";

// Сверка с официальным калькулятором LAMA BPO. Литовские формулы не
// подтверждает человек; взамен наш расчёт обязан совпасть с официальным не
// меньше чем на 30 наборах оценок (docs/PLAN-LITHUANIA-2027.md, раздел 4).
//
// Случаи готовит pipeline/src/lt_check_calculator.py, ответы официального
// калькулятора вписывает человек (поле official): сервис расчёта запрещает
// автоматических клиентов. Пока ответ не вписан, случай не проверяется —
// поэтому отдельный тест ниже следит, сколько случаев действительно сверено.

type Case = {
  id: number;
  note: string;
  formula_number: string;
  formula: LtFormula;
  program_name: string;
  exams: LtExams;
  official: number | null;
};

const file = path.join(__dirname, "..", "..", "docs", "checks", "lt-calculator-cases-2026.json");
const data = JSON.parse(readFileSync(file, "utf-8")) as { admission_year: number; cases: Case[] };
const checked = data.cases.filter((item) => item.official !== null);

/** Сколько случаев должно совпасть, чтобы расчёт можно было показывать. */
const REQUIRED_CASES = 30;

describe("литовский балл — сверка с официальным калькулятором", () => {
  it("случаев подготовлено не меньше, чем требует план", () => {
    expect(data.cases.length).toBeGreaterThanOrEqual(REQUIRED_CASES);
    expect(new Set(data.cases.map((item) => item.id)).size).toBe(data.cases.length);
  });

  it("каждый случай считается нашим вычислителем без ошибок", () => {
    for (const item of data.cases) {
      const score = ltScore(item.formula, item.exams);
      expect(score.total, `случай ${item.id}`).toBeGreaterThanOrEqual(0);
      expect(score.total, `случай ${item.id}`).toBeLessThanOrEqual(10);
    }
  });

  // Сверенных случаев может не быть вовсе — тогда этот блок пуст, а не красный:
  // отсутствие сверки не ошибка расчёта. Показ расчёта посетителю закрыт
  // отдельно — отметкой checked_at в базе.
  for (const item of checked) {
    it(`случай ${item.id}: формула ${item.formula_number}, ${item.note} — как у официального калькулятора`, () => {
      expect(ltScore(item.formula, item.exams).total).toBe(item.official);
    });
  }

  it(`сверено случаев: ${checked.length} из ${data.cases.length}`, () => {
    // Число в названии теста — чтобы состояние сверки было видно в отчёте о
    // тестах. Тест не падает, пока сверка не закончена.
    expect(checked.length).toBeLessThanOrEqual(data.cases.length);
  });
});
