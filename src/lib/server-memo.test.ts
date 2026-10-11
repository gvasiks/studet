import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { forgetEverything, remember } from "./server-memo";

const TTL = 5 * 60_000;

// Часы теста: время двигается только вручную.
let clock = 0;
const now = () => clock;
// Дать отработать фоновым обещаниям.
const settle = () => new Promise((resolve) => setTimeout(resolve, 0));

beforeEach(() => {
  clock = 1_000_000;
  forgetEverything();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("память серверного процесса", () => {
  it("первый раз идёт в базу, дальше отдаёт запомненное", async () => {
    const load = vi.fn(async () => ["a", "b"]);
    expect(await remember("list", TTL, load, now)).toEqual(["a", "b"]);
    clock += TTL - 1;
    expect(await remember("list", TTL, load, now)).toEqual(["a", "b"]);
    expect(load).toHaveBeenCalledTimes(1);
  });

  it("у каждого ключа своё значение", async () => {
    expect(await remember("LV", TTL, async () => 977, now)).toBe(977);
    expect(await remember("LT", TTL, async () => 1020, now)).toBe(1020);
    expect(await remember("LV", TTL, async () => 0, now)).toBe(977);
  });

  it("одновременные первые запросы ждут одну загрузку", async () => {
    const load = vi.fn(async () => "value");
    const results = await Promise.all([remember("k", TTL, load, now), remember("k", TTL, load, now)]);
    expect(results).toEqual(["value", "value"]);
    expect(load).toHaveBeenCalledTimes(1);
  });

  it("когда срок вышел, посетитель получает прежнее сразу, а новое — следующий", async () => {
    let version = 1;
    const load = vi.fn(async () => `v${version}`);
    expect(await remember("k", TTL, load, now)).toBe("v1");

    version = 2;
    clock += TTL;
    expect(await remember("k", TTL, load, now)).toBe("v1");
    await settle();
    expect(await remember("k", TTL, load, now)).toBe("v2");
    expect(load).toHaveBeenCalledTimes(2);
  });

  it("пока идёт обновление, второе не запускается", async () => {
    let release: (value: string) => void = () => {};
    const slow = vi.fn(() => new Promise<string>((resolve) => (release = resolve)));
    await remember("k", TTL, async () => "old", now);

    clock += TTL;
    expect(await remember("k", TTL, slow, now)).toBe("old");
    expect(await remember("k", TTL, slow, now)).toBe("old");
    expect(slow).toHaveBeenCalledTimes(1);

    release("new");
    await settle();
    expect(await remember("k", TTL, slow, now)).toBe("new");
  });

  it("сбой обновления оставляет прежнее значение и повторяет попытку не сразу", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    await remember("k", TTL, async () => "old", now);

    const failing = vi.fn(async () => {
      throw new Error("база не ответила");
    });
    clock += TTL;
    expect(await remember("k", TTL, failing, now)).toBe("old");
    await settle();

    // сразу после сбоя новых попыток нет
    clock += 1_000;
    expect(await remember("k", TTL, failing, now)).toBe("old");
    await settle();
    expect(failing).toHaveBeenCalledTimes(1);

    // через полминуты — следующая попытка, и она удаётся
    clock += 30_000;
    const working = vi.fn(async () => "new");
    expect(await remember("k", TTL, working, now)).toBe("old");
    await settle();
    expect(await remember("k", TTL, working, now)).toBe("new");
  });

  it("сбой первой загрузки уходит вызывающему и не запоминается", async () => {
    await expect(remember("k", TTL, async () => Promise.reject(new Error("нет связи")), now)).rejects.toThrow("нет связи");
    expect(await remember("k", TTL, async () => "value", now)).toBe("value");
  });
});
