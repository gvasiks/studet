// Балл для показа: два знака после запятой, десятичный знак — по языку
// («551,67» по-латышски, «551.67» по-английски). Раньше латвийский
// калькулятор и /match писали точку на всех языках (аудит 2026-10-04);
// литовский калькулятор форматировал по языку и раньше.
export function formatPoints(value: number, language: string): string {
  return value.toLocaleString(language, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
