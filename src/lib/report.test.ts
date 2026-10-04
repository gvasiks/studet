import { describe, expect, it } from "vitest";
import { buildReportMailto, getReportEmail } from "./report";

describe("getReportEmail", () => {
  it("берёт FEEDBACK_EMAIL, а без него — адрес со страницы /privacy", () => {
    expect(getReportEmail({ FEEDBACK_EMAIL: "kludas@example.lv", PRIVACY_CONTACT_EMAIL: "dati@example.lv" })).toBe(
      "kludas@example.lv",
    );
    expect(getReportEmail({ PRIVACY_CONTACT_EMAIL: " dati@example.lv " })).toBe("dati@example.lv");
  });

  it("без адреса или с мусором вместо адреса — null, ссылка не выводится", () => {
    expect(getReportEmail({})).toBeNull();
    expect(getReportEmail({ FEEDBACK_EMAIL: "" })).toBeNull();
    expect(getReportEmail({ FEEDBACK_EMAIL: "[PRIVACY_CONTACT_EMAIL]" })).toBeNull();
    expect(getReportEmail({ FEEDBACK_EMAIL: "bez adreses" })).toBeNull();
  });
});

describe("buildReportMailto", () => {
  it("кодирует тему и текст, перенос строки — %0D%0A", () => {
    const href = buildReportMailto("kludas@example.lv", "Kļūda: Ekonomika & tiesības", "Lapa: https://x.lv/a?b=1\nKas nav pareizi:");
    expect(href).toBe(
      "mailto:kludas@example.lv?subject=K%C4%BC%C5%ABda%3A%20Ekonomika%20%26%20ties%C4%ABbas" +
        "&body=Lapa%3A%20https%3A%2F%2Fx.lv%2Fa%3Fb%3D1%0D%0AKas%20nav%20pareizi%3A",
    );
  });

  it("амперсанд в названии программы не ломает ссылку на части", () => {
    const href = buildReportMailto("a@b.lv", "A&body=x", "y");
    expect(href.split("&body=")).toHaveLength(2);
  });
});
