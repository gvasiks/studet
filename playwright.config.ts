import { defineConfig } from "@playwright/test";

// Только axe-аудит доступности (ревью 2026-09, пункт 15) — не e2e для
// функциональности, для этого уже есть vitest на чистой логике. Именно
// поэтому webServer запускает "npm run start", не "next dev": пусть
// сборка уже случится один раз в CI-шаге до этого (ci.yml), а не дважды.
// Локально: собрать (`npm run build`) перед `npm run test:a11y`.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: {
    baseURL: "http://localhost:3000",
  },
  webServer: {
    command: "npm run start",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
