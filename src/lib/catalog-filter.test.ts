import { describe, expect, it } from "vitest";
import type { ProgrammeWithUniversity } from "./catalog";
import { filterProgrammes } from "./catalog-filter";

const programme = (id: string, fields: Record<string, unknown>, university: Record<string, unknown> = {}) =>
  ({
    id,
    city: "riga",
    language_of_instruction: "lv",
    study_mode: "full_time",
    funding_type: "both",
    ...fields,
    university: { slug: "lu", kind: "public", country: "LV", ...university },
  }) as unknown as ProgrammeWithUniversity;

const CATALOG = [
  programme("law", {}),
  programme("it-en", { language_of_instruction: "en", funding_type: "paid" }, { slug: "rtu" }),
  programme("design", { city: "liepaja", study_mode: "part_time" }, { slug: "riseba", kind: "private" }),
  programme("no-city", { city: null, funding_type: "budget" }),
  // литовская программа: вид финансирования не известен
  programme("lt", { city: "vilnius", language_of_instruction: "lt", funding_type: null }, { slug: "vu", country: "LT" }),
];

const ids = (list: ProgrammeWithUniversity[]) => list.map((item) => item.id);
const NO_FIELDS = new Map<string, string>();

describe("отбор программ в памяти", () => {
  it("без фильтров — весь список, новым массивом", () => {
    const result = filterProgrammes(CATALOG, {}, null, NO_FIELDS);
    expect(ids(result)).toEqual(["law", "it-en", "design", "no-city", "lt"]);
    expect(result).not.toBe(CATALOG);
  });

  it("город: программа без города под фильтр не попадает", () => {
    expect(ids(filterProgrammes(CATALOG, { cities: ["riga"] }, null, NO_FIELDS))).toEqual(["law", "it-en"]);
    expect(ids(filterProgrammes(CATALOG, { cities: ["liepaja", "vilnius"] }, null, NO_FIELDS))).toEqual(["design", "lt"]);
    expect(ids(filterProgrammes(CATALOG, { cities: [] }, null, NO_FIELDS))).toHaveLength(5);
  });

  it("язык, форма, вуз и тип вуза", () => {
    expect(ids(filterProgrammes(CATALOG, { language: "en" }, null, NO_FIELDS))).toEqual(["it-en"]);
    expect(ids(filterProgrammes(CATALOG, { mode: "part_time" }, null, NO_FIELDS))).toEqual(["design"]);
    expect(ids(filterProgrammes(CATALOG, { university: "rtu" }, null, NO_FIELDS))).toEqual(["it-en"]);
    expect(ids(filterProgrammes(CATALOG, { kind: "private" }, null, NO_FIELDS))).toEqual(["design"]);
  });

  it("только бюджет: «бюджет» и «бюджет и платно»; без сведений — не попадает", () => {
    expect(ids(filterProgrammes(CATALOG, { budgetOnly: true }, null, NO_FIELDS))).toEqual(["law", "design", "no-city"]);
  });

  it("интересы: по направлению программы; без разметки — не попадает", () => {
    const fields = new Map([
      ["law", "380"],
      ["it-en", "481"],
      ["design", "214"],
    ]);
    expect(ids(filterProgrammes(CATALOG, { interests: ["it"] }, new Set(["481", "483"]), fields))).toEqual(["it-en"]);
    expect(ids(filterProgrammes(CATALOG, { interests: ["law", "it"] }, new Set(["380", "481"]), fields))).toEqual(["law", "it-en"]);
    expect(filterProgrammes(CATALOG, { interests: ["it"] }, new Set(["999"]), fields)).toEqual([]);
  });

  it("несколько фильтров действуют вместе", () => {
    expect(ids(filterProgrammes(CATALOG, { cities: ["riga"], language: "lv", budgetOnly: true }, null, NO_FIELDS))).toEqual(["law"]);
  });
});
