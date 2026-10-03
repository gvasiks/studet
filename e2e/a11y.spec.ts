import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Ключевые маршруты обеих аудиторий — не все (verification/favorites/
// calculator без подтверждённой формулы почти пусты, calculator сам по
// себе клиентский повтор тех же HeroUI-полей, что и в анкете). Ревью
// 2026-09, пункт 15: "клавиатурный проход по новым экранам на обоих
// языках" был сделан руками (см. коммит с фиксами) — это его
// автоматизированное продолжение на каждый push.
// /programmes/gfk/110 — программа из NIID: на ней есть блоки «Ko iegūsi» и
// «Par programmu» (диплом и описание), которых нет у программ ЛУ.
const ROUTES = ["", "/programmes", "/programmes/lu/economics", "/programmes/gfk/110", "/survey", "/match", "/rights", "/glossary", "/privacy", "/favorites"];
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

// «Мой список» с сохранёнными программами: карточки, галочки «сравнить»
// (пятая и дальше — неактивные) и таблица сравнения. Пустую страницу
// проверяет общий цикл выше, но вся вёрстка появляется только со списком.
for (const locale of LOCALES) {
  test(`нет нарушений axe на /${locale}/favorites с пятью программами`, async ({ page }) => {
    await page.goto(`/${locale}/programmes`);
    const stars = page.locator('main article button[aria-pressed="false"]');
    for (let i = 0; i < 5; i++) await stars.first().click();
    await page.goto(`/${locale}/favorites`);
    await page.locator("table").waitFor();
    await expect(page.locator('main article input[type="checkbox"]:disabled')).toHaveCount(1);
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
  });
}

// Меню шапки на телефоне: общий цикл идёт в широкой раскладке, где шесть
// пунктов стоят строкой, а кнопки «Izvēlne» нет вовсе.
for (const locale of LOCALES) {
  test(`нет нарушений axe на /${locale}/programmes с открытым меню на телефоне`, async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`/${locale}/programmes`);
    await page.locator('button[aria-controls="site-menu"]').click();
    await page.locator("#site-menu").waitFor();
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
  });
}
