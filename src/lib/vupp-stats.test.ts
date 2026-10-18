import { describe, expect, it } from "vitest";
import { latestVuppYear, vuppGroupName, vuppModeKey, vuppRound, type VuppStat } from "./vupp-stats";

function stat(overrides: Partial<VuppStat>): VuppStat {
  return {
    admissionYear: 2026,
    programmeCode: "207B7",
    programmeName: "Biznesa vadība",
    studyMode: "Pilna laika (dienas)",
    funding: "Budžets",
    city: "Rīga",
    places: 23,
    placesUnlimited: false,
    applications: 831,
    firstPriority: 174,
    passed: 23,
    stage: "2. kārtas apstiprinātie pieteikumi uzņemšanai pamatstudiju programmās",
    portalUpdatedOn: "2026-08-03",
    sourceUrl: "https://statistika.vupp.lv/2026_Vasara/2",
    extractedAt: "2026-10-18T12:00:00Z",
    ...overrides,
  };
}

describe("прошлогодний конкурс латвийской программы", () => {
  it("цифр нет — блока нет", () => {
    expect(latestVuppYear([])).toBeNull();
  });

  it("берётся самый поздний год, прошлые не подмешиваются", () => {
    const result = latestVuppYear([stat({ admissionYear: 2025, places: 31 }), stat({}), stat({ admissionYear: 2024 })]);
    expect(result?.year).toBe(2026);
    expect(result?.groups).toHaveLength(1);
    expect(result?.groups[0].rows.map((row) => row.places)).toEqual([23]);
    expect(result?.round).toBe(2);
    expect(result?.portalUpdatedOn).toBe("2026-08-03");
  });

  it("сначала бюджет, потом платные; очная форма раньше заочной", () => {
    const result = latestVuppYear([
      stat({ funding: "Maksa", studyMode: "Nepilna laika (klātiene vai vakara)" }),
      stat({ funding: "Maksa" }),
      stat({ funding: "Budžets", city: "Cēsis" }),
      stat({ funding: "Budžets" }),
    ]);
    expect(result?.groups[0].rows.map((row) => [row.funding, row.studyMode, row.city])).toEqual([
      ["Budžets", "Pilna laika (dienas)", "Cēsis"],
      ["Budžets", "Pilna laika (dienas)", "Rīga"],
      ["Maksa", "Pilna laika (dienas)", "Rīga"],
      ["Maksa", "Nepilna laika (klātiene vai vakara)", "Rīga"],
    ]);
  });

  it("подпрограммы — отдельными группами со своим названием", () => {
    const result = latestVuppYear([
      stat({ programmeCode: "20916", programmeName: "Bioloģija, apakšprogramma Biomedicīna" }),
      stat({ programmeCode: "20915", programmeName: "Bioloģija, apakšprogramma Bioloģija" }),
    ]);
    expect(result?.groups.map((group) => group.name)).toEqual([
      "Bioloģija, apakšprogramma Bioloģija",
      "Bioloģija, apakšprogramma Biomedicīna",
    ]);
  });

  it("разные коды с одним названием (очная и заочная форма РТУ) — одна таблица", () => {
    const result = latestVuppYear([
      stat({ programmeCode: "NGCS0", programmeName: "Skolotājs", studyMode: "Nepilna laika (neklātiene)", city: "Liepāja" }),
      stat({ programmeCode: "LGCS0", programmeName: "Skolotājs", city: "Liepāja" }),
    ]);
    expect(result?.groups).toHaveLength(1);
    expect(result?.groups[0].rows.map((row) => row.programmeCode)).toEqual(["LGCS0", "NGCS0"]);
  });

  it("филиалы — в одной таблице с основной программой", () => {
    const result = latestVuppYear([
      stat({ programmeCode: "204KH", programmeName: "Pirmsskolas skolotājs (Cēsis)", city: "Cēsis" }),
      stat({ programmeCode: "204KE", programmeName: "Pirmsskolas skolotājs" }),
    ]);
    expect(result?.groups.map((group) => group.name)).toEqual(["Pirmsskolas skolotājs"]);
    expect(result?.groups[0].rows.map((row) => row.city)).toEqual(["Cēsis", "Rīga"]);
    // скобка, которая не город строки, остаётся частью названия
    expect(vuppGroupName(stat({ programmeName: "Skolotājs (Matemātika)", city: "Daugavpils" }))).toBe("Skolotājs (Matemātika)");
  });

  it("незнакомая форма обучения не ломает порядок и остаётся в конце", () => {
    const result = latestVuppYear([stat({ studyMode: "Jauna forma" }), stat({})]);
    expect(result?.groups[0].rows.map((row) => row.studyMode)).toEqual(["Pilna laika (dienas)", "Jauna forma"]);
    expect(vuppModeKey("Jauna forma")).toBeNull();
  });

  it("тур берётся из заголовка среза", () => {
    expect(vuppRound("2. kārtas apstiprinātie pieteikumi")).toBe(2);
    expect(vuppRound("Apstiprinātie pieteikumi")).toBeNull();
  });
});
