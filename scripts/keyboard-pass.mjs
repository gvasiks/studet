// Клавиатурный проход по страницам: Tab от начала до конца, на каждой
// остановке — есть ли видимый признак фокуса. Часть предрелизной проверки
// (CLAUDE.md, «Доступность»): автоаудит axe клавиатуру не проверяет.
//
// Запуск при работающем сайте (npm run dev или npm run start):
//   node scripts/keyboard-pass.mjs /lt/survey /lt/match
//   node scripts/keyboard-pass.mjs            # набор литовских страниц
//
// Скрипт ничего не утверждает за человека: он печатает, сколько остановок
// на странице, все ли интерактивные элементы достижимы и у каких остановок
// признак фокуса не найден. Код возврата 1 — есть что посмотреть глазами.
import { chromium } from "@playwright/test";

const BASE = process.env.BASE_URL ?? "http://localhost:3000";
const DEFAULT_PAGES = [
  "/lt",
  "/lt/programmes",
  "/lt/programmes/vu/medicina",
  "/lt/programmes/vu/medicina/calculator",
  "/lt/survey",
  "/lt/match",
  "/lt/favorites",
  "/lt/glossary",
  "/lt/rights",
  "/lt/privacy",
  "/en-lt/programmes",
  "/lv-lt/programmes",
];
const MAX_STOPS = 400;

// Выполняется в странице: что сейчас в фокусе и виден ли фокус.
function describeFocus() {
  const element = document.activeElement;
  if (!element || element === document.body) return null;
  // Служебная панель Next.js в режиме разработки — не часть сайта.
  if (element.tagName.toLowerCase() === "nextjs-portal") return { skip: true };
  const drawn = (style) => (style.outlineStyle !== "none" && parseFloat(style.outlineWidth) > 0) || style.boxShadow !== "none";
  // Рамка бывает и на псевдоэлементе: у карточки программы ссылка растянута
  // на всю карточку через ::after, и рамка фокуса нарисована на нём.
  const visible = (node) =>
    Boolean(node) && (drawn(getComputedStyle(node)) || drawn(getComputedStyle(node, "::after")) || drawn(getComputedStyle(node, "::before")));
  // Признак фокуса бывает не на самом элементе: у скрытых чекбоксов и радио
  // он рисуется на подписи, соседнем элементе или обёртке компонента.
  const candidates = [
    element,
    element.closest("label"),
    element.nextElementSibling,
    element.parentElement,
    element.closest("[data-focus-visible='true']"),
    ...(element.closest("label")?.querySelectorAll("*") ?? []),
  ];
  const text = (element.getAttribute("aria-label") || element.textContent || element.getAttribute("name") || "").trim().replace(/\s+/g, " ");
  // Номер остановки ставится на сам элемент: одинаковых по разметке ссылок на
  // странице много (меню в шапке и в подвале), а узнать надо именно этот.
  window.__keyboardStops = (window.__keyboardStops ?? 0) + (element.dataset.keyboardStop ? 0 : 1);
  const repeated = Boolean(element.dataset.keyboardStop);
  element.dataset.keyboardStop ??= String(window.__keyboardStops);
  return {
    tag: element.tagName.toLowerCase() + (element.getAttribute("type") ? `[${element.getAttribute("type")}]` : ""),
    text: text.slice(0, 50),
    visible: candidates.some(visible),
    repeated,
  };
}

// Выполняется в странице: сколько элементов должно получать фокус по Tab.
function countTabbable() {
  const selector = "a[href], button, input, select, textarea, summary, [tabindex]";
  return [...document.querySelectorAll(selector)].filter((node) => {
    if (node.disabled || node.tabIndex < 0) return false;
    if (node.type === "hidden") return false;
    // содержимое закрытого <details> (меню сортировки) Tab обходит, пока меню не открыто
    const details = node.closest("details:not([open])");
    if (details && !node.closest("summary")) return false;
    // радио одной группы — одна остановка
    if (node.type === "radio" && !node.checked && document.querySelector(`input[type=radio][name="${node.name}"]:checked`)) return false;
    const rect = node.getBoundingClientRect();
    const style = getComputedStyle(node);
    return style.visibility !== "hidden" && style.display !== "none" && (rect.width > 0 || rect.height > 0 || node.matches("input"));
  }).length;
}

const pages = process.argv.slice(2).length > 0 ? process.argv.slice(2) : DEFAULT_PAGES;
const browser = await chromium.launch();
let problems = 0;
for (const path of pages) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.goto(BASE + path, { waitUntil: "networkidle" });
  const expected = await page.evaluate(countTabbable);
  const stops = [];
  for (let index = 0; index < MAX_STOPS; index += 1) {
    await page.keyboard.press("Tab");
    const stop = await page.evaluate(describeFocus);
    if (!stop) break; // фокус ушёл со страницы — проход закончен
    if (stop.skip) continue;
    if (stop.repeated) break; // вернулись к началу
    stops.push(stop);
  }
  const hidden = stops.filter((stop) => !stop.visible);
  // Остановок меньше, чем интерактивных элементов, — до чего-то Tab не дошёл.
  const flag = hidden.length > 0 || stops.length === MAX_STOPS || stops.length < expected ? "ПОСМОТРЕТЬ" : "ok";
  if (flag !== "ok") problems += 1;
  console.log(`${flag}  ${path}: остановок ${stops.length}, интерактивных элементов ${expected}, без признака фокуса ${hidden.length}`);
  for (const stop of hidden.slice(0, 8)) console.log(`      нет признака фокуса: <${stop.tag}> «${stop.text}»`);
  if (stops.length > 0) console.log(`      первая: <${stops[0].tag}> «${stops[0].text}» · последняя: <${stops.at(-1).tag}> «${stops.at(-1).text}»`);
  await page.close();
}

// --- действия с клавиатуры -------------------------------------------------
// Проход по Tab показывает, что до элемента можно дойти; здесь — что им можно
// воспользоваться без мыши. Только литовские экраны (при запуске без
// аргументов): анкета, меню сортировки, «куда я прохожу», расчёт балла.

// Нажимать Tab, пока в фокусе не окажется элемент, подходящий под условие.
async function tabTo(page, description, predicate, limit = 120) {
  for (let index = 0; index < limit; index += 1) {
    await page.keyboard.press("Tab");
    if (await page.evaluate(predicate)) return;
  }
  throw new Error(`Tab не дошёл до: ${description}`);
}

const actions = [
  {
    name: "анкета: отметить интерес пробелом, пройти шаги клавишей Enter",
    run: async (page) => {
      await page.goto(BASE + "/lt/survey", { waitUntil: "networkidle" });
      await tabTo(page, "плитка интереса", () => document.activeElement?.matches("input[type=checkbox][value=it]"));
      await page.keyboard.press("Space");
      for (let step = 0; step < 5; step += 1) {
        await tabTo(page, "кнопка «дальше»", () => {
          const buttons = [...document.querySelectorAll("main button")];
          return document.activeElement === buttons.at(-1);
        });
        await page.keyboard.press("Enter");
        await page.waitForTimeout(300);
      }
      await page.waitForURL(/\/lt\/programmes\?interest=it/, { timeout: 15000 });
    },
  },
  {
    name: "каталог: открыть меню сортировки и выбрать пункт",
    run: async (page) => {
      await page.goto(BASE + "/lt/programmes", { waitUntil: "networkidle" });
      await tabTo(page, "кнопка сортировки", () => document.activeElement?.matches("details summary"));
      await page.keyboard.press("Enter");
      await tabTo(page, "пункт сортировки", () => document.activeElement?.matches("details a[href*='sort=name_desc']"));
      await page.keyboard.press("Enter");
      await page.waitForURL(/sort=name_desc/, { timeout: 15000 });
    },
  },
  {
    name: "«куда я прохожу»: ввести оценки, раскрыть разбор балла",
    run: async (page) => {
      await page.goto(BASE + "/lt/match", { waitUntil: "networkidle" });
      for (const value of ["80", "70", "60"]) {
        await tabTo(page, "поле оценки", () => {
          const element = document.activeElement;
          return Boolean(element?.matches("input[inputmode=decimal]")) && element.value === "";
        });
        await page.keyboard.type(value);
      }
      await tabTo(page, "разбор балла", () => document.activeElement?.matches("main details summary"));
      await page.keyboard.press("Enter");
      const open = await page.evaluate(() => document.activeElement?.closest("details")?.open === true);
      if (!open) throw new Error("разбор балла не раскрылся по Enter");
    },
  },
  {
    name: "расчёт балла: ввести оценки и получить итог",
    run: async (page) => {
      await page.goto(BASE + "/lt/programmes/vu/medicina/calculator", { waitUntil: "networkidle" });
      const before = await page.evaluate(() => document.querySelector("main").innerText);
      for (const value of ["90", "80", "60"]) {
        await tabTo(page, "поле оценки", () => {
          const element = document.activeElement;
          return Boolean(element?.matches("input[inputmode=decimal]")) && element.value === "";
        });
        await page.keyboard.type(value);
      }
      await page.waitForTimeout(300);
      const after = await page.evaluate(() => document.querySelector("main").innerText);
      if (after === before || !/\d,\d\d/.test(after)) throw new Error("после ввода оценок балл на странице не появился");
    },
  },
];

if (process.argv.slice(2).length === 0) {
  for (const action of actions) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    try {
      await action.run(page);
      console.log(`ok  ${action.name}`);
    } catch (error) {
      problems += 1;
      console.log(`ПОСМОТРЕТЬ  ${action.name}: ${error.message}`);
    }
    await page.close();
  }
}

await browser.close();
process.exit(problems > 0 ? 1 : 0);
