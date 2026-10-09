import { describe, expect, it } from "vitest";
import { CAPTURE_URL, pageviewEvent, shouldCount, uuidv7, withoutQuery } from "./analytics";

const visit = { distinctId: "visitor-1", sessionId: "session-1" };

describe("счётчик посещений: что уходит в аналитику", () => {
  it("сервер — в Европейском союзе", () => {
    expect(new URL(CAPTURE_URL).hostname).toBe("eu.i.posthog.com");
  });

  it("параметры адреса и якорь не уходят: ни текст поиска, ни ответы анкеты", () => {
    expect(withoutQuery("https://studypick.eu/lv/programmes?q=medic%C4%ABna&interest=it&city=riga#top")).toBe(
      "https://studypick.eu/lv/programmes",
    );
    expect(withoutQuery("https://studypick.eu/lt/programmes/vu/medicina")).toBe("https://studypick.eu/lt/programmes/vu/medicina");
    expect(withoutQuery("")).toBe("");
    expect(withoutQuery("не адрес")).toBe("");
  });

  it("событие просмотра содержит только перечисленные поля", () => {
    const event = pageviewEvent(
      "phc_test",
      visit,
      "https://studypick.eu/lv/programmes?q=tiesibas&budget=1",
      "https://www.google.com/search?q=augstskolas+uznemsana",
    );
    expect(event).toEqual({
      api_key: "phc_test",
      event: "$pageview",
      distinct_id: "visitor-1",
      properties: {
        $current_url: "https://studypick.eu/lv/programmes",
        $host: "studypick.eu",
        $pathname: "/lv/programmes",
        $referrer: "https://www.google.com/search",
        $referring_domain: "www.google.com",
        $session_id: "session-1",
        $process_person_profile: false,
        $lib: "studypick-web",
      },
    });
    // ни поискового запроса на сайте, ни запроса в поисковике
    expect(JSON.stringify(event)).not.toMatch(/tiesibas|budget|augstskolas/);
  });

  it("заход без источника помечается как прямой", () => {
    const { properties } = pageviewEvent("phc_test", visit, "https://studypick.eu/lv", "");
    expect(properties.$referrer).toBe("$direct");
    expect(properties.$referring_domain).toBe("$direct");
  });

  it("номер визита — UUID версии 7 с временем в начале", () => {
    const random = new Uint8Array([0xab, 0xcd, 0xef, 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xff]);
    const id = uuidv7(Date.UTC(2026, 9, 9), random);
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
    expect(parseInt(id.replace(/-/g, "").slice(0, 12), 16)).toBe(Date.UTC(2026, 9, 9));
    expect(uuidv7(1, random)).not.toBe(uuidv7(2, random));
  });

  it("считается только рабочий сайт: без ключа, при разработке и на localhost — нет", () => {
    expect(shouldCount("phc_test", "production", "studypick.eu")).toBe(true);
    expect(shouldCount(undefined, "production", "studypick.eu")).toBe(false);
    expect(shouldCount("", "production", "studypick.eu")).toBe(false);
    expect(shouldCount("phc_test", "development", "studypick.eu")).toBe(false);
    expect(shouldCount("phc_test", "production", "localhost")).toBe(false);
    expect(shouldCount("phc_test", "production", "127.0.0.1")).toBe(false);
    expect(shouldCount("phc_test", "production", "app.localhost")).toBe(false);
  });
});
