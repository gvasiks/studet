// Ревью 2026-09, пункт 09: бюджет веса статики в CI, чтобы 2,8 МБ
// hero-bg.png не повторился незаметно через полгода с другой картинкой
// того же размера. Один файл — 300 КБ ("целиться в сотни килобайт" —
// ревью); не общий бюджет на всю папку, чтобы новый тяжёлый файл не
// прятался в сумме за уже лёгкими.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const BUDGET_BYTES = 300 * 1024;
const PUBLIC_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "public");

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(fullPath) : [fullPath];
  });
}

const oversized = walk(PUBLIC_DIR)
  .map((filePath) => ({ filePath, size: fs.statSync(filePath).size }))
  .filter(({ size }) => size > BUDGET_BYTES);

if (oversized.length > 0) {
  for (const { filePath, size } of oversized) {
    console.error(`${path.relative(PUBLIC_DIR, filePath)}: ${(size / 1024).toFixed(0)} КБ > ${BUDGET_BYTES / 1024} КБ`);
  }
  console.error("\nСовременный формат (WebP/AVIF) и/или сжатие через sharp обычно решают это без потери качества.");
  process.exit(1);
}

console.log(`Бюджет статики соблюдён (< ${BUDGET_BYTES / 1024} КБ на файл).`);
