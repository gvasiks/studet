import { describe, expect, it } from "vitest";
import {
  admissionState,
  openDeadline,
  parseFunding,
  plainDate,
  studyFormKey,
  studyForms,
  tallinnDate,
} from "./ee-admission";

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

describe("условия конкурса со страницы SAIS", () => {
  it("дата без времени показывается тем же днём", () => {
    expect(plainDate("2026-09-01", "en-GB")).toBe("01/09/2026");
    expect(plainDate("2027-02-08", "en-GB")).toBe("08/02/2027");
  });

  it("знакомая форма обучения получает ключ перевода, незнакомая — нет", () => {
    expect(studyFormKey("päevane õpe")).toBe("daytime");
    expect(studyFormKey("sessioonõpe")).toBe("session");
    expect(studyFormKey("kaugõpe")).toBeNull();
    expect(studyFormKey(null)).toBeNull();
    // две формы у одного конкурса — каждая переводится отдельно
    expect(studyForms("päevane õpe, sessioonõpe")).toEqual(["päevane õpe", "sessioonõpe"]);
    expect(studyForms("sessioonõpe")).toEqual(["sessioonõpe"]);
    expect(studyForms(null)).toEqual([]);
  });

  it("финансирование: варианты нагрузки и цены как в базе", () => {
    const funding = parseFunding([
      { load: "full", paid: false, prices: [] },
      {
        load: "part",
        paid: true,
        prices: [{ amount: 1050, currency: "EUR", period: "semester", period_text: "semester", target: null }],
      },
      {
        load: "unspecified",
        paid: true,
        prices: [{ amount: 40, currency: "EUR", period: "credit", period_text: "1 EAP", target: "Kõik" }],
      },
    ]);
    expect(funding).toEqual([
      { load: "full", paid: false, prices: [] },
      { load: "part", paid: true, prices: [{ amount: 1050, currency: "EUR", period: "semester", periodText: "semester", target: null }] },
      { load: "unspecified", paid: true, prices: [{ amount: 40, currency: "EUR", period: "credit", periodText: "1 EAP", target: "Kõik" }] },
    ]);
  });

  it("непонятная запись отбрасывается, а не показывается", () => {
    expect(parseFunding(null)).toEqual([]);
    expect(parseFunding("tasuta")).toEqual([]);
    expect(parseFunding([{ load: "weekend", paid: true, prices: [] }, { load: "full", paid: "yes" }, null])).toEqual([]);
    // цена без суммы или валюты пропускается, вариант нагрузки остаётся
    expect(
      parseFunding([
        {
          load: "full",
          paid: true,
          prices: [{ amount: "4200", currency: "EUR", period: "semester" }, { amount: 0, currency: "EUR" }, { amount: 100, currency: "" }],
        },
      ]),
    ).toEqual([{ load: "full", paid: true, prices: [] }]);
    // незнакомый период — «other», исходный текст остаётся
    expect(parseFunding([{ load: "full", paid: true, prices: [{ amount: 300, currency: "EUR", period: "month", period_text: "kuu" }] }])).toEqual([
      { load: "full", paid: true, prices: [{ amount: 300, currency: "EUR", period: "other", periodText: "kuu", target: null }] },
    ]);
  });
});

describe("срок подачи на карточке эстонской программы", () => {
  const now = new Date("2026-10-13T10:00:00Z");
  const deadlines = { open: "2026-10-18T20:59:00+00:00", justClosed: "2026-10-13T09:59:00+00:00" };

  it("действующий срок показывается, прошедший и отсутствующий — нет", () => {
    expect(openDeadline(deadlines, "open", now)).toBe("2026-10-18T20:59:00+00:00");
    // перечень в памяти мог устареть на несколько минут — срок сверяется с часами
    expect(openDeadline(deadlines, "justClosed", now)).toBeNull();
    expect(openDeadline(deadlines, "unknown", now)).toBeNull();
    expect(openDeadline({}, "open", now)).toBeNull();
  });
});
