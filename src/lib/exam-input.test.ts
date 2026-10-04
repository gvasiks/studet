import { describe, expect, it } from "vitest";
import { parseNonNegative, parsePercent } from "./exam-input";

describe("parsePercent", () => {
  it("пустое поле — не ошибка и не ноль", () => {
    expect(parsePercent("")).toEqual({ state: "empty" });
    expect(parsePercent("   ")).toEqual({ state: "empty" });
  });

  it("целые и дробные, запятая и точка равноправны", () => {
    expect(parsePercent("72")).toEqual({ state: "ok", value: 72 });
    expect(parsePercent("72,5")).toEqual({ state: "ok", value: 72.5 });
    expect(parsePercent("72.5")).toEqual({ state: "ok", value: 72.5 });
    expect(parsePercent(" 64 ")).toEqual({ state: "ok", value: 64 });
  });

  it("границы шкалы входят", () => {
    expect(parsePercent("0")).toEqual({ state: "ok", value: 0 });
    expect(parsePercent("100")).toEqual({ state: "ok", value: 100 });
  });

  it("вне шкалы 0–100 — ошибка, а не число", () => {
    expect(parsePercent("101")).toEqual({ state: "invalid" });
    expect(parsePercent("100,01")).toEqual({ state: "invalid" });
    expect(parsePercent("725")).toEqual({ state: "invalid" });
    expect(parsePercent("-5")).toEqual({ state: "invalid" });
  });

  it("не число — ошибка", () => {
    for (const raw of ["abc", "7a", "1e2", "7 2", "72,", ",5", "72,5,1", "+72", "72%"]) {
      expect(parsePercent(raw), raw).toEqual({ state: "invalid" });
    }
  });
});

describe("parseNonNegative", () => {
  it("без верхней границы: у вступительных испытаний шкалы разные", () => {
    expect(parseNonNegative("850")).toEqual({ state: "ok", value: 850 });
    expect(parseNonNegative("7,25")).toEqual({ state: "ok", value: 7.25 });
  });

  it("отрицательное и нечисловое — ошибка", () => {
    expect(parseNonNegative("-1")).toEqual({ state: "invalid" });
    expect(parseNonNegative("x")).toEqual({ state: "invalid" });
    expect(parseNonNegative("")).toEqual({ state: "empty" });
  });
});
