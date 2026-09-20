// Вспомогательное для страницы /privacy. Тексты политики — в словарях
// (privacy.*); здесь только подстановка контактов и разбор строк на
// абзацы и списки. Без импортов: модуль читается и тестами (vitest не
// понимает алиас "@/").

export type BodyBlock = { type: "p"; text: string } | { type: "ul"; items: string[] };

// Строка, начинающаяся с "- ", — пункт списка; подряд идущие пункты
// собираются в один список, остальные строки — абзацы.
export function groupBody(lines: string[]): BodyBlock[] {
  const blocks: BodyBlock[] = [];
  for (const line of lines) {
    if (line.startsWith("- ")) {
      const last = blocks[blocks.length - 1];
      const item = line.slice(2);
      if (last?.type === "ul") last.items.push(item);
      else blocks.push({ type: "ul", items: [item] });
    } else {
      blocks.push({ type: "p", text: line });
    }
  }
  return blocks;
}

export function fillPlaceholders(text: string, values: Record<string, string>): string {
  return text.replace(/\{(\w+)\}/g, (whole, key: string) => values[key] ?? whole);
}

// Кто отвечает за данные и куда писать — решает владелец при публикации
// (docs/PRIVACY-CHECKLIST.md). Пока переменные не заданы, страница показывает
// имена переменных вместо контактов, чтобы пустое место было видно.
export function getPrivacyContact(): { controller: string; email: string } {
  return {
    controller: process.env.PRIVACY_CONTROLLER_NAME || "[PRIVACY_CONTROLLER_NAME]",
    email: process.env.PRIVACY_CONTACT_EMAIL || "[PRIVACY_CONTACT_EMAIL]",
  };
}
