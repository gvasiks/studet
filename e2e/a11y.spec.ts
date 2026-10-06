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
// /programmes/lu/economics/calculator — калькулятор с формулой; /programmes/lu/nav-tadas — страница
// «не найдено» (код ответа 404, но вёрстка своя — её тоже проверяем).
const ROUTES = ["", "/programmes", "/programmes/lu/economics", "/programmes/lu/economics/calculator", "/programmes/gfk/110", "/programmes/lu/nav-tadas", "/survey", "/match", "/rights", "/glossary", "/privacy", "/favorites"];
const LOCALES = ["lv", "en-lv", "lt-lv"] as const;

for (const locale of LOCALES) {
  for (const route of ROUTES) {
    test(`нет нарушений axe на /${locale}${route}`, async ({ page }) => {
      await page.goto(`/${locale}${route}`);
      const results = await new AxeBuilder({ page }).analyze();
      expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
    });
  }
}

// Литва: каталог, карточка, расчёт балла и «куда я прохожу» на литовском и
// английском. /lt/survey — раздела у Литвы ещё нет, проверяется вёрстка
// страницы «не найдено». Адреса существуют только при
// NEXT_PUBLIC_PREVIEW_COUNTRIES=1 (локально — .env.local, в CI — ci.yml).
const LT_ROUTES = [
  "/lt",
  "/lt/programmes",
  "/lt/programmes/vu/medicina",
  // расчёт балла: форма (медицина) и страница «расчёта нет» (предметная педагогика)
  "/lt/programmes/vu/medicina/calculator",
  "/lt/programmes/vu/dalyko-pedagogika/calculator",
  "/lt/favorites",
  "/lt/match",
  "/lt/survey",
  "/en-lt",
  "/en-lt/programmes",
  "/en-lt/programmes/vu/medicina",
  // Литва на латышском (решение 2026-10-06). Латвия на литовском (/lt-lv)
  // открыта без флага и проверяется выше вместе с остальными адресами Латвии.
  "/lv-lt",
  "/lv-lt/programmes",
  "/lv-lt/programmes/vu/medicina",
];

for (const route of LT_ROUTES) {
  test(`нет нарушений axe на ${route}`, async ({ page }) => {
    await page.goto(route);
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
  });
}

// Блок результатов /match появляется только после ввода экзаменов — его не
// видно на пустой странице, а вёрстка там самая сложная (счётчики в <dl>,
// группы, раскрывающийся разбор балла).
for (const locale of LOCALES) {
  test(`нет нарушений axe на /${locale}/match с введёнными экзаменами`, async ({ page }) => {
    await page.goto(`/${locale}/match`);
    const inputs = page.locator('input[inputmode="decimal"]');
    await inputs.nth(0).fill("80");
    await inputs.nth(1).fill("70");
    await inputs.nth(2).fill("60");
    await page.locator("details summary").first().click();
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
  });
}

// То же для Литвы: карточки групп с баллом, раскрытый разбор и раскрытый
// список программ. Форма другая (LtMatchForm), поэтому свой сценарий.
for (const locale of ["lt", "en-lt"] as const) {
  test(`нет нарушений axe на /${locale}/match с введёнными экзаменами`, async ({ page }) => {
    await page.goto(`/${locale}/match`);
    const inputs = page.locator('input[inputmode="decimal"]');
    await inputs.nth(0).fill("80");
    await inputs.nth(1).fill("70");
    await inputs.nth(2).fill("60");
    await page.locator("details summary").first().click();
    await page.locator("button[aria-controls^='lt-match-programmes-']").first().click();
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
