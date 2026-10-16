import { test, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

// подписи кнопок — из тех же словарей, что у сайта
const dictionary = (language: string) =>
  JSON.parse(readFileSync(`src/i18n/dictionaries/${language}.json`, "utf8")) as { survey: { next: string } };
const lv = dictionary("lv");
const en = dictionary("en");

// Клавиатурный проход (предрелизная проверка Д5, CLAUDE.md: «клавиатурный
// проход по новым экранам на обоих языках»). axe в a11y.spec.ts смотрит
// разметку, но не проходит формы: здесь анкета и калькулятор заполняются
// только клавишами Tab, пробел, Enter и цифрами — без мыши.

/** Нажимать Tab, пока фокус не встанет на подходящий элемент. */
async function tabTo(page: Page, matches: (element: Element) => boolean, limit = 80) {
  for (let step = 0; step < limit; step += 1) {
    await page.keyboard.press("Tab");
    if (await page.evaluate(matches, undefined as never).catch(() => false)) return;
  }
  throw new Error("за отведённое число нажатий Tab фокус не дошёл до нужного элемента");
}

const LANGUAGES = [
  { locale: "lv", dict: lv },
  { locale: "en-lv", dict: en },
] as const;

for (const { locale, dict } of LANGUAGES) {
  test(`анкета проходится клавиатурой: /${locale}/survey`, async ({ page }) => {
    await page.goto(`/${locale}/survey`);
    const firstStep = await page.locator("main legend").first().innerText();

    await tabTo(page, () => document.activeElement?.matches('main input[type="checkbox"]') ?? false);
    await page.keyboard.press("Space");
    expect(await page.evaluate(() => (document.activeElement as HTMLInputElement).checked)).toBe(true);

    const next = dict.survey.next;
    await page.evaluate((label) => ((window as unknown as { __next: string }).__next = label), next);
    await tabTo(
      page,
      () =>
        document.activeElement?.tagName === "BUTTON" &&
        document.activeElement.textContent?.trim() === (window as unknown as { __next: string }).__next,
    );
    await page.keyboard.press("Enter");
    await expect(page.locator("main legend").first()).not.toHaveText(firstStep);
  });

  test(`калькулятор заполняется клавиатурой: /${locale}/programmes/lu/economics/calculator`, async ({ page }) => {
    await page.goto(`/${locale}/programmes/lu/economics/calculator`);
    const fields = await page.locator('main input[type="text"]').count();
    expect(fields).toBeGreaterThan(0);
    for (let index = 0; index < fields; index += 1) {
      await tabTo(
        page,
        () => (document.activeElement?.matches('main input[type="text"]') ?? false) && (document.activeElement as HTMLInputElement).value === "",
      );
      await page.keyboard.type("80");
    }
    // итог объявляется экранному диктору: живая область с числом
    const status = page.locator('main [role="status"]').first();
    await expect(status).toHaveAttribute("aria-live", "polite");
    await expect(status).toContainText(/\d+[.,]\d{2}/);
  });
}

// Фокус виден: у первых элементов страницы в порядке Tab есть рамка
// (outline) или кольцо (box-shadow) — WCAG 2.2, 2.4.7.
for (const path of ["/lv/programmes", "/en-lv/programmes/lu/economics"]) {
  test(`фокус виден на первых шагах Tab: ${path}`, async ({ page }) => {
    await page.goto(path);
    for (let step = 0; step < 6; step += 1) {
      await page.keyboard.press("Tab");
      const visible = await page.evaluate(() => {
        const element = document.activeElement;
        if (!element || element === document.body) return { ok: true, what: "body" };
        const style = getComputedStyle(element);
        const outline = style.outlineStyle !== "none" && parseFloat(style.outlineWidth) > 0;
        const ring = style.boxShadow !== "none";
        return { ok: outline || ring, what: `${element.tagName} ${element.textContent?.trim().slice(0, 40)}` };
      });
      expect(visible.ok, `нет видимого фокуса у ${visible.what}`).toBe(true);
    }
  });
}
