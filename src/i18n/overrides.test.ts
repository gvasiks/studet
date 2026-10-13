import { describe, expect, it } from "vitest";
import { mergeDictionary } from "./merge";
import lv from "./dictionaries/lv.json";
import en from "./dictionaries/en.json";
import lt from "./dictionaries/lt.json";
import enLt from "./dictionaries/en-lt.json";
import lvLt from "./dictionaries/lv-lt.json";
import ltLv from "./dictionaries/lt-lv.json";
import enEe from "./dictionaries/en-ee.json";
import et from "./dictionaries/et.json";
import etLv from "./dictionaries/et-lv.json";
import etLt from "./dictionaries/et-lt.json";
import lvEe from "./dictionaries/lv-ee.json";
import ltEe from "./dictionaries/lt-ee.json";

// Файл отличий накладывается на базовый словарь по ключам. Ключ с
// опечаткой не заменил бы строку, а молча добавил бы новую, которую никто
// не читает, — посетитель увидел бы текст про другую страну.
function paths(value: unknown, prefix = ""): string[] {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return [prefix];
  return Object.entries(value).flatMap(([key, child]) => paths(child, `${prefix}.${key}`));
}

describe("файлы отличий словарей", () => {
  const cases = [
    { name: "en-lt", override: enLt, base: en },
    { name: "lv-lt", override: lvLt, base: lv },
    { name: "lt-lv", override: ltLv, base: lt },
    { name: "en-ee", override: enEe, base: en },
    { name: "lv-ee", override: lvEe, base: lv },
    { name: "lt-ee", override: ltEe, base: lt },
    // эстонский словарь лежит поверх английского (dictionaries.ts)
    { name: "et-lv", override: etLv, base: mergeDictionary(en, et) },
    { name: "et-lt", override: etLt, base: mergeDictionary(en, et) },
  ];

  for (const { name, override, base } of cases) {
    it(`${name}: каждый ключ есть в базовом словаре`, () => {
      const known = new Set(paths(base));
      expect(paths(override).filter((path) => !known.has(path))).toEqual([]);
    });
  }

  // Эстонский словарь лежит поверх английского (dictionaries.ts): строка,
  // которой в et.json нет, молча показалась бы по-английски. Поэтому в нём
  // обязаны быть все те же ключи, что в английском, — и короткие тексты, и
  // словарь терминов, права и политика (списки сравниваются как один ключ).
  it("et: в эстонском словаре те же ключи, что в английском", () => {
    expect(paths(et).sort()).toEqual(paths(en).sort());
  });

  it("et: подстановки те же, что в английской строке", () => {
    const flat = (value: unknown, prefix = ""): [string, string][] =>
      typeof value === "string"
        ? [[prefix, value]]
        : Object.entries(value as Record<string, unknown>).flatMap(([key, child]) => flat(child, `${prefix}.${key}`));
    const english = new Map(flat(en).filter(([, text]) => typeof text === "string"));
    const placeholders = (line: string) => (line.match(/\{\w+\}/g) ?? []).sort();
    // длинные разделы у стран разные по составу — их сверяют тесты ниже
    const long = ["rights", "glossary", "privacy"];
    for (const [path, text] of flat(et)) {
      if (long.includes(path.split(".")[1])) continue;
      expect(placeholders(text), path).toEqual(placeholders(english.get(path) ?? ""));
    }
  });

  // Эстонские словарь, права и политика написаны сразу на четырёх языках
  // (et.json — эстонский; остальные — в файлах отличий) по закону о высшем
  // образовании Эстонии.
  describe("Эстония: словарь, права и политика на четырёх языках", () => {
    const ids = (list: { id: string }[]) => list.map((entry) => entry.id);
    const estonia = [
      { name: "et", dictionary: et, latvia: etLv },
      { name: "lv-ee", dictionary: mergeDictionary(lv, lvEe), latvia: lv },
      { name: "en-ee", dictionary: mergeDictionary(en, enEe), latvia: en },
      { name: "lt-ee", dictionary: mergeDictionary(lt, ltEe), latvia: mergeDictionary(lt, ltLv) },
    ];

    it("на каждом языке один и тот же набор записей и та же ссылка на закон", () => {
      for (const { name, dictionary } of estonia) {
        expect(ids(dictionary.glossary.items), name).toEqual(ids(et.glossary.items));
        expect(ids(dictionary.rights.items), name).toEqual(ids(et.rights.items));
        expect(ids(dictionary.privacy.sections), name).toEqual(ids(et.privacy.sections));
        expect(dictionary.rights.sources.map((source) => source.url), name).toEqual(["https://www.riigiteataja.ee/akt/KHaS"]);
      }
    });

    it("нет пустых записей и повторяющихся якорей", () => {
      for (const { name, dictionary } of estonia) {
        for (const item of dictionary.glossary.items) expect(item.term && item.definition && item.source, `${name} ${item.id}`).toBeTruthy();
        for (const item of dictionary.rights.items) expect(item.title && item.text && item.source, `${name} ${item.id}`).toBeTruthy();
        expect(new Set(ids(dictionary.glossary.items)).size, name).toBe(dictionary.glossary.items.length);
        expect(new Set(ids(dictionary.rights.items)).size, name).toBe(dictionary.rights.items.length);
        expect(dictionary.rights.checkedNote && dictionary.rights.intro && dictionary.glossary.intro, name).toBeTruthy();
      }
    });

    // Латышский и литовский словари написаны для своих стран: эстонские
    // тексты не должны достаться им в наследство.
    it("в правах и словаре нет латвийских и литовских записей", () => {
      for (const { name, dictionary } of estonia) {
        const text = JSON.stringify([dictionary.rights.items, dictionary.rights.intro, dictionary.rights.checkedNote, dictionary.glossary]);
        expect(text, name).not.toMatch(/MK noteikumi|Nr\. 846|nr 846|No\. 846|LAMA BPO/);
      }
    });

    it("политика отличается от латвийской на том же языке только в трёх разделах", () => {
      const own = new Set(["survey", "minors", "rights"]);
      for (const { name, dictionary, latvia } of estonia) {
        const sections = dictionary.privacy.sections;
        expect(ids(sections), name).toEqual(ids(latvia.privacy.sections));
        sections.forEach((section, index) => {
          const original = latvia.privacy.sections[index];
          if (own.has(section.id)) {
            expect(section, `${name} ${section.id}`).not.toEqual(original);
            expect(section.body.length, `${name} ${section.id}`).toBe(original.body.length);
          } else {
            expect(section, `${name} ${section.id}`).toEqual(original);
          }
        });
      }
    });

    it("в эстонской политике — эстонский надзорный орган и возраст согласия 13 лет", () => {
      for (const { name, dictionary } of estonia) {
        const text = JSON.stringify(dictionary.privacy);
        expect(text, name).toContain("aki.ee");
        expect(text, name).not.toContain("vdai.lrv.lt");
        expect(dictionary.privacy.sections.find((section) => section.id === "minors")!.body[0], name).toContain("13");
      }
    });
  });

  // Литовский и эстонский переводы латвийских словаря, прав и политики: тот
  // же набор записей, что в латышском оригинале, — иначе якорные ссылки и
  // оглавление на разных языках разошлись бы.
  for (const [name, translation] of [
    ["lt-lv", ltLv],
    ["et-lv", etLv],
  ] as const) {
    it(`${name}: словарь, права и политика содержат те же записи, что латышский оригинал`, () => {
      const ids = (list: { id: string }[]) => list.map((entry) => entry.id);
      expect(ids(translation.glossary.items)).toEqual(ids(lv.glossary.items));
      expect(ids(translation.rights.items)).toEqual(ids(lv.rights.items));
      expect(ids(translation.privacy.sections)).toEqual(ids(lv.privacy.sections));
      expect(translation.rights.sources.map((source) => source.url)).toEqual(lv.rights.sources.map((source) => source.url));
    });

    it(`${name}: в политике столько же строк, те же списки и те же подстановки`, () => {
      const placeholders = (line: string) => (line.match(/\{\w+\}/g) ?? []).sort();
      lv.privacy.sections.forEach((original, index) => {
        const translated = translation.privacy.sections[index];
        expect(translated.body.length, original.id).toBe(original.body.length);
        original.body.forEach((line, lineIndex) => {
          expect(translated.body[lineIndex].startsWith("- "), `${original.id}[${lineIndex}]`).toBe(line.startsWith("- "));
          expect(placeholders(translated.body[lineIndex]), `${original.id}[${lineIndex}]`).toEqual(placeholders(line));
        });
      });
    });

    it(`${name}: у каждой записи есть текст и источник, в правах и политике — оговорка о переводе`, () => {
      for (const item of translation.glossary.items) expect(item.term && item.definition && item.source, item.id).toBeTruthy();
      for (const item of translation.rights.items) expect(item.title && item.text && item.source, item.id).toBeTruthy();
      expect(translation.rights.checkedNote).not.toBe(lv.rights.checkedNote);
      expect(translation.privacy.intro).not.toBe(lv.privacy.intro);
    });
  }

  // Литовские словарь, права и политика написаны сразу на трёх языках
  // (lt.json — литовский; английский и латышский — в файлах отличий);
  // эстонский перевод добавлен 2026-10-13 (et-lt.json).
  describe("Литва: словарь, права и политика на четырёх языках", () => {
    const ids = (list: { id: string }[]) => list.map((entry) => entry.id);

    it("на каждом языке один и тот же набор записей и те же ссылки на источники", () => {
      for (const translated of [enLt, lvLt, etLt]) {
        expect(ids(translated.glossary.items)).toEqual(ids(lt.glossary.items));
        expect(ids(translated.rights.items)).toEqual(ids(lt.rights.items));
        expect(ids(translated.privacy.sections)).toEqual(ids(lt.privacy.sections));
        expect(translated.rights.sources.map((source) => source.url)).toEqual(lt.rights.sources.map((source) => source.url));
      }
    });

    it("нет пустых записей и повторяющихся якорей", () => {
      for (const dictionary of [lt, enLt, lvLt, etLt]) {
        for (const item of dictionary.glossary.items) {
          expect(item.term && item.definition && item.source, item.id).toBeTruthy();
        }
        for (const item of dictionary.rights.items) {
          expect(item.title && item.text && item.source, item.id).toBeTruthy();
        }
        expect(new Set(ids(dictionary.glossary.items)).size).toBe(dictionary.glossary.items.length);
        expect(new Set(ids(dictionary.rights.items)).size).toBe(dictionary.rights.items.length);
        expect(dictionary.rights.checkedNote && dictionary.rights.intro && dictionary.glossary.intro).toBeTruthy();
      }
    });

    // Политика у двух стран одна и та же, кроме трёх мест: какие фильтры
    // анкеты попадают в адрес, возраст согласия и куда жаловаться. Если
    // поправить латвийский текст и забыть литовский, тест это покажет.
    it("политика отличается от латвийской на том же языке только в трёх разделах", () => {
      const own = new Set(["survey", "minors", "rights"]);
      const pairs = [
        { lithuania: lt.privacy.sections, latvia: ltLv.privacy.sections },
        { lithuania: enLt.privacy.sections, latvia: en.privacy.sections },
        { lithuania: lvLt.privacy.sections, latvia: lv.privacy.sections },
        { lithuania: etLt.privacy.sections, latvia: etLv.privacy.sections },
      ];
      for (const { lithuania, latvia } of pairs) {
        expect(ids(lithuania)).toEqual(ids(latvia));
        lithuania.forEach((section, index) => {
          if (own.has(section.id)) {
            expect(section, section.id).not.toEqual(latvia[index]);
            expect(section.body.length, section.id).toBe(latvia[index].body.length);
          } else {
            expect(section, section.id).toEqual(latvia[index]);
          }
        });
      }
    });

    it("в литовской политике — литовский возраст согласия и литовский надзорный орган", () => {
      for (const dictionary of [lt, enLt, lvLt, etLt]) {
        const text = JSON.stringify(dictionary.privacy.sections);
        expect(text).toContain("14");
        expect(text).not.toMatch(/\b13\b/);
        expect(text).toContain("vdai.lrv.lt");
      }
    });
  });

  it("у базовых словарей один и тот же набор ключей", () => {
    // списки (items, sections) сравниваются как один ключ: их длина у стран разная
    expect(new Set(paths(lt))).toEqual(new Set(paths(lv)));
    expect(new Set(paths(en))).toEqual(new Set(paths(lv)));
  });
});
