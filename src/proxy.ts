import { NextResponse, type NextRequest } from "next/server";
import { legacyLocales, localeForBrowser, locales, type Locale } from "@/i18n/config";

// Посетитель без сегмента в адресе попадает на версию на своём языке:
// латышский — в Латвию, литовский — в Литву, остальные — см. localeForBrowser.
function preferredLocale(request: NextRequest): Locale {
  const acceptLanguage = request.headers.get("accept-language") ?? "";
  return localeForBrowser(acceptLanguage.split(",")[0]?.split("-")[0] ?? "");
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const hasLocale = locales.some(
    (locale) => pathname === `/${locale}` || pathname.startsWith(`/${locale}/`),
  );
  if (hasLocale) return;

  const url = request.nextUrl.clone();

  // Старый адрес английской версии: /en/… -> /en-lv/… (постоянная
  // переадресация, чтобы закладки и разосланные ссылки не ломались).
  const first = pathname.split("/")[1] ?? "";
  const renamed = legacyLocales[first];
  if (renamed) {
    url.pathname = `/${renamed}${pathname.slice(first.length + 1)}`;
    return NextResponse.redirect(url, 308);
  }

  url.pathname = `/${preferredLocale(request)}${pathname}`;
  return NextResponse.redirect(url);
}

export const config = {
  // всё, кроме статики Next.js, API-роутов и файлов с расширением (иконки, изображения)
  matcher: ["/((?!_next|api|.*\\..*).*)"],
};
