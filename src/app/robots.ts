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
        // /verification здесь намеренно НЕТ (решение владельца 2026-10-10):
        // строка в robots.txt сама сообщала адрес внутренней страницы всем,
        // кто его читает. От индексации её закрывает noindex в метаданных
        // страницы — а чтобы поисковик его увидел, обход запрещать нельзя.
        disallow: ["/*/favorites"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
