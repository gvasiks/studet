import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Ключевые маршруты обеих аудиторий — не все (verification/favorites/
// calculator без подтверждённой формулы почти пусты, calculator сам по
// себе клиентский повтор тех же HeroUI-полей, что и в анкете). Ревью
// 2026-09, пункт 15: "клавиатурный проход по новым экранам на обоих
// языках" был сделан руками (см. коммит с фиксами) — это его
// автоматизированное продолжение на каждый push.
const ROUTES = ["", "/programmes", "/programmes/lu/economics", "/survey", "/match"];
const LOCALES = ["lv", "en"] as const;

for (const locale of LOCALES) {
  for (const route of ROUTES) {
    test(`нет нарушений axe на /${locale}${route}`, async ({ page }) => {
      await page.goto(`/${locale}${route}`);
      const results = await new AxeBuilder({ page }).analyze();
      expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
    });
  }
}
