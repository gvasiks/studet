import { describe, expect, it } from "vitest";
import { matchRounds, roundSources, type ApplicationRound } from "./deadlines";

const round = (overrides: Partial<ApplicationRound>): ApplicationRound => ({
  universityId: "uni-1",
  degreeLevel: null,
  languageOfInstruction: null,
  label: "round",
  opensOn: null,
  closesOn: null,
  note: null,
  sourceUrl: null,
  verifiedAt: "2026-11-22T09:55:29Z",
  ...overrides,
});

describe("matchRounds", () => {
  it("отбирает раунд другого вуза", () => {
    const rounds = [round({ universityId: "uni-2" })];
    expect(matchRounds(rounds, "uni-1", "bachelor", "en")).toHaveLength(0);
  });

  it("null в degree_level/language_of_instruction значит «для всех»", () => {
    const rounds = [round({})];
    expect(matchRounds(rounds, "uni-1", "bachelor", "lv")).toHaveLength(1);
    expect(matchRounds(rounds, "uni-1", "master", "en")).toHaveLength(1);
  });

  it("непустой degree_level должен совпасть точно", () => {
    const rounds = [round({ degreeLevel: "bachelor" })];
    expect(matchRounds(rounds, "uni-1", "bachelor", "lv")).toHaveLength(1);
    expect(matchRounds(rounds, "uni-1", "master", "lv")).toHaveLength(0);
  });

  it("возвращает несколько подходящих раундов сразу — пример Turība EN (Autumn + Winter intake)", () => {
    const rounds = [
      round({ label: "Autumn intake", languageOfInstruction: "en" }),
      round({ label: "Winter intake", languageOfInstruction: "en" }),
    ];
    expect(matchRounds(rounds, "uni-1", "bachelor", "en")).toHaveLength(2);
    expect(matchRounds(rounds, "uni-1", "bachelor", "lv")).toHaveLength(0);
  });
});

describe("roundSources", () => {
  it("два окна из одного документа, подтверждённые в один день, — одна строка", () => {
    const url = "https://jk.lv/uznemsana/";
    const rounds = [round({ label: "Ziemas", sourceUrl: url }), round({ label: "Vasaras", sourceUrl: url, verifiedAt: "2026-11-22T18:00:00Z" })];
    expect(roundSources(rounds)).toEqual([{ sourceUrl: url, verifiedAt: "2026-11-22T09:55:29Z" }]);
  });

  it("разные источники — разные строки; не-http адрес ссылкой не становится", () => {
    const rounds = [round({ sourceUrl: "https://a.lv" }), round({ sourceUrl: "javascript:alert(1)" })];
    expect(roundSources(rounds).map((s) => s.sourceUrl)).toEqual(["https://a.lv/", null]);
  });
});
