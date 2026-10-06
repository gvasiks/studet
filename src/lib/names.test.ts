import { describe, expect, it } from "vitest";
import { localizedName } from "./names";

const latvian = { name_lv: "Latvijas Universitāte", name_lt: null, name_en: "University of Latvia" };
const latvianEnglishOnly = { name_lv: null, name_lt: null, name_en: "Economics" };
const lithuanian = { name_lv: null, name_lt: "Vilniaus universitetas", name_en: "Vilnius University" };
const lithuanianNativeOnly = { name_lv: null, name_lt: "Medicina", name_en: null };

describe("localizedName", () => {
  it("берёт название на языке страницы, когда оно есть", () => {
    expect(localizedName(latvian, "lv")).toBe("Latvijas Universitāte");
    expect(localizedName(latvian, "en")).toBe("University of Latvia");
    expect(localizedName(lithuanian, "lt")).toBe("Vilniaus universitetas");
    expect(localizedName(lithuanian, "en")).toBe("Vilnius University");
  });

  it("на чужом языке показывает название на языке страны, а не английское", () => {
    expect(localizedName(lithuanian, "lv")).toBe("Vilniaus universitetas");
    expect(localizedName(latvian, "lt")).toBe("Latvijas Universitāte");
  });

  it("английское — последний запасной вариант", () => {
    expect(localizedName(latvianEnglishOnly, "lv")).toBe("Economics");
    expect(localizedName(latvianEnglishOnly, "lt")).toBe("Economics");
    expect(localizedName(lithuanianNativeOnly, "en")).toBe("Medicina");
  });

  it("запись без name_lt (старый запрос) не ломается", () => {
    expect(localizedName({ name_lv: "Tiesību zinātne", name_en: null }, "lt")).toBe("Tiesību zinātne");
    expect(localizedName({ name_lv: null, name_en: null }, "lv")).toBe("");
  });
});
