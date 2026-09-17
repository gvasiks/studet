import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        // /favorites — своя страница у каждого посетителя (localStorage),
        // индексировать нечего; уже noindex на уровне метаданных, disallow
        // здесь дополнительно экономит краулинговый бюджет.
        disallow: ["/*/favorites"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
