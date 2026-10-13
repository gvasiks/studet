import { describe, expect, it } from "vitest";
import { admissionState, tallinnDate } from "./ee-admission";

describe("последний конкурс эстонской программы", () => {
  const now = new Date("2026-10-13T10:00:00Z");

  it("срок не прошёл — конкурс действующий, в том числе если подача ещё не началась", () => {
    expect(admissionState({ closesAt: "2026-10-18T20:59:00+00:00" }, now)).toBe("current");
    expect(admissionState({ closesAt: "2027-07-01T20:59:00+00:00" }, now)).toBe("current");
    // последняя минута подачи — ещё действующий
    expect(admissionState({ closesAt: "2026-10-13T10:00:00+00:00" }, now)).toBe("current");
  });

  it("срок прошёл — это прошлый приём, а не открытый конкурс", () => {
    expect(admissionState({ closesAt: "2026-07-05T20:59:00+00:00" }, now)).toBe("past");
    expect(admissionState({ closesAt: "2026-10-13T09:59:59+00:00" }, now)).toBe("past");
  });

  it("конца подачи нет — сказать «открыт» нельзя", () => {
    expect(admissionState({ closesAt: null }, now)).toBe("undated");
  });

  it("даты показываются по эстонским часам, а не по часам сервера", () => {
    // подача открывается 5 октября в 00:00 по Таллину — это 21:00 четвёртого по UTC
    expect(tallinnDate("2026-10-04T21:00:00+00:00", "en-GB")).toBe("05/10/2026");
    // и закрывается 18 октября в 23:59
    expect(tallinnDate("2026-10-18T20:59:00+00:00", "en-GB")).toBe("18/10/2026");
    // зимой разница с UTC — два часа
    expect(tallinnDate("2027-01-11T21:59:00+00:00", "en-GB")).toBe("11/01/2027");
  });
});
