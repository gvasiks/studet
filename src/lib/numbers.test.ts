import { describe, expect, it } from "vitest";
import { formatPoints } from "./numbers";

describe("балл для показа", () => {
  it("два знака, десятичный знак по языку", () => {
    expect(formatPoints(551.666, "lv")).toBe("551,67");
    expect(formatPoints(551.666, "en")).toBe("551.67");
    expect(formatPoints(42, "lt")).toBe("42,00");
    expect(formatPoints(7.5, "et")).toBe("7,50");
  });
});
