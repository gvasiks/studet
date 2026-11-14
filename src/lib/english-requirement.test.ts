import { describe, expect, it } from "vitest";
import { parseEnglishRequirements, pickEnglishRequirement } from "./english-requirement";

const row = (overrides: Partial<Parameters<typeof parseEnglishRequirements>[0][number]> = {}) => ({
  programme_id: null,
  ielts_min: "6.0",
  toefl_ibt_min: 80,
  toefl_ibt_band: null,
  note: null,
  source_url: "https://apply.lu.lv/courses/course/163",
  verified_at: "2026-11-15T10:00:00Z",
  ...overrides,
});

describe("parseEnglishRequirements", () => {
  it("числа из numeric-колонок приходят строками — переводятся в числа", () => {
    const [item] = parseEnglishRequirements([row({ toefl_ibt_band: "4.0" })]);
    expect(item).toMatchObject({ ieltsMin: 6, toeflIbtMin: 80, toeflIbtBand: 4 });
  });

  it("неподтверждённые строки и строки без цифр отбрасываются", () => {
    expect(parseEnglishRequirements([row({ verified_at: null }), row({ ielts_min: null, toefl_ibt_min: null })])).toEqual([]);
  });
});

describe("pickEnglishRequirement", () => {
  const items = parseEnglishRequirements([
    row({ ielts_min: "6.0" }),
    row({ programme_id: "english-studies", ielts_min: "7.0", toefl_ibt_min: 100 }),
  ]);

  it("строка программы важнее строки вуза", () => {
    expect(pickEnglishRequirement(items, "english-studies")?.ieltsMin).toBe(7);
  });

  it("без своей строки у программы — требование вуза", () => {
    expect(pickEnglishRequirement(items, "physics")?.ieltsMin).toBe(6);
  });

  it("строка другой программы чужой программе не достаётся", () => {
    const only = parseEnglishRequirements([row({ programme_id: "english-studies" })]);
    expect(pickEnglishRequirement(only, "physics")).toBeNull();
  });
});
