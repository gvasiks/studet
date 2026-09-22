import { describe, expect, it } from "vitest";
import { isPipelineStale, PIPELINE_STALE_AFTER_DAYS } from "./pipeline-health";

const NOW = new Date("2026-09-22T12:00:00Z");

describe("свежесть последнего сбора", () => {
  it("сбор ни разу не был успешным — просрочен", () => {
    expect(isPipelineStale(null, NOW)).toBe(true);
  });

  it("сбор два часа назад — не просрочен", () => {
    expect(isPipelineStale("2026-09-22T10:00:00Z", NOW)).toBe(false);
  });

  it("граница: 9 дней ещё не просрочен, день сверху — просрочен", () => {
    expect(PIPELINE_STALE_AFTER_DAYS).toBe(9);
    expect(isPipelineStale("2026-09-13T12:00:00Z", NOW)).toBe(false);
    expect(isPipelineStale("2026-09-12T00:00:00Z", NOW)).toBe(true);
  });
});
