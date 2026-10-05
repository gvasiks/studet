import { describe, expect, it } from "vitest";
import { mergeDictionary } from "./merge";

describe("mergeDictionary", () => {
  const base = {
    meta: { title: "Latvia" },
    catalog: { title: "Catalogue", city: { riga: "Riga" } },
    rights: { title: "Rights", items: [{ id: "a" }, { id: "b" }] },
  };

  it("заменяет только названные строки, остальное остаётся", () => {
    const merged = mergeDictionary(base, { meta: { title: "Lithuania" }, catalog: { city: { vilnius: "Vilnius" } } });
    expect(merged.meta.title).toBe("Lithuania");
    expect(merged.catalog.title).toBe("Catalogue");
    expect(merged.catalog.city).toEqual({ riga: "Riga", vilnius: "Vilnius" });
  });

  it("список заменяется целиком, а не дополняется", () => {
    const merged = mergeDictionary(base, { rights: { items: [] } });
    expect(merged.rights.items).toEqual([]);
    expect(merged.rights.title).toBe("Rights");
  });

  it("базовый словарь не меняется", () => {
    mergeDictionary(base, { meta: { title: "x" } });
    expect(base.meta.title).toBe("Latvia");
  });
});
