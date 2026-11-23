import { describe, expect, it } from "vitest";
import { admissionYear, eeVariants, variantLines, type EeVariantSource } from "./ee-variants";

function programme(id: string, name: string, extra: Partial<EeVariantSource> = {}): EeVariantSource {
  return { id, university_id: "tlu", name_et: name, degree_level: "bachelor", language_of_instruction: "et", ...extra };
}

const texts = {
  specialization: "Specialisation: {name}",
  admission: "SAIS {year}",
  admissionUndated: "SAIS, no dates",
  noAdmission: "No SAIS round",
};

describe("версии одного учебного плана у эстонских программ", () => {
  it("у программы без двойника подписей нет", () => {
    const result = eeVariants([programme("a", "Ajakirjandus"), programme("b", "Psühholoogia")], new Map(), new Map([["a", { year: 2026 }]]));
    expect(result.size).toBe(0);
  });

  it("разные специализация и конкурс — обе подписи", () => {
    const result = eeVariants(
      [programme("a", "Audiovisuaalne meedia"), programme("b", "Audiovisuaalne meedia")],
      new Map([
        ["a", "televisioon ja audiovisuaalne meedia"],
        ["b", "audiovisuaalne meedia"],
      ]),
      new Map([["a", { year: 2026 }]]),
    );
    expect(result.get("a")).toEqual({ specialization: "televisioon ja audiovisuaalne meedia", admission: { year: 2026 } });
    expect(result.get("b")).toEqual({ specialization: "audiovisuaalne meedia", admission: "none" });
  });

  it("одинаковое у всей группы не показывается", () => {
    const result = eeVariants(
      [programme("a", "Ajakirjandus"), programme("b", "Ajakirjandus")],
      new Map([
        ["a", "ajakirjandus"],
        ["b", "Ajakirjandus"],
      ]),
      new Map([["a", { year: 2026 }]]),
    );
    // специализация совпала (без учёта регистра) — только конкурс
    expect(result.get("a")).toEqual({ admission: { year: 2026 } });
    expect(result.get("b")).toEqual({ admission: "none" });
  });

  it("у обеих конкурс одного года — по конкурсу не различаются", () => {
    const result = eeVariants(
      [programme("a", "Bioloogia"), programme("b", "Bioloogia")],
      new Map(),
      new Map([
        ["a", { year: 2026 }],
        ["b", { year: 2026 }],
      ]),
    );
    expect(result.size).toBe(0);
  });

  it("специализация есть только у одной — подпись только у неё", () => {
    const result = eeVariants([programme("a", "Koreograafia"), programme("b", "Koreograafia")], new Map([["a", "tantsupedagoogika"]]), new Map());
    expect(result.get("a")).toEqual({ specialization: "tantsupedagoogika" });
    expect(result.has("b")).toBe(false);
  });

  it("другой вуз, уровень или язык — не двойник", () => {
    const result = eeVariants(
      [
        programme("a", "Informaatika"),
        programme("b", "Informaatika", { university_id: "ut" }),
        programme("c", "Informaatika", { degree_level: "master" }),
        programme("d", "Informaatika", { language_of_instruction: "en" }),
      ],
      new Map(),
      new Map([["a", { year: 2026 }]]),
    );
    expect(result.size).toBe(0);
  });

  it("год конкурса — по эстонским часам, с начала подачи", () => {
    // 1 января 2027 года, 00:00 по Таллину — по UTC ещё 2026 год
    expect(admissionYear("2026-12-31T22:00:00+00:00", null)).toBe(2027);
    expect(admissionYear(null, "2026-07-05T20:59:00+00:00")).toBe(2026);
    expect(admissionYear(null, null)).toBeNull();
  });

  it("подписи по строке на различие", () => {
    expect(variantLines(undefined, texts)).toEqual([]);
    expect(variantLines({ specialization: "x", admission: { year: 2026 } }, texts)).toEqual(["Specialisation: x", "SAIS 2026"]);
    expect(variantLines({ admission: "none" }, texts)).toEqual(["No SAIS round"]);
    expect(variantLines({ admission: { year: null } }, texts)).toEqual(["SAIS, no dates"]);
  });
});
