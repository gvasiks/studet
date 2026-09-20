import { describe, expect, it } from "vitest";
import { documentAgeDays, isDocumentStale, STALE_AFTER_DAYS } from "./document-age";

const NOW = new Date("2026-09-20T12:00:00Z");

describe("возраст документа-источника", () => {
  it("считает полные дни", () => {
    expect(documentAgeDays("2026-09-19", NOW)).toBe(1);
    expect(documentAgeDays("2026-09-20", NOW)).toBe(0);
  });

  it("документ ЛУ 2025/26 (04.07.2025) на 20.09.2026 устарел", () => {
    expect(isDocumentStale("2025-07-04", NOW)).toBe(true);
  });

  it("документ Ventspils с поправкой 18.06.2026 свежий", () => {
    expect(isDocumentStale("2026-06-18", NOW)).toBe(false);
  });

  it("граница: ровно год ещё не устарел, день сверху — устарел", () => {
    expect(isDocumentStale("2025-09-20", NOW)).toBe(false);
    expect(STALE_AFTER_DAYS).toBe(365);
    expect(isDocumentStale("2025-09-19", NOW)).toBe(true);
  });

  it("без даты документа — не считаем устаревшим (об этом скажет неполный протокол)", () => {
    expect(isDocumentStale(null, NOW)).toBe(false);
  });
});
