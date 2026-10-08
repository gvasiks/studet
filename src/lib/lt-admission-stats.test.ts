import { describe, expect, it } from "vitest";
import { latestAdmissionYear, type LtAdmissionStat } from "./lt-admission-stats";

function stat(admissionYear: number, funding: LtAdmissionStat["funding"], applications: number): LtAdmissionStat {
  return {
    admissionYear,
    funding,
    applications,
    firstPriority: 1,
    invited: 1,
    signed: 1,
    sourceUrl: "https://data.gov.lt/datasets/2914/",
    extractedAt: `${admissionYear}-10-08T00:00:00Z`,
  };
}

describe("цифры прошлого приёма литовской программы", () => {
  it("чисел нет — блока нет", () => {
    expect(latestAdmissionYear([])).toBeNull();
  });

  it("берётся самый поздний год, прошлые годы не подмешиваются", () => {
    const result = latestAdmissionYear([stat(2024, "state", 700), stat(2025, "state", 893), stat(2024, "paid", 400)]);
    expect(result?.year).toBe(2025);
    expect(result?.rows.map((row) => [row.funding, row.applications])).toEqual([["state", 893]]);
    expect(result?.extractedAt).toBe("2025-10-08T00:00:00Z");
  });

  it("виды места идут в одном порядке, как бы ни пришли из базы", () => {
    const result = latestAdmissionYear([stat(2025, "paid", 93), stat(2025, "stipend", 55), stat(2025, "state", 266)]);
    expect(result?.rows.map((row) => row.funding)).toEqual(["state", "stipend", "paid"]);
  });

  it("незнакомый вид места не показывается", () => {
    const odd = { ...stat(2025, "state", 5), funding: "other" as unknown as LtAdmissionStat["funding"] };
    expect(latestAdmissionYear([odd])).toBeNull();
  });
});
