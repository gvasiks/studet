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

  it("у базовых словарей один и тот же набор ключей", () => {
    // списки (items, sections) сравниваются как один ключ: их длина у стран разная
    expect(new Set(paths(lt))).toEqual(new Set(paths(lv)));
    expect(new Set(paths(en))).toEqual(new Set(paths(lv)));
  });
});
