import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  // Тот же псевдоним "@/…", что в tsconfig.json: без него тест модуля,
  // который импортирует через "@/", не запускается.
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  test: {
    // e2e/ — отдельный набор для Playwright (аудит доступности, пункт 15
    // ревью 2026-09), не для vitest: vitest по умолчанию подхватывает
    // и *.spec.ts тоже, а API у @playwright/test другой.
    exclude: ["node_modules/**", "e2e/**"],
  },
});
