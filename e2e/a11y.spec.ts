import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Ключевые маршруты обеих аудиторий — не все (verification/favorites/
// calculator без подтверждённой формулы почти пусты, calculator сам по
// себе клиентский повтор тех же HeroUI-полей, что и в анкете). Ревью
// 2026-09, пункт 15: "клавиатурный проход по новым экранам на обоих
// языках" был сделан руками (см. коммит с фиксами) — это его
// автоматизированное продолжение на каждый push.
const ROUTES = ["", "/programmes", "/programmes/lu/economics", "/survey", "/match", "/rights", "/glossary", "/privacy", "/favorites"];
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

// Блок результатов /match появляется только после ввода экзаменов — его не
// видно на пустой странице, а вёрстка там самая сложная (счётчики в <dl>,
// группы, раскрывающийся разбор балла).
for (const locale of LOCALES) {
  test(`нет нарушений axe на /${locale}/match с введёнными экзаменами`, async ({ page }) => {
    await page.goto(`/${locale}/match`);
    const inputs = page.locator('input[type="number"]');
    await inputs.nth(0).fill("80");
    await inputs.nth(1).fill("70");
    await inputs.nth(2).fill("60");
    await page.locator("details summary").first().click();
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
  });
}
