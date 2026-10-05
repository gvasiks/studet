import { describe, expect, it } from "vitest";
import { httpUrl, matchChannel, type ApplicationChannel } from "./application-channel";

function channel(overrides: Partial<ApplicationChannel>): ApplicationChannel {
  return {
    universityId: "lu",
    degreeLevel: null,
    channelType: "university",
    url: "https://example.lv/apply",
    sourceUrl: "https://example.lv/admission",
    verifiedAt: "2026-10-05T10:00:00+00:00",
    ...overrides,
  };
}

describe("matchChannel", () => {
  const channels = [
    channel({ degreeLevel: null, url: "https://lu.example/all" }),
    channel({ degreeLevel: "bachelor", channelType: "unified_portal", url: "https://portal.example/apply" }),
    channel({ universityId: "rtu", degreeLevel: null, url: "https://rtu.example/all" }),
  ];

  it("запись с уровнем программы важнее записи «все уровни»", () => {
    expect(matchChannel(channels, "lu", "bachelor")?.url).toBe("https://portal.example/apply");
  });

  it("для уровня без своей записи берётся запись «все уровни»", () => {
    expect(matchChannel(channels, "lu", "master")?.url).toBe("https://lu.example/all");
  });

  it("чужой вуз не подходит", () => {
    expect(matchChannel(channels, "rtu", "bachelor")?.url).toBe("https://rtu.example/all");
    expect(matchChannel(channels, "rsu", "bachelor")).toBeNull();
  });

  it("запись только для другого уровня не подставляется", () => {
    const onlyBachelor = [channel({ degreeLevel: "bachelor" })];
    expect(matchChannel(onlyBachelor, "lu", "master")).toBeNull();
  });
});

describe("httpUrl", () => {
  it("пропускает http и https", () => {
    expect(httpUrl("https://latvija.gov.lv/Services/1")).toBe("https://latvija.gov.lv/Services/1");
    expect(httpUrl("http://www.koledza.lv/")).toBe("http://www.koledza.lv/");
  });

  it("всё остальное — не ссылка", () => {
    expect(httpUrl("javascript:alert(1)")).toBeNull();
    expect(httpUrl("mailto:info@example.lv")).toBeNull();
    expect(httpUrl("www.example.lv")).toBeNull();
    expect(httpUrl("")).toBeNull();
    expect(httpUrl(null)).toBeNull();
  });
});
