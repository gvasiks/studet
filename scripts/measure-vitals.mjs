// Лабораторный замер скорости страниц на рабочей сборке: LCP, CLS, время
// до первого байта и суммарное время долгих задач. Часть предрелизной
// проверки (CLAUDE.md, «Работоспособность»: LCP < 2,5 с, CLS < 0,1).
//
// Это замер на СВОЁМ компьютере с искусственным замедлением (телефон
// среднего класса: процессор в 4 раза медленнее, сеть «быстрый 4G»), а не
// на настоящих посетителях. Он ловит грубые регрессии до выпуска; норматив
// проверяется по реальным посетителям (PostHog) после запуска. INP здесь не
// меряется: ему нужны настоящие действия пользователя.
//
// Запуск при работающей рабочей сборке (npm run build && npm run start):
//   BASE_URL=http://localhost:3000 node scripts/measure-vitals.mjs /lt /lt/programmes
//   node scripts/measure-vitals.mjs            # набор литовских страниц
import { chromium } from "@playwright/test";

const BASE = process.env.BASE_URL ?? "http://localhost:3000";
const RUNS = 3;
const DEFAULT_PAGES = [
  "/lt",
  "/lt/programmes",
  "/lt/programmes/vu/medicina",
  "/lt/programmes/vu/medicina/calculator",
  "/lt/survey",
  "/lt/match",
  "/lt/glossary",
  "/lt/rights",
  "/en-lt/programmes/vu/medicina",
  "/lv-lt/programmes",
];
const LIMITS = { lcp: 2500, cls: 0.1 };

const median = (values) => [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];

async function measure(browser, path) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  const client = await context.newCDPSession(page);
  await client.send("Emulation.setCPUThrottlingRate", { rate: 4 });
  // «быстрый 4G»: 1,6 Мбит/с вниз, 750 кбит/с вверх, задержка 150 мс
  await client.send("Network.emulateNetworkConditions", { offline: false, latency: 150, downloadThroughput: (1.6 * 1024 * 1024) / 8, uploadThroughput: (750 * 1024) / 8 });
  await page.addInitScript(() => {
    window.__vitals = { lcp: 0, cls: 0, longTasks: 0 };
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) window.__vitals.lcp = entry.startTime;
    }).observe({ type: "largest-contentful-paint", buffered: true });
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) if (!entry.hadRecentInput) window.__vitals.cls += entry.value;
    }).observe({ type: "layout-shift", buffered: true });
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) window.__vitals.longTasks += Math.max(0, entry.duration - 50);
    }).observe({ type: "longtask", buffered: true });
  });
  await page.goto(BASE + path, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  const result = await page.evaluate(() => {
    const navigation = performance.getEntriesByType("navigation")[0];
    const scripts = performance.getEntriesByType("resource").filter((entry) => entry.initiatorType === "script");
    return {
      ...window.__vitals,
      ttfb: navigation.responseStart,
      scriptKb: scripts.reduce((sum, entry) => sum + entry.transferSize, 0) / 1024,
    };
  });
  await context.close();
  return result;
}

const pages = process.argv.slice(2).length > 0 ? process.argv.slice(2) : DEFAULT_PAGES;
const browser = await chromium.launch();
let failed = 0;
console.log("страница | LCP, мс | CLS | до первого байта, мс | долгие задачи, мс | скрипты, КБ");
for (const path of pages) {
  const runs = [];
  for (let index = 0; index < RUNS; index += 1) runs.push(await measure(browser, path));
  const lcp = median(runs.map((run) => run.lcp));
  const cls = median(runs.map((run) => run.cls));
  const ok = lcp < LIMITS.lcp && cls < LIMITS.cls;
  if (!ok) failed += 1;
  console.log(
    `${ok ? "ok" : "ВЫШЕ НОРМЫ"}  ${path} | ${Math.round(lcp)} | ${cls.toFixed(3)} | ${Math.round(median(runs.map((run) => run.ttfb)))} | ${Math.round(median(runs.map((run) => run.longTasks)))} | ${Math.round(median(runs.map((run) => run.scriptKb)))}`,
  );
}
await browser.close();
process.exit(failed > 0 ? 1 : 0);
