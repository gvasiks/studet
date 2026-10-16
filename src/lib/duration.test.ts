import { describe, expect, it } from "vitest";
import { durationLabel } from "./duration";

const lv = { one: "gads", many: "gadi" };
const en = { one: "year", many: "years" };
const et = { one: "aasta", many: "aastat" };

describe("срок обучения", () => {
  it("латышский: единственное число у чисел на 1, кроме 11", () => {
    expect(durationLabel(1, "lv", lv)).toBe("1 gads");
    expect(durationLabel(21, "lv", lv)).toBe("21 gads");
    expect(durationLabel(11, "lv", lv)).toBe("11 gadi");
    expect(durationLabel(4, "lv", lv)).toBe("4 gadi");
  });

  it("дробь — с запятой и одним знаком, во множественном числе", () => {
    expect(durationLabel(4.5, "lv", lv)).toBe("4,5 gadi");
    expect(durationLabel(1.5, "lv", lv)).toBe("1,5 gadi");
    expect(durationLabel(2.0833333, "lv", lv)).toBe("2,1 gadi");
    expect(durationLabel(4.5, "en", en)).toBe("4.5 years");
  });

  it("английский и эстонский: единственное число только у единицы", () => {
    expect(durationLabel(1, "en", en)).toBe("1 year");
    expect(durationLabel(21, "en", en)).toBe("21 years");
    expect(durationLabel(1, "et", et)).toBe("1 aasta");
    expect(durationLabel(3, "et", et)).toBe("3 aastat");
  });
});
