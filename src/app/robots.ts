import type { MetadataRoute } from "next";
import { isSiteClosed, SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  // Закрытая выкладка до запуска: обход запрещён целиком, карты сайта нет.
  if (isSiteClosed()) return { rules: [{ userAgent: "*", disallow: "/" }] };

  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        // /favorites — своя страница у каждого посетителя (localStorage),
        // индексировать нечего; уже noindex на уровне метаданных, disallow
        // здесь дополнительно экономит краулинговый бюджет.
        // /verification — внутренний рабочий инструмент (пункт 03), не
        // часть продукта ни для одной аудитории.
        disallow: ["/*/favorites", "/*/verification"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
