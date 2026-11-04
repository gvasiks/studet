"use client";

// Введённые экзамены — в sessionStorage этой вкладки (решение владельца
// 2026-11-03): раньше они жили только в памяти страницы и пропадали, стоило
// открыть программу из «Kur var iestāties» и вернуться назад. sessionStorage,
// а не localStorage: вкладку закрыли — результатов нет; на сервер и в адрес
// они по-прежнему не попадают (экзамены несовершеннолетних, CLAUDE.md).
// Политика конфиденциальности говорит именно так — меняя хранение, правь и её.
//
// Ключ — на страну, общий для «Kur var iestāties» и калькулятора: экзамены,
// введённые в одном месте, видны в другом. Каждая форма читает только свои
// предметы и, записывая, не стирает чужие.
//
// useSyncExternalStore, как в FavoriteButton: хранилище — внешнее состояние,
// снимок — строка, на сервере пустая (поля приходят пустыми и заполняются
// после загрузки).

import { useCallback, useMemo, useSyncExternalStore } from "react";
import type { Country } from "@/i18n/config";

const CHANGE_EVENT = "studet:exams-changed";

function storageKey(country: Country): string {
  return `studet:exams:${country.toLowerCase()}`;
}

// Если sessionStorage недоступен (приватный режим Safari, запрет сайту
// хранить данные), ввод живёт здесь — до перезагрузки страницы, как раньше.
const memory = new Map<Country, string>();
const broken = new Set<Country>();

function readRaw(country: Country): string {
  if (typeof window === "undefined") return "";
  if (broken.has(country)) return memory.get(country) ?? "";
  try {
    return window.sessionStorage.getItem(storageKey(country)) ?? "";
  } catch {
    return memory.get(country) ?? "";
  }
}

function writeRaw(country: Country, raw: string): void {
  memory.set(country, raw);
  try {
    if (raw === "") window.sessionStorage.removeItem(storageKey(country));
    else window.sessionStorage.setItem(storageKey(country), raw);
  } catch {
    broken.add(country);
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

function subscribe(onChange: () => void): () => void {
  window.addEventListener(CHANGE_EVENT, onChange);
  return () => window.removeEventListener(CHANGE_EVENT, onChange);
}

// Битый JSON или чужая форма записи — считаем, что ничего не введено.
function parse(raw: string): Record<string, unknown> {
  if (raw === "") return {};
  try {
    const value: unknown = JSON.parse(raw);
    return value !== null && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

/**
 * Как useState для полей экзаменов, но значения переживают переход на другую
 * страницу в этой вкладке. `isValid` отсеивает записи, которые форма не
 * понимает: значение из хранилища могли подменить руками.
 */
export function useSessionExams<T>(
  country: Country,
  subjects: readonly string[],
  empty: T,
  isValid: (value: unknown) => value is T,
): [Record<string, T>, (update: (prev: Record<string, T>) => Record<string, T>) => void, () => void] {
  const raw = useSyncExternalStore(
    subscribe,
    () => readRaw(country),
    () => "",
  );

  const inputs = useMemo(() => {
    const stored = parse(raw);
    return Object.fromEntries(
      subjects.map((subject) => {
        const value = stored[subject];
        return [subject, isValid(value) ? value : empty];
      }),
    );
  }, [raw, subjects, empty, isValid]);

  const setInputs = useCallback(
    (update: (prev: Record<string, T>) => Record<string, T>) => {
      // Читаем заново, а не из замыкания: два поля, изменённые подряд, не
      // должны затирать друг друга.
      const stored = parse(readRaw(country));
      const prev = Object.fromEntries(
        subjects.map((subject) => [subject, isValid(stored[subject]) ? (stored[subject] as T) : empty]),
      );
      writeRaw(country, JSON.stringify({ ...stored, ...update(prev) }));
    },
    [country, subjects, empty, isValid],
  );

  const clear = useCallback(() => writeRaw(country, ""), [country]);

  return [inputs, setInputs, clear];
}

const MAX_LENGTH = 10;

const LEVELS: readonly unknown[] = ["augstakais", "optimalais", "vispaarigais"];

/** Поле латвийского экзамена: процент и уровень. */
export function isLvExamInput(value: unknown): value is { percent: string; level: "augstakais" | "optimalais" | "vispaarigais" | null } {
  if (value === null || typeof value !== "object") return false;
  const { percent, level } = value as Record<string, unknown>;
  return typeof percent === "string" && percent.length <= MAX_LENGTH && (level === null || LEVELS.includes(level));
}

/** Поле литовского экзамена: оценка и курс математики. */
export function isLtExamInput(value: unknown): value is { score: string; course: "A" | "B" } {
  if (value === null || typeof value !== "object") return false;
  const { score, course } = value as Record<string, unknown>;
  return typeof score === "string" && score.length <= MAX_LENGTH && (course === "A" || course === "B");
}
