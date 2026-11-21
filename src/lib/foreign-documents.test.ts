import { describe, expect, it } from "vitest";
import { checklistSources, checklistStorageKey, groupByStage, parseRequirements } from "./foreign-documents";

const row = (overrides: Partial<Parameters<typeof parseRequirements>[0][number]> = {}) => ({
  document: "passport",
  applies_to: "all",
  stage: "application",
  note: null,
  sort_order: 0,
  source_url: "https://www.rtu.lv/en/studies/admission-1",
  verified_at: "2026-11-15T10:00:00Z",
  ...overrides,
});

describe("parseRequirements", () => {
  it("отбрасывает неподтверждённые строки и неизвестные ключи", () => {
    const items = parseRequirements([
      row(),
      row({ verified_at: null }),
      row({ document: "visa_photo" }),
      row({ applies_to: "everyone" }),
      row({ stage: "after_arrival" }),
    ]);
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({ document: "passport", appliesTo: "all", stage: "application" });
  });
});

describe("groupByStage", () => {
  it("сначала подача, потом до приезда; внутри — порядок источника; пустых этапов нет", () => {
    const items = parseRequirements([
      row({ document: "legalisation", stage: "before_arrival", sort_order: 9 }),
      row({ document: "cv", sort_order: 5 }),
      row({ document: "passport", sort_order: 1 }),
    ]);
    const groups = groupByStage(items);
    expect(groups.map((group) => group.stage)).toEqual(["application", "before_arrival"]);
    expect(groups[0].items.map((item) => item.document)).toEqual(["passport", "cv"]);
    expect(groupByStage(items.filter((item) => item.stage === "application")).map((group) => group.stage)).toEqual([
      "application",
    ]);
  });

  it("не меняет переданный список (он общий в памяти сервера)", () => {
    const items = parseRequirements([row({ document: "cv", sort_order: 5 }), row({ sort_order: 1 })]);
    groupByStage(items);
    expect(items.map((item) => item.document)).toEqual(["cv", "passport"]);
  });
});

describe("checklistSources", () => {
  it("источники без повторов и самая ранняя дата проверки", () => {
    const items = parseRequirements([
      row({ verified_at: "2026-11-20T00:00:00Z" }),
      row({ document: "cv", verified_at: "2026-11-15T00:00:00Z" }),
      row({ document: "legalisation", source_url: "https://www.rtu.lv/en/studies/immigration-regulations/visa-free-entry" }),
    ]);
    const sources = checklistSources(items);
    expect(sources.urls).toHaveLength(2);
    expect(sources.verifiedAt).toBe("2026-11-15T00:00:00Z");
    expect(sources.automatic).toBe(false);
    expect(checklistSources([])).toEqual({ urls: [], verifiedAt: null, automatic: false });
  });

  // Литва и Эстония (решение 2026-11-19): неподтверждённые строки проходят
  // только по флагу, и тогда весь список — «извлечено автоматически», без даты.
  it("неподтверждённые строки — только с allowUnverified, и список без даты", () => {
    const rows = [row({ verified_at: "2026-11-20T00:00:00Z" }), row({ document: "cv", verified_at: null })];
    expect(parseRequirements(rows)).toHaveLength(1);
    const items = parseRequirements(rows, true);
    expect(items).toHaveLength(2);
    expect(checklistSources(items)).toMatchObject({ verifiedAt: null, automatic: true });
  });
});

describe("checklistStorageKey", () => {
  it("свой ключ у вуза и уровня", () => {
    expect(checklistStorageKey("rtu", "bachelor")).toBe("studet:documents:rtu:bachelor");
    expect(checklistStorageKey("rtu", "master")).not.toBe(checklistStorageKey("rtu", "bachelor"));
  });
});
