import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // e2e/ — отдельный набор для Playwright (аудит доступности, пункт 15
    // ревью 2026-09), не для vitest: vitest по умолчанию подхватывает
    // и *.spec.ts тоже, а API у @playwright/test другой.
    exclude: ["node_modules/**", "e2e/**"],
  },
});
