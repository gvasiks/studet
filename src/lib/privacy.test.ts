import { describe, expect, it } from "vitest";
import { fillPlaceholders, groupBody } from "./privacy";

describe("groupBody", () => {
  it("собирает подряд идущие пункты в один список, остальное — абзацы", () => {
    expect(groupBody(["Вступление", "- один", "- два", "Между", "- три"])).toEqual([
      { type: "p", text: "Вступление" },
      { type: "ul", items: ["один", "два"] },
      { type: "p", text: "Между" },
      { type: "ul", items: ["три"] },
    ]);
  });

  it("дефис внутри строки списком не считается", () => {
    expect(groupBody(["Ne - saraksts"])).toEqual([{ type: "p", text: "Ne - saraksts" }]);
  });
});

describe("fillPlaceholders", () => {
  it("подставляет известные значения, неизвестные оставляет как есть", () => {
    const text = "Pārzinis {controller}, e-pasts {email}, {other}";
    expect(fillPlaceholders(text, { controller: "X", email: "a@b" })).toBe("Pārzinis X, e-pasts a@b, {other}");
  });
});
