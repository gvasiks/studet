"""Вежливый обход источников (ревизия 2026-09-20, пункт 04).

Скрейперы бьют по сайтам вузов без ограничений; самая вероятная
неприятность — не юридическая, а техническая: блокировка по адресу в
неподходящий момент. Решение собирать данные без отдельной проверки
условий использования принято владельцем (CLAUDE.md), этот модуль лишь
снижает уже принятый риск.

Подключается ОДИН раз в main.py — `polite.install()`. Все 24 сборщика
создают страницы через `browser.new_page()` и ходят через `page.goto()`,
поэтому подмена двух методов Playwright заменяет правку каждого
сборщика. Что делает:

- честный User-Agent: "StudetBot/1.0 (+контакт)" — администратор,
  которому что-то не нравится, напишет письмо, а не заблокирует адрес.
  Контакт берётся из переменной SCRAPER_CONTACT (URL или почта);
  без неё User-Agent остаётся без контакта, и об этом предупреждают;
- пауза между страницами ОДНОГО домена: не меньше SCRAPE_DELAY_SECONDS
  (по умолчанию 1,5) и не меньше Crawl-delay из robots.txt — у niid.lv
  это 10 секунд. Сборщики идут по очереди, так что параллельных
  запросов к одному домену и так нет;
- robots.txt: запрещённые для нас адреса не открываются, а попадают в
  отчёт (SCRAPE_OBEY_ROBOTS=0 отключает, для отладки);
- картинки, шрифты и видео не загружаются — тексту они не нужны, а
  сайту это десятки лишних запросов на страницу;
- локальный кэш для отладки (SCRAPE_CACHE=1): страницы и XHR сутки
  лежат в pipeline/.cache/, повторный запуск сборщика идёт без сети.
  В CI кэш выключен — данные должны быть свежими.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Browser, Page, Route

PRODUCT_TOKEN = "StudetBot"
DEFAULT_DELAY_SECONDS = 1.5
CACHE_TTL_SECONDS = 24 * 3600
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
SKIPPED_RESOURCE_TYPES = {"image", "media", "font"}
CACHED_RESOURCE_TYPES = {"document", "xhr", "fetch"}


class RobotsDisallowed(Exception):
    """robots.txt запрещает этот адрес для нашего User-Agent."""


_installed = False
_last_finished: dict[str, float] = {}
_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
_stats = {"pages": 0, "waited": 0.0, "assets_skipped": 0, "cache_hits": 0, "blocked": []}


def user_agent() -> str:
    contact = os.environ.get("SCRAPER_CONTACT", "").strip()
    return f"Mozilla/5.0 (compatible; {PRODUCT_TOKEN}/1.0" + (f"; +{contact}" if contact else "") + ")"


def _delay() -> float:
    try:
        return float(os.environ.get("SCRAPE_DELAY_SECONDS", DEFAULT_DELAY_SECONDS))
    except ValueError:
        return DEFAULT_DELAY_SECONDS


def _obey_robots() -> bool:
    return os.environ.get("SCRAPE_OBEY_ROBOTS", "1") != "0"


def _cache_enabled() -> bool:
    return os.environ.get("SCRAPE_CACHE", "") == "1"


def _robots_for(url: str) -> urllib.robotparser.RobotFileParser | None:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin in _robots:
        return _robots[origin]

    parser: urllib.robotparser.RobotFileParser | None = urllib.robotparser.RobotFileParser()
    try:
        request = urllib.request.Request(f"{origin}/robots.txt", headers={"User-Agent": user_agent()})
        body = urllib.request.urlopen(request, timeout=15).read().decode("utf-8", "replace")
        parser.parse(body.splitlines())  # type: ignore[union-attr]
    except urllib.error.HTTPError:
        # по RFC 9309 недоступный (4xx) robots.txt — "ограничений нет"
        parser = None
    except Exception:  # noqa: BLE001 — сеть моргнула: не блокируем весь источник из-за robots.txt
        parser = None
    _robots[origin] = parser
    return parser


def _cache_paths(url: str) -> tuple[Path, Path]:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{key}.json", CACHE_DIR / f"{key}.bin"


def _cached(url: str) -> bool:
    if not _cache_enabled():
        return False
    meta, body = _cache_paths(url)
    return meta.exists() and body.exists() and time.time() - meta.stat().st_mtime < CACHE_TTL_SECONDS


def _wait_turn(url: str) -> None:
    """Проверка robots.txt и пауза перед переходом на страницу."""
    if _cached(url):
        return  # ответ из кэша сети не касается

    host = urlparse(url).netloc
    parser = _robots_for(url)
    if parser is not None and _obey_robots() and not parser.can_fetch(PRODUCT_TOKEN, url):
        _stats["blocked"].append(url)
        raise RobotsDisallowed(url)

    crawl_delay = (parser.crawl_delay(PRODUCT_TOKEN) or 0) if parser is not None else 0
    wait = _last_finished.get(host, 0.0) + max(_delay(), float(crawl_delay)) - time.monotonic()
    if wait > 0:
        time.sleep(wait)
        _stats["waited"] += wait


def _route_handler(route: Route) -> None:
    request = route.request
    if request.resource_type in SKIPPED_RESOURCE_TYPES:
        _stats["assets_skipped"] += 1
        route.abort()
        return

    if _cache_enabled() and request.method == "GET" and request.resource_type in CACHED_RESOURCE_TYPES:
        meta_path, body_path = _cache_paths(request.url)
        if _cached(request.url):
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            _stats["cache_hits"] += 1
            route.fulfill(status=meta["status"], headers=meta["headers"], body=body_path.read_bytes())
            return
        response = route.fetch()
        CACHE_DIR.mkdir(exist_ok=True)
        body_path.write_bytes(response.body())
        content_type = response.headers.get("content-type", "text/html; charset=utf-8")
        meta_path.write_text(
            json.dumps({"status": response.status, "headers": {"content-type": content_type}}),
            encoding="utf-8",
        )
        route.fulfill(response=response)
        return

    route.continue_()


def install() -> None:
    """Подмена Browser.new_page и Page.goto. Вызывать один раз, после load_dotenv()."""
    global _installed
    if _installed:
        return
    _installed = True

    if not os.environ.get("SCRAPER_CONTACT", "").strip():
        print(
            "polite: SCRAPER_CONTACT не задан — User-Agent уйдёт без контакта. Задайте URL или "
            "почту в pipeline/.env (и переменную SCRAPER_CONTACT в GitHub)."
        )

    original_new_page = Browser.new_page
    original_goto = Page.goto

    def new_page(self: Browser, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("user_agent", user_agent())
        page = original_new_page(self, **kwargs)
        page.route("**/*", _route_handler)
        return page

    def goto(self: Page, url: str, **kwargs):  # type: ignore[no-untyped-def]
        _wait_turn(url)
        try:
            return original_goto(self, url, **kwargs)
        finally:
            _stats["pages"] += 1
            _last_finished[urlparse(url).netloc] = time.monotonic()

    Browser.new_page = new_page  # type: ignore[method-assign]
    Page.goto = goto  # type: ignore[method-assign]


def report_and_reset() -> str:
    """Одна строка для журнала после каждого источника."""
    blocked = _stats["blocked"]
    line = (
        f"polite: страниц {_stats['pages']}, ждали {_stats['waited']:.0f} с, "
        f"картинок/шрифтов пропущено {_stats['assets_skipped']}, из кэша {_stats['cache_hits']}, "
        f"закрыто robots.txt {len(blocked)}"
    )
    if blocked:
        line += " (" + ", ".join(blocked[:3]) + (" …" if len(blocked) > 3 else "") + ")"
    _stats.update(pages=0, waited=0.0, assets_skipped=0, cache_hits=0, blocked=[])
    return line
