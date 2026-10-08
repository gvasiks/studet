import { describe, expect, it } from "vitest";
import lv from "./dictionaries/lv.json";
import en from "./dictionaries/en.json";
import lt from "./dictionaries/lt.json";
import enLt from "./dictionaries/en-lt.json";
import lvLt from "./dictionaries/lv-lt.json";
import ltLv from "./dictionaries/lt-lv.json";

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
  ];

  for (const { name, override, base } of cases) {
    it(`${name}: каждый ключ есть в базовом словаре`, () => {
      const known = new Set(paths(base));
      expect(paths(override).filter((path) => !known.has(path))).toEqual([]);
    });
  }

  // Литовский перевод латвийских словаря, прав и политики: тот же набор
  // записей, что в латышском оригинале, — иначе якорные ссылки и оглавление
  // на двух языках разошлись бы.
  it("lt-lv: словарь, права и политика содержат те же записи, что латышский оригинал", () => {
    const ids = (list: { id: string }[]) => list.map((entry) => entry.id);
    expect(ids(ltLv.glossary.items)).toEqual(ids(lv.glossary.items));
    expect(ids(ltLv.rights.items)).toEqual(ids(lv.rights.items));
    expect(ids(ltLv.privacy.sections)).toEqual(ids(lv.privacy.sections));
    expect(ltLv.rights.sources.map((source) => source.url)).toEqual(lv.rights.sources.map((source) => source.url));
  });

  it("lt-lv: в политике столько же строк, те же списки и те же подстановки", () => {
    const placeholders = (line: string) => (line.match(/\{\w+\}/g) ?? []).sort();
    lv.privacy.sections.forEach((original, index) => {
      const translated = ltLv.privacy.sections[index];
      expect(translated.body.length, original.id).toBe(original.body.length);
      original.body.forEach((line, lineIndex) => {
        expect(translated.body[lineIndex].startsWith("- "), `${original.id}[${lineIndex}]`).toBe(line.startsWith("- "));
        expect(placeholders(translated.body[lineIndex]), `${original.id}[${lineIndex}]`).toEqual(placeholders(line));
      });
    });
  });

  // Литовские словарь, права и политика написаны сразу на трёх языках
  // (lt.json — литовский; английский и латышский — в файлах отличий).
  describe("Литва: словарь, права и политика на трёх языках", () => {
    const ids = (list: { id: string }[]) => list.map((entry) => entry.id);

    it("на каждом языке один и тот же набор записей и те же ссылки на источники", () => {
      for (const translated of [enLt, lvLt]) {
        expect(ids(translated.glossary.items)).toEqual(ids(lt.glossary.items));
        expect(ids(translated.rights.items)).toEqual(ids(lt.rights.items));
        expect(ids(translated.privacy.sections)).toEqual(ids(lt.privacy.sections));
        expect(translated.rights.sources.map((source) => source.url)).toEqual(lt.rights.sources.map((source) => source.url));
      }
    });

    it("нет пустых записей и повторяющихся якорей", () => {
      for (const dictionary of [lt, enLt, lvLt]) {
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
      for (const dictionary of [lt, enLt, lvLt]) {
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
