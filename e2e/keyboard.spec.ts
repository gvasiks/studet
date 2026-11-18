import { test, expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

// подписи кнопок — из тех же словарей, что у сайта
const dictionary = (language: string) =>
  JSON.parse(readFileSync(`src/i18n/dictionaries/${language}.json`, "utf8")) as { survey: { next: string } };
const lv = dictionary("lv");
const en = dictionary("en");
const lt = dictionary("lt");
const et = dictionary("et");

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

// Анкета: латвийская на всех языках интерфейса, литовская и эстонская
// (последние две — за флагом предпросмотра, как в a11y.spec.ts).
const SURVEYS = [
  { locale: "lv", dict: lv },
  { locale: "en-lv", dict: en },
  { locale: "lt-lv", dict: lt },
  { locale: "et-lv", dict: et },
  { locale: "lt", dict: lt },
  { locale: "et", dict: et },
] as const;

// Калькулятор с формулой: латвийский (ЛУ) на латышском, английском и
// эстонском, литовский (VU, медицина).
const CALCULATORS = [
  "/lv/programmes/lu/economics/calculator",
  "/en-lv/programmes/lu/economics/calculator",
  "/et-lv/programmes/lu/economics/calculator",
  "/lt/programmes/vu/medicina/calculator",
];

for (const { locale, dict } of SURVEYS) {
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
    // фокус перешёл на заголовок нового шага, а не остался на кнопке
    expect(await page.evaluate(() => document.activeElement?.tagName)).toBe("LEGEND");
    // у каждой группы ответов есть имя для экранного диктора
    const unnamed = await page.locator('main [role="radiogroup"]:not([aria-label]), main [role="group"]:not([aria-label]):has(input)').count();
    expect(unnamed).toBe(0);
  });
}

for (const path of CALCULATORS) {
  test(`калькулятор заполняется клавиатурой: ${path}`, async ({ page }) => {
    await page.goto(path);
    const fields = await page.locator('main input[type="text"]').count();
    expect(fields).toBeGreaterThan(0);
    for (let index = 0; index < fields; index += 1) {
      await tabTo(
        page,
        () => (document.activeElement?.matches('main input[type="text"]') ?? false) && (document.activeElement as HTMLInputElement).value === "",
      );
      await page.keyboard.type("80");
      // латвийский калькулятор: уровень экзамена выбирается обязательно
      // (решение владельца 2026-10-16) — Tab в группу уровней и пробел
      if (!path.startsWith("/lt/")) {
        await page.keyboard.press("Tab");
        if (await page.evaluate(() => document.activeElement?.matches('input[type="radio"]') ?? false)) {
          await page.keyboard.press("Space");
        }
      }
    }
    // итог объявляется экранному диктору: живая область с числом
    const status = page.locator('main [role="status"]').first();
    await expect(status).toHaveAttribute("aria-live", "polite");
    await expect(status).toContainText(/\d+[.,]\d{2}/);
  });
}

// Фокус виден: у первых элементов страницы в порядке Tab есть рамка
// (outline) или кольцо (box-shadow) — WCAG 2.2, 2.4.7.
for (const path of ["/lv/programmes", "/en-lv/programmes/lu/economics", "/lt/programmes", "/et/programmes"]) {
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

// Прошлогодний конкурс (с 2026-10-18): больше трёх подпрограмм — каждая
// свёрнута в <details>; заголовок открывается клавишей Enter, фокус на нём виден.
test("свёрнутая подпрограмма прошлогоднего конкурса открывается клавиатурой", async ({ page }) => {
  await page.goto("/lv/programmes/du/niid-94");
  await tabTo(page, () => document.activeElement?.matches("#past-admission summary") ?? false, 200);
  const state = () =>
    page.evaluate(() => {
      const summary = document.activeElement as HTMLElement;
      const style = getComputedStyle(summary);
      return {
        open: (summary.parentElement as HTMLDetailsElement).open,
        focusVisible: (style.outlineStyle !== "none" && parseFloat(style.outlineWidth) > 0) || style.boxShadow !== "none",
      };
    });
  expect(await state()).toEqual({ open: false, focusVisible: true });
  await page.keyboard.press("Enter");
  expect((await state()).open).toBe(true);
});

// Защитные заголовки (next.config.ts, аудит 2026-10-04): страницу нельзя
// встроить в чужой фрейм, сервер не называет себя.
test("защитные заголовки на ответах сайта", async ({ request }) => {
  const response = await request.get("/lv");
  const headers = response.headers();
  expect(headers["x-frame-options"]).toBe("DENY");
  expect(headers["content-security-policy"]).toContain("frame-ancestors 'none'");
  expect(headers["content-security-policy"]).toContain("default-src 'self'");
  expect(headers["content-security-policy"]).toContain("script-src 'self' 'unsafe-inline'");
  expect(headers["content-security-policy"]).not.toContain("unsafe-eval");
  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
  expect(headers["x-powered-by"]).toBeUndefined();
});

// Политика ограничивает источники скриптов, стилей, картинок и запросов
// (next.config.ts, проверка безопасности 2026-11-16, находка 2). Если Next.js,
// HeroUI или новая страница возьмёт что-то не из разрешённого списка, браузер
// это заблокирует молча — тест ловит такие отказы на главных страницах.
for (const path of [
  "/lv",
  "/en-lv",
  "/lv/programmes",
  "/lv/programmes/lu/economics",
  "/lv/programmes/lu/economics/calculator",
  "/en-lv/programmes/rtu/computer-science-236",
  "/lv/survey",
  "/lv/match",
  "/lv/favorites",
  "/en-lv/student-documents",
  "/en-lv/student-permit",
]) {
  test(`политика CSP ничего не блокирует: ${path}`, async ({ page }) => {
    const violations: string[] = [];
    await page.addInitScript(() => {
      document.addEventListener("securitypolicyviolation", (event) => {
        (window as unknown as { __csp: string[] }).__csp ??= [];
        (window as unknown as { __csp: string[] }).__csp.push(`${event.violatedDirective} ${event.blockedURI}`);
      });
    });
    page.on("console", (message) => {
      if (/content security policy/i.test(message.text())) violations.push(message.text());
    });
    await page.goto(path);
    await page.waitForLoadState("networkidle");
    const fromPage = await page.evaluate(() => (window as unknown as { __csp?: string[] }).__csp ?? []);
    expect([...violations, ...fromPage]).toEqual([]);
  });
}

// Продукт для иностранцев (предрелизная проверка 2026-11-15): чек-лист
// документов отмечается пробелом, счётчик в живой области меняется, отметка
// переживает перезагрузку; фокус виден на новых страницах.
for (const locale of ["lv", "en-lv"]) {
  test(`чек-лист документов отмечается клавиатурой: /${locale}`, async ({ page }) => {
    await page.goto(`/${locale}/programmes/rtu/computer-science-236`);
    const progress = page.locator('section[aria-labelledby="foreign-documents"] [aria-live="polite"]');
    const before = await progress.innerText();
    await tabTo(page, () => document.activeElement?.matches('section[aria-labelledby="foreign-documents"] input[type="checkbox"]') ?? false, 200);
    const focusVisible = await page.evaluate(() => {
      const style = getComputedStyle(document.activeElement as Element);
      return (style.outlineStyle !== "none" && parseFloat(style.outlineWidth) > 0) || style.boxShadow !== "none";
    });
    expect(focusVisible, "нет видимого фокуса у флажка").toBe(true);
    await page.keyboard.press("Space");
    await expect(page.locator('section[aria-labelledby="foreign-documents"] input[type="checkbox"]').first()).toBeChecked();
    await expect(progress).not.toHaveText(before);
    await page.reload();
    await expect(page.locator('section[aria-labelledby="foreign-documents"] input[type="checkbox"]').first()).toBeChecked();
  });

  test(`оглавление списков документов работает с клавиатуры: /${locale}/student-documents`, async ({ page }) => {
    await page.goto(`/${locale}/student-documents`);
    await tabTo(page, () => document.activeElement?.matches('main a[href^="#"]') ?? false, 120);
    const target = await page.evaluate(() => (document.activeElement as HTMLAnchorElement).getAttribute("href"));
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(new RegExp(`${target}$`));
    await expect(page.locator(target!)).toBeInViewport();
  });
}

for (const path of ["/en-lv/student-permit", "/lv/student-permit", "/en-lv/student-documents", "/en-lv/programmes/rtu/computer-science-236"]) {
  test(`фокус виден на первых шагах Tab: ${path}`, async ({ page }) => {
    await page.goto(path);
    for (let step = 0; step < 8; step += 1) {
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
