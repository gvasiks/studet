import { describe, expect, it } from "vitest";
import { currentAccreditation, pickDetails, sourceHost } from "./programme-details";

const NIID = {
  degree_awarded_lv: "Profesionālais bakalaurs mehatronikā",
  qualification_lv: "Mehatronikas inženieris (6. PKL)",
  diploma_document_lv: "Profesionālā bakalaura diploms",
  description_lv: "Pirmā rindkopa.\n\nOtrā rindkopa.",
  details_source_url: "https://www.niid.lv/niid_search/program/24775?qy=&tg=",
  details_extracted_at: "2026-10-03T12:00:00+00:00",
};

const LU = {
  degree_awarded_en: "Bachelor of Humanities in English and Language Studies",
  description_en: "The programme consists of three sub-programmes.",
  details_source_url: "https://www.lu.lv/en/studies/study-programmes-1/bachelors-study-programmes/x/",
  details_extracted_at: "2026-10-03T12:00:00+00:00",
};

describe("pickDetails", () => {
  it("нет сведений — нет блока", () => {
    expect(pickDetails({}, "lv")).toBeNull();
    expect(pickDetails({ description_lv: "  " }, "lv")).toBeNull();
    expect(pickDetails({ degree_awarded_lv: null, description_en: null }, "en")).toBeNull();
  });

  it("латышские сведения из NIID показываются на обоих языках страницы, с lang=lv", () => {
    for (const locale of ["lv", "en"] as const) {
      const details = pickDetails(NIID, locale);
      expect(details?.lang).toBe("lv");
      expect(details?.degree).toBe("Profesionālais bakalaurs mehatronikā");
      expect(details?.qualification).toBe("Mehatronikas inženieris (6. PKL)");
      expect(details?.paragraphs).toEqual(["Pirmā rindkopa.", "Otrā rindkopa."]);
      expect(details?.sourceHost).toBe("niid.lv");
    }
  });

  it("английские сведения ЛУ показываются на обоих языках страницы, с lang=en", () => {
    for (const locale of ["lv", "en"] as const) {
      const details = pickDetails(LU, locale);
      expect(details?.lang).toBe("en");
      expect(details?.degree).toBe("Bachelor of Humanities in English and Language Studies");
      expect(details?.qualification).toBeNull();
      expect(details?.document).toBeNull();
      expect(details?.sourceHost).toBe("lu.lv");
    }
  });

  it("если есть оба набора — берётся тот, что на языке страницы", () => {
    const both = { ...NIID, ...LU };
    expect(pickDetails(both, "lv")?.lang).toBe("lv");
    expect(pickDetails(both, "en")?.lang).toBe("en");
  });

  it("только описание без степени — блок всё равно есть", () => {
    const details = pickDetails({ description_en: "Text." }, "lv");
    expect(details?.degree).toBeNull();
    expect(details?.paragraphs).toEqual(["Text."]);
    expect(details?.sourceHost).toBeNull();
  });
});

describe("sourceHost", () => {
  it("убирает www и путь", () => {
    expect(sourceHost("https://www.niid.lv/niid_search/program/543")).toBe("niid.lv");
    expect(sourceHost("https://venta.lv/program/x")).toBe("venta.lv");
  });

  it("мусор и пустота — null, а не исключение", () => {
    expect(sourceHost("not a url")).toBeNull();
    expect(sourceHost(null)).toBeNull();
    expect(sourceHost(undefined)).toBeNull();
  });
});

describe("currentAccreditation", () => {
  it("дата сегодня или позже показывается как есть", () => {
    expect(currentAccreditation("2027-04-22", "2026-10-04")).toBe("2027-04-22");
    expect(currentAccreditation("2026-10-04", "2026-10-04")).toBe("2026-10-04");
  });

  it("дата в прошлом не показывается — источник устарел", () => {
    expect(currentAccreditation("2026-03-31", "2026-10-04")).toBeNull();
    expect(currentAccreditation("2026-10-03", "2026-10-04")).toBeNull();
  });

  it("нет даты — нечего показывать", () => {
    expect(currentAccreditation(null, "2026-10-04")).toBeNull();
    expect(currentAccreditation(undefined, "2026-10-04")).toBeNull();
  });
});
