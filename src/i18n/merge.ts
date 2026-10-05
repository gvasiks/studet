// Наложить отличия на базовый словарь. Объекты сливаются по ключам,
// всё остальное (строки, списки) заменяется целиком: список из отличий —
// это новый список, а не дополнение к старому.
export function mergeDictionary<T>(base: T, patch: unknown): T {
  if (patch === null || typeof patch !== "object" || Array.isArray(patch)) return patch as T;
  if (base === null || typeof base !== "object" || Array.isArray(base)) return patch as T;

  const result: Record<string, unknown> = { ...(base as Record<string, unknown>) };
  for (const [key, value] of Object.entries(patch)) {
    result[key] = mergeDictionary(result[key], value);
  }
  return result as T;
}
