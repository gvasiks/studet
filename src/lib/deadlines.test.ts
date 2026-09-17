import { describe, expect, it } from "vitest";
import { matchRounds, type ApplicationRound } from "./deadlines";

const round = (overrides: Partial<ApplicationRound>): ApplicationRound => ({
  universityId: "uni-1",
  degreeLevel: null,
  languageOfInstruction: null,
  label: "round",
  opensOn: null,
  closesOn: null,
  note: null,
  sourceUrl: null,
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
