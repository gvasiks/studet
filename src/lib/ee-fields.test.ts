import { describe, expect, it } from "vitest";
import { INTEREST_KEYS } from "./fields";
import { EE_FIELD_CODES, eeInterestOf } from "./ee-fields";

// Номера направлений (õppesuund) в справочнике государственного портала —
// все 34, что были в его данных 2026-10-11.
const PORTAL_FIELDS = [
  "2388", "2399", "2416", "2432", "2425", "2403", "2526", "2535", "2491", "2505", "2498", "2522", "2514",
  "2577", "2584", "2587", "2590", "2593", "2450", "2439", "2457", "2633", "2660", "2653", "2565", "2570",
  "2539", "2554", "2617", "2600", "2629", "2464", "2484", "2481",
];

describe("эстонские направления и категории интересов", () => {
  it("в списке 34 направления, и у каждого есть категория", () => {
    expect(new Set(PORTAL_FIELDS).size).toBe(34);
    expect([...EE_FIELD_CODES].sort()).toEqual([...PORTAL_FIELDS].sort());
    for (const code of PORTAL_FIELDS) expect(eeInterestOf(code, null), code).not.toBeNull();
  });

  it("категория по направлению — как у Латвии и Литвы", () => {
    expect(eeInterestOf("2526", null)).toBe("it");
    expect(eeInterestOf("2481", null)).toBe("law");
    expect(eeInterestOf("2653", null)).toBe("law"); // безопасность и оборона
    expect(eeInterestOf("2464", null)).toBe("business");
    expect(eeInterestOf("2600", null)).toBe("health");
    expect(eeInterestOf("2617", "Sotsiaaltöö ja nõustamine")).toBe("health");
    expect(eeInterestOf("2660", null)).toBe("engineering"); // транспорт
    expect(eeInterestOf("2498", null)).toBe("science"); // окружающая среда
    expect(eeInterestOf("2403", null)).toBe("arts");
    expect(eeInterestOf("2633", "Sport")).toBe("services");
    expect(eeInterestOf("2388", null)).toBe("society"); // педагогика
  });

  it("экономика — в бизнесе, остальные социальные науки — в обществе", () => {
    expect(eeInterestOf("2439", "Majandusteadus")).toBe("business");
    expect(eeInterestOf("2439", "Psühholoogia")).toBe("society");
    expect(eeInterestOf("2439", null)).toBe("society");
  });

  it("незнакомое направление — без категории", () => {
    expect(eeInterestOf("9999", null)).toBeNull();
    expect(eeInterestOf("", "Uus rühm")).toBeNull();
  });

  it("каждая категория анкеты кому-то досталась", () => {
    const used = new Set(PORTAL_FIELDS.map((code) => eeInterestOf(code, null)));
    used.add(eeInterestOf("2439", "Majandusteadus"));
    for (const key of INTEREST_KEYS) expect(used.has(key), key).toBe(true);
  });
});
