import { describe, expect, it } from "vitest";
import { formatDate } from "./dates";

describe("дата для показа", () => {
  const day = "2026-10-06T12:00:00Z";

  it("английская — с названием месяца, а не американским порядком цифр", () => {
    expect(formatDate(day, "en", "UTC")).toBe("6 Oct 2026");
    expect(formatDate(day, "en", "UTC")).not.toContain("10/6");
    // сентябрь — «Sep» везде, а не «Sept», как пишут одни браузеры
    expect(formatDate("2026-09-20T15:00:00Z", "en", "UTC")).toBe("20 Sep 2026");
    expect(formatDate("2027-01-05T12:00:00Z", "en", "UTC")).toBe("5 Jan 2027");
  });

  it("у остальных языков — их обычная запись цифрами", () => {
    expect(formatDate(day, "lv", "UTC")).toBe("6.10.2026.");
    expect(formatDate(day, "lt", "UTC")).toBe("2026-10-06");
    expect(formatDate(day, "et", "UTC")).toBe("6.10.2026");
  });

  it("по умолчанию — рижское время: одинаково на сервере и в браузере", () => {
    // 22:30 по UTC 5 октября — в Риге уже 6 октября
    expect(formatDate("2026-10-05T22:30:00Z", "lv")).toBe("6.10.2026.");
    // дата без времени — тот же день, а не накануне
    expect(formatDate("2027-07-20", "en")).toBe("20 Jul 2027");
  });

  it("часовой пояс решает, какой это день", () => {
    // 22:30 по UTC 5 октября — уже 6 октября в Таллине
    expect(formatDate("2026-10-05T22:30:00Z", "lv", "Europe/Tallinn")).toBe("6.10.2026.");
    expect(formatDate(new Date("2026-10-05T22:30:00Z"), "en", "UTC")).toBe("5 Oct 2026");
  });
});
