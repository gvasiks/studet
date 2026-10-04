// Разбор числа, которое человек ввёл в поле результата экзамена
// (калькулятор и «Kur varu iestāties»). Без импортов — модуль читается и
// тестами (vitest не понимает алиас "@/").
//
// Зачем отдельная функция. Раньше поле было <input type="number">, а
// значение превращалось в число через Number(): 101 и −5 считались как
// есть (итог выходил за шкалу вуза), а «72,5» в браузере с английской
// локалью теряло запятую и становилось 725. Теперь поле текстовое, и
// разбор один на оба экрана: запятая и точка равноправны, всё остальное —
// ошибка, которую видно под полем (аудит 2026-10-04, пункт 2).

export type ParsedNumber =
  | { state: "empty" }
  | { state: "ok"; value: number }
  | { state: "invalid" };

// Только цифры и один десятичный разделитель. Минус, «1e2», пробел внутри,
// буквы — не число, которое можно получить на экзамене.
const NUMBER_PATTERN = /^\d+(?:[.,]\d+)?$/;

/** Неотрицательное число: для слагаемых без единой шкалы (вступительное испытание, аттестат). */
export function parseNonNegative(raw: string): ParsedNumber {
  const text = raw.trim();
  if (text === "") return { state: "empty" };
  if (!NUMBER_PATTERN.test(text)) return { state: "invalid" };
  return { state: "ok", value: Number(text.replace(",", ".")) };
}

/** Результат централизованного экзамена: от 0 до 100 процентов. */
export function parsePercent(raw: string): ParsedNumber {
  const parsed = parseNonNegative(raw);
  if (parsed.state === "ok" && parsed.value > 100) return { state: "invalid" };
  return parsed;
}
