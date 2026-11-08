import { describe, expect, it } from "vitest";
import {
  currentCountryCosts,
  euPriceIncludesCandidates,
  feesFor,
  firstYearTotal,
  formatMoney,
  type CountryCost,
  type ProgrammeFee,
} from "./foreign-costs";

function cost(partial: Partial<CountryCost>): CountryCost {
  return {
    code: "means_per_month",
    appliesTo: "non_eu",
    amount: 780,
    currency: "EUR",
    period: "month",
    validFrom: "2026-01-01",
    validTo: null,
    sourceTitle: "MK noteikumi",
    sourceUrl: "https://likumi.lv/",
    verifiedAt: "2026-11-08T00:00:00Z",
    ...partial,
  };
}

function fee(partial: Partial<ProgrammeFee>): ProgrammeFee {
  return {
    kind: "tuition",
    appliesTo: "non_eu",
    amount: 4000,
    currency: "EUR",
    period: "year",
    academicYear: "2027/28",
    sourceUrl: "https://example.lv/",
    verifiedAt: "2026-11-08T00:00:00Z",
    euScope: null,
    ...partial,
  };
}

describe("цена ЕС для стран-кандидатов", () => {
  it("пометка нужна, если хоть одна плата так помечена", () => {
    expect(euPriceIncludesCandidates([fee({}), fee({ euScope: "eu_efta_candidates" })])).toBe(true);
    expect(euPriceIncludesCandidates([fee({})])).toBe(false);
    expect(euPriceIncludesCandidates([])).toBe(false);
  });
});

describe("суммы страны на дату", () => {
  it("берёт действующую строку с самой поздней датой начала", () => {
    const rows = [
      cost({ amount: 740, validFrom: "2025-01-01", validTo: "2026-01-01" }),
      cost({ amount: 780, validFrom: "2026-01-01" }),
      cost({ amount: 800, validFrom: "2027-01-01" }),
    ];
    const current = currentCountryCosts(rows, new Date("2026-11-08T12:00:00Z"));
    expect(current.map((row) => row.amount)).toEqual([780]);
  });

  it("закрытая строка в день valid_to уже не действует", () => {
    const rows = [cost({ amount: 740, validFrom: "2025-01-01", validTo: "2026-01-01" })];
    expect(currentCountryCosts(rows, new Date("2026-01-01T12:00:00Z"))).toEqual([]);
  });
});

describe("плата программы", () => {
  it("по группе и за последний учебный год", () => {
    const fees = [
      fee({ amount: 3800, academicYear: "2026/27" }),
      fee({ amount: 4000, academicYear: "2027/28" }),
      fee({ amount: 2000, appliesTo: "eu" }),
    ];
    expect(feesFor(fees, "non_eu").tuition?.amount).toBe(4000);
    expect(feesFor(fees, "eu").tuition?.amount).toBe(2000);
  });
});

describe("итог первого года", () => {
  const costs = [
    cost({ code: "residence_permit_review", amount: 160, period: "once" }),
    cost({ code: "residence_permit_registration", amount: 75, period: "once" }),
    cost({ code: "long_stay_visa", amount: 90, period: "once" }),
    cost({ code: "means_per_month", amount: 780 }),
  ];

  it("плата + взносы вуза + пошлины ВНЖ; виза и средства не входят", () => {
    const fees = feesFor([fee({}), fee({ kind: "application_fee", amount: 50, period: "once" })], "non_eu");
    expect(firstYearTotal(fees, costs, "non_eu")).toEqual({ amount: 4000 + 50 + 160 + 75, currency: "EUR" });
  });

  it("у граждан ЕС пошлин ВНЖ нет — только плата", () => {
    expect(firstYearTotal(feesFor([fee({ appliesTo: "eu", amount: 2000 })], "eu"), costs, "eu")).toEqual({
      amount: 2000,
      currency: "EUR",
    });
  });

  it("без платы за обучение итога нет", () => {
    expect(firstYearTotal({}, costs, "non_eu")).toBeNull();
  });

  it("разные валюты не складываются", () => {
    expect(firstYearTotal(feesFor([fee({ currency: "USD" })], "non_eu"), costs, "non_eu")).toBeNull();
  });
});

describe("деньги по языку", () => {
  it("без копеек, если их нет", () => {
    expect(formatMoney(4000, "EUR", "en")).toBe("€4,000");
    expect(formatMoney(160, "EUR", "lv").replace(/\s/g, " ")).toBe("160 €");
    expect(formatMoney(12.5, "EUR", "en")).toBe("€12.50");
  });
});
